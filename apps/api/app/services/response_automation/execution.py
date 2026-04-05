from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.enums import (
    IncidentStatus,
    ResponseActionType,
    ResponsePolicyTarget,
    ResponseStatus,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.response_policy import ResponsePolicy
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.repositories.policies import PoliciesRepository
from app.repositories.responses import ResponsesRepository
from app.services.response_automation.adapters import AdapterContext, execute_adapter
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.features import (
    extract_destination_ip,
    extract_destination_port,
    extract_source_ip,
    extract_username,
)
from app.services.scoring.rollup import incident_rollup_score, refresh_incident_priority


def _create_audit_log(
    session: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    details: dict,
) -> None:
    AuditLogsRepository(session).create(
        AuditLog(
            actor=None,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details,
        )
    )


def _ensure_incident_for_alert(
    session: Session,
    alert: NormalizedAlert,
) -> Incident:
    if alert.incident is not None:
        return alert.incident

    incident = IncidentsRepository(session).create(
        Incident(
            title=f"Automated response context: {alert.title}",
            summary=(
                "Incident created automatically so policy-driven response actions "
                "can be tracked in the SME SOC workflow."
            ),
            status=IncidentStatus.TRIAGED,
            priority=priority_from_score(alert.risk_score.score if alert.risk_score else alert.severity * 10),
            created_at=alert.created_at,
            updated_at=datetime.now(UTC),
        )
    )
    session.flush()
    alert.incident_id = incident.id
    session.flush()
    if incident.primary_alert_id is None:
        incident.primary_alert_id = alert.id
        session.flush()
    session.refresh(alert)
    session.refresh(incident)
    refresh_incident_priority(incident)

    _create_audit_log(
        session,
        entity_type="incident",
        entity_id=str(incident.id),
        action="incident.created.automated_response",
        details={
            "alert_id": str(alert.id),
            "summary": "Incident created automatically for policy-driven response execution.",
            "priority": incident.priority.value,
            "state": incident.status.value,
        },
    )
    _create_audit_log(
        session,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.linked_incident.automated_response",
        details={
            "incident_id": str(incident.id),
            "summary": "Alert was linked to an auto-created incident for policy execution.",
        },
    )
    return incident


def _resolve_target_value(
    policy: ResponsePolicy,
    *,
    alert: NormalizedAlert | None,
    incident: Incident,
) -> str | None:
    primary_alert = alert or incident.primary_alert
    if policy.action_type == ResponseActionType.BLOCK_IP:
        if primary_alert is None:
            return None
        return extract_source_ip(primary_alert)
    if policy.action_type == ResponseActionType.DISABLE_USER:
        if primary_alert is None:
            return None
        return extract_username(primary_alert)
    if policy.action_type == ResponseActionType.QUARANTINE_HOST_FLAG:
        if primary_alert and primary_alert.asset is not None:
            return primary_alert.asset.hostname
        return None
    if policy.action_type == ResponseActionType.CREATE_MANUAL_REVIEW:
        return incident.title
    if policy.action_type == ResponseActionType.NOTIFY_ADMIN:
        return "AegisCore administrators"
    return None


def _build_execution_payload(
    policy: ResponsePolicy,
    *,
    alert: NormalizedAlert | None,
    incident: Incident,
    target_value: str | None,
    reason: str,
) -> dict:
    primary_alert = alert or incident.primary_alert
    return {
        "policy": {
            "id": str(policy.id),
            "name": policy.name,
            "target": policy.target.value,
            "detection_type": policy.detection_type.value,
            "min_risk_score": policy.min_risk_score,
            "action_type": policy.action_type.value,
            "mode": policy.mode.value,
        },
        "incident": {
            "id": str(incident.id),
            "title": incident.title,
            "priority": incident.priority.value,
            "status": incident.status.value,
        },
        "alert": {
            "id": str(primary_alert.id) if primary_alert else None,
            "detection_type": primary_alert.detection_type.value if primary_alert else None,
            "risk_score": round(primary_alert.risk_score.score) if primary_alert and primary_alert.risk_score else None,
            "source_ip": extract_source_ip(primary_alert) if primary_alert else None,
            "destination_ip": extract_destination_ip(primary_alert) if primary_alert else None,
            "destination_port": extract_destination_port(primary_alert) if primary_alert else None,
            "username": extract_username(primary_alert) if primary_alert else None,
        },
        "target_value": target_value,
        "evaluation_reason": reason,
        "config": policy.config,
    }


def _upsert_response_action(
    session: Session,
    *,
    policy: ResponsePolicy,
    incident: Incident,
    alert: NormalizedAlert | None,
    target_value: str | None,
    reason: str,
) -> ResponseAction:
    responses_repository = ResponsesRepository(session)
    existing = responses_repository.find_existing_policy_action(
        policy_id=policy.id,
        incident_id=incident.id,
        normalized_alert_id=alert.id if alert else None,
    )
    if existing is not None:
        return existing

    response_action = responses_repository.create(
        ResponseAction(
            incident=incident,
            normalized_alert=alert,
            policy=policy,
            action_type=policy.action_type.value,
            status=ResponseStatus.QUEUED,
            mode=policy.mode,
            target_value=target_value,
            attempt_count=0,
            details={
                "policy_snapshot": {
                    "id": str(policy.id),
                    "name": policy.name,
                    "target": policy.target.value,
                    "detection_type": policy.detection_type.value,
                    "min_risk_score": policy.min_risk_score,
                    "action_type": policy.action_type.value,
                    "mode": policy.mode.value,
                },
                "evaluation_reason": reason,
            },
        )
    )
    session.flush()
    _create_audit_log(
        session,
        entity_type="response",
        entity_id=str(response_action.id),
        action="response.policy_matched",
        details={
            "policy_id": str(policy.id),
            "policy_name": policy.name,
            "incident_id": str(incident.id),
            "alert_id": str(alert.id) if alert else None,
            "summary": "Automated response policy matched and queued execution.",
        },
    )
    return response_action


def _execute_response_action(
    session: Session,
    *,
    response_action: ResponseAction,
    payload: dict,
) -> ResponseAction:
    settings = get_settings()

    if response_action.status in {
        ResponseStatus.COMPLETED,
        ResponseStatus.WARNING,
        ResponseStatus.IN_PROGRESS,
    }:
        return response_action

    max_attempts = max(1, settings.automated_response_max_retries)
    response_action.status = ResponseStatus.IN_PROGRESS

    final_result = None
    for _ in range(max_attempts):
        response_action.attempt_count += 1
        response_action.last_attempted_at = datetime.now(UTC)
        _create_audit_log(
            session,
            entity_type="response",
            entity_id=str(response_action.id),
            action="response.execution_attempted",
            details={
                "attempt_count": response_action.attempt_count,
                "action_type": response_action.action_type,
                "mode": response_action.mode.value,
                "summary": "Automated response execution attempt started.",
            },
        )

        final_result = execute_adapter(
            AdapterContext(
                action_type=ResponseActionType(response_action.action_type),
                mode=response_action.mode,
                target_value=response_action.target_value,
                policy_name=response_action.policy.name if response_action.policy else "Unnamed policy",
                payload=payload,
            ),
            settings=settings,
        )
        if final_result.status != ResponseStatus.FAILED:
            break

    assert final_result is not None
    response_action.status = final_result.status
    response_action.result_summary = final_result.summary
    response_action.result_message = final_result.message
    response_action.executed_at = datetime.now(UTC)
    response_action.details = {
        **response_action.details,
        **final_result.details,
        "result_status": final_result.status.value,
        "result_summary": final_result.summary,
        "result_message": final_result.message,
    }

    _create_audit_log(
        session,
        entity_type="response",
        entity_id=str(response_action.id),
        action=f"response.execution_{response_action.status.value}",
        details={
            "attempt_count": response_action.attempt_count,
            "action_type": response_action.action_type,
            "status": response_action.status.value,
            "summary": final_result.summary,
            "message": final_result.message,
        },
    )
    return response_action


def _evaluate_policy(
    session: Session,
    *,
    policy: ResponsePolicy,
    incident: Incident,
    alert: NormalizedAlert | None,
    risk_score: float,
    reason: str,
) -> ResponseAction:
    target_value = _resolve_target_value(policy, alert=alert, incident=incident)
    response_action = _upsert_response_action(
        session,
        policy=policy,
        incident=incident,
        alert=alert,
        target_value=target_value,
        reason=reason,
    )
    payload = _build_execution_payload(
        policy,
        alert=alert,
        incident=incident,
        target_value=target_value,
        reason=reason,
    )
    return _execute_response_action(
        session,
        response_action=response_action,
        payload=payload,
    )


def evaluate_alert_policies(
    session: Session,
    alert: NormalizedAlert,
) -> list[ResponseAction]:
    if alert.risk_score is None:
        return []

    policies = PoliciesRepository(session).find_matching_policies(
        target=ResponsePolicyTarget.ALERT,
        detection_type=alert.detection_type,
        risk_score=alert.risk_score.score,
    )
    if not policies:
        return []

    incident = _ensure_incident_for_alert(session, alert)
    responses: list[ResponseAction] = []
    for policy in policies:
        reason = (
            f"Alert matched policy {policy.name} because {alert.detection_type.value} "
            f"scored {round(alert.risk_score.score)} and met the threshold of "
            f"{policy.min_risk_score}."
        )
        responses.append(
            _evaluate_policy(
                session,
                policy=policy,
                incident=incident,
                alert=alert,
                risk_score=alert.risk_score.score,
                reason=reason,
            )
        )
    refresh_incident_priority(incident)
    return responses


def evaluate_incident_policies_for_alert(
    session: Session,
    alert: NormalizedAlert,
) -> list[ResponseAction]:
    if alert.risk_score is None:
        return []

    matching_policies = PoliciesRepository(session).find_matching_policies(
        target=ResponsePolicyTarget.INCIDENT,
        detection_type=alert.detection_type,
        risk_score=alert.risk_score.score,
    )
    if not matching_policies:
        return []

    incident = _ensure_incident_for_alert(session, alert)
    return evaluate_incident_policies(session, incident)


def evaluate_incident_policies(
    session: Session,
    incident: Incident,
) -> list[ResponseAction]:
    primary_alert = incident.primary_alert
    if primary_alert is None:
        return []

    rollup_score = incident_rollup_score(incident)
    policies = PoliciesRepository(session).find_matching_policies(
        target=ResponsePolicyTarget.INCIDENT,
        detection_type=primary_alert.detection_type,
        risk_score=rollup_score,
    )
    responses: list[ResponseAction] = []
    for policy in policies:
        reason = (
            f"Incident matched policy {policy.name} because the linked-alert rollup "
            f"score reached {round(rollup_score)} for {primary_alert.detection_type.value}."
        )
        responses.append(
            _evaluate_policy(
                session,
                policy=policy,
                incident=incident,
                alert=None,
                risk_score=rollup_score,
                reason=reason,
            )
        )
    refresh_incident_priority(incident)
    return responses
