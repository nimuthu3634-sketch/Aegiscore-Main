# Policy evaluation and execution flow for automated response actions.

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.enums import (
    DetectionType,
    IncidentStatus,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
    ResponseStatus,
    ScoreMethod,
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
from app.services.notifications.service import (
    notify_for_high_risk_incident,
    notify_for_response_result,
)
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.features import (
    extract_destination_ip,
    extract_destination_port,
    extract_source_ip,
    extract_username,
)
from app.services.response_automation.ai_direct_brute_force_block import (
    AUTOMATION_RULE_ID as AI_DIRECT_AUTOMATION_RULE_ID,
    evaluate_ai_direct_brute_force_block,
)
from app.services.response_automation.ip_safety import (
    validate_automated_block_ip_target,
)
from app.services.response_automation.ml_brute_force_automation import (
    AUTOMATION_RULE_ID,
    ml_brute_force_auto_block_evaluation,
)
from app.services.scoring.rollup import incident_rollup_score, refresh_incident_priority


# Resolves the display name used by adapters and audit logs.
def _response_adapter_policy_name(response_action: ResponseAction) -> str:
    details = response_action.details or {}
    named = str(details.get("adapter_policy_name") or "").strip()
    if named:
        return named
    if response_action.policy is not None:
        return response_action.policy.name
    return "Unnamed policy"


# Creates system audit records for automation decisions and execution results.
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


# Ensures an alert has an incident so response actions can be tracked properly.
def _ensure_incident_for_alert(
    session: Session,
    alert: NormalizedAlert,
) -> Incident:
    # Reuse the existing incident when the alert is already linked.
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


# Resolves the action target, such as source IP, username, or hostname.
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


# Builds the payload passed into the selected response adapter.
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
            "asset_ip": (
                (primary_alert.normalized_payload or {}).get("asset_ip") if primary_alert else None
            ),
            "destination_port": extract_destination_port(primary_alert) if primary_alert else None,
            "username": extract_username(primary_alert) if primary_alert else None,
        },
        "target_value": target_value,
        "evaluation_reason": reason,
        "config": policy.config,
    }


# Builds adapter payload for the built-in ML brute-force block rule.
def _build_builtin_ml_brute_force_payload(
    *,
    alert: NormalizedAlert,
    incident: Incident,
    target_value: str | None,
    reason: str,
    evaluation_detail: dict,
) -> dict:
    primary_alert = alert
    return {
        "policy": None,
        "built_in_automation": {
            "rule": AUTOMATION_RULE_ID,
            "name": "TensorFlow brute-force IP auto-block",
            "evaluation": evaluation_detail,
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
            "risk_score": round(primary_alert.risk_score.score)
            if primary_alert and primary_alert.risk_score
            else None,
            "source_ip": extract_source_ip(primary_alert) if primary_alert else None,
            "destination_ip": extract_destination_ip(primary_alert) if primary_alert else None,
            "asset_ip": (primary_alert.normalized_payload or {}).get("asset_ip"),
            "destination_port": extract_destination_port(primary_alert) if primary_alert else None,
            "username": extract_username(primary_alert) if primary_alert else None,
        },
        "target_value": target_value,
        "evaluation_reason": reason,
        "config": {},
    }


# Builds adapter payload for the AI-direct brute-force block rule.
def _build_ai_direct_execution_payload(
    *,
    alert: NormalizedAlert,
    incident: Incident,
    target_value: str | None,
    evaluation_detail: dict,
    fixed_reason: str,
) -> dict:
    primary_alert = alert
    return {
        "policy": None,
        "built_in_automation": {
            "rule": AI_DIRECT_AUTOMATION_RULE_ID,
            "name": "AI-direct TensorFlow brute-force IP block",
            "evaluation": evaluation_detail,
            "triggered_by": "ai_model",
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
            "risk_score": round(primary_alert.risk_score.score)
            if primary_alert and primary_alert.risk_score
            else None,
            "source_ip": extract_source_ip(primary_alert) if primary_alert else None,
            "destination_ip": extract_destination_ip(primary_alert) if primary_alert else None,
            "asset_ip": (primary_alert.normalized_payload or {}).get("asset_ip"),
            "destination_port": extract_destination_port(primary_alert) if primary_alert else None,
            "username": extract_username(primary_alert) if primary_alert else None,
        },
        "target_value": target_value,
        "evaluation_reason": fixed_reason,
        "config": {},
    }


# Creates or reuses the response action for AI-direct block automation.
def _upsert_ai_direct_automation_action(
    session: Session,
    *,
    incident: Incident,
    alert: NormalizedAlert,
    target_value: str | None,
    evaluation_detail: dict,
    failed_logins_5m: int,
    model_priority_tier: str,
    fixed_reason: str,
) -> ResponseAction:
    responses_repository = ResponsesRepository(session)
    existing = responses_repository.find_existing_automation_action(
        incident_id=incident.id,
        normalized_alert_id=alert.id,
        automation_rule=AI_DIRECT_AUTOMATION_RULE_ID,
    )
    if existing is not None:
        return existing

    tier_clean = (model_priority_tier or "").strip().lower()
    response_action = responses_repository.create(
        ResponseAction(
            incident=incident,
            normalized_alert=alert,
            policy=None,
            action_type=ResponseActionType.BLOCK_IP.value,
            status=ResponseStatus.QUEUED,
            mode=ResponseMode.LIVE,
            target_value=target_value,
            attempt_count=0,
            details={
                "triggered_by": "ai_model",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "detection_type": DetectionType.BRUTE_FORCE.value,
                "source_ip": target_value,
                "failed_logins_5m": failed_logins_5m,
                "model_priority_tier": tier_clean or None,
                "scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
                "reason": fixed_reason,
                "adapter_policy_name": "AI-direct: TensorFlow brute-force IP block",
                "ai_direct_evaluation": evaluation_detail,
                "evaluation_reason": fixed_reason,
            },
        )
    )
    session.flush()
    _create_audit_log(
        session,
        entity_type="response",
        entity_id=str(response_action.id),
        action="response.ai_direct_automation_matched",
        details={
            "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
            "incident_id": str(incident.id),
            "alert_id": str(alert.id),
            "summary": "AI-direct TensorFlow brute-force block queued from scoring pipeline.",
            "evaluation": evaluation_detail,
        },
    )
    return response_action


# Runs the AI-direct block flow after scoring when all gates pass.
def execute_ai_direct_block_if_required(
    session: Session,
    alert: NormalizedAlert,
) -> list[ResponseAction]:
    """Queue ``block_ip`` immediately after TensorFlow scoring when AI-direct gates pass."""
    settings = get_settings()
    rs = alert.risk_score
    if rs is None:
        return []

    if (
        alert.detection_type != DetectionType.BRUTE_FORCE
        or rs.scoring_method != ScoreMethod.TENSORFLOW_MODEL
    ):
        return []

    # Feature flag keeps AI-direct blocking disabled unless the lab explicitly enables it.
    if not settings.ai_direct_brute_force_block_enabled:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "feature_disabled",
                "summary": "AI_DIRECT_BRUTE_FORCE_BLOCK_ENABLED is false.",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
            },
        )
        return []

    passed, evaluation_detail = evaluate_ai_direct_brute_force_block(alert)
    tier_display = evaluation_detail.get("model_priority_tier") or (
        rs.priority_label.value if rs.priority_label else None
    )
    failed_5m_val = (evaluation_detail.get("checks") or {}).get("failed_logins_5m")

    _create_audit_log(
        session,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.ai_direct_block.evaluation",
        details={
            "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
            "passed": passed,
            "checks": evaluation_detail.get("checks"),
            "thresholds": evaluation_detail.get("thresholds"),
            "summary": evaluation_detail.get("summary"),
            "model_priority_tier": tier_display,
            "failed_logins_5m": failed_5m_val,
        },
    )

    # If any AI-direct gate fails, no response action is created.
    if not passed:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "gates_failed",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "summary": "AI-direct brute-force gates did not pass.",
                "evaluation": evaluation_detail,
            },
        )
        return []

    if not settings.automated_response_builtin_adapters_enabled:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "builtin_adapters_disabled",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "summary": "AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED is false.",
            },
        )
        return []

    incident = alert.incident or _ensure_incident_for_alert(session, alert)
    target_ip = evaluation_detail.get("resolved_source_ip") or extract_source_ip(alert)
    if not target_ip:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "missing_source_ip",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "summary": "Resolved source IP missing after gate evaluation.",
            },
        )
        return []

    responses_repository = ResponsesRepository(session)
    # Prevents duplicate block_ip actions for the same alert and source IP.
    if responses_repository.find_existing_block_ip_for_alert_target(
        normalized_alert_id=alert.id,
        target_ip=target_ip,
    ):
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "duplicate_block_ip",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "target_ip": target_ip,
                "summary": "block_ip already recorded for this alert and IP.",
            },
        )
        return []

    # Final IP safety validation protects infrastructure and configured protected IPs.
    ip_ok, ip_msg = validate_automated_block_ip_target(
        target_ip,
        settings=settings,
        alert=alert,
        execution_payload=None,
    )
    if not ip_ok:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.ai_direct_block.skipped",
            details={
                "reason": "unsafe_or_protected_ip",
                "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
                "target_ip": target_ip,
                "message": ip_msg,
                "summary": "AI-direct block skipped: IP safety validation failed.",
            },
        )
        return []

    fixed_reason = "AI model classified brute-force alert as high/critical risk"
    tier_raw = (rs.explanation or {}).get("model_priority_tier") or tier_display
    tier_clean = str(tier_raw).strip().lower() if tier_raw else ""

    failed_int = int(failed_5m_val) if isinstance(failed_5m_val, int) else int(failed_5m_val or 0)

    response_action = _upsert_ai_direct_automation_action(
        session,
        incident=incident,
        alert=alert,
        target_value=target_ip,
        evaluation_detail=evaluation_detail,
        failed_logins_5m=failed_int,
        model_priority_tier=tier_clean,
        fixed_reason=fixed_reason,
    )
    payload = _build_ai_direct_execution_payload(
        alert=alert,
        incident=incident,
        target_value=target_ip,
        evaluation_detail=evaluation_detail,
        fixed_reason=fixed_reason,
    )
    executed = _execute_response_action(
        session,
        response_action=response_action,
        payload=payload,
    )
    _create_audit_log(
        session,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.ai_direct_block.executed",
        details={
            "automation_rule": AI_DIRECT_AUTOMATION_RULE_ID,
            "response_action_id": str(executed.id),
            "status": executed.status.value,
            "result_summary": executed.result_summary,
            "target_ip": target_ip,
        },
    )
    refresh_incident_priority(incident)
    return [executed]


# Creates a policy response action or reuses the existing one to avoid duplicates.
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


# Creates or reuses the response action for built-in ML brute-force automation.
def _upsert_builtin_automation_action(
    session: Session,
    *,
    incident: Incident,
    alert: NormalizedAlert,
    target_value: str | None,
    reason: str,
    evaluation_detail: dict,
) -> ResponseAction:
    responses_repository = ResponsesRepository(session)
    existing = responses_repository.find_existing_automation_action(
        incident_id=incident.id,
        normalized_alert_id=alert.id,
        automation_rule=AUTOMATION_RULE_ID,
    )
    if existing is not None:
        return existing

    response_action = responses_repository.create(
        ResponseAction(
            incident=incident,
            normalized_alert=alert,
            policy=None,
            action_type=ResponseActionType.BLOCK_IP.value,
            status=ResponseStatus.QUEUED,
            mode=ResponseMode.LIVE,
            target_value=target_value,
            attempt_count=0,
            details={
                "automation_rule": AUTOMATION_RULE_ID,
                "adapter_policy_name": "Built-in: TensorFlow brute-force IP block (v1)",
                "policy_snapshot": None,
                "ml_brute_force_evaluation": evaluation_detail,
                "evaluation_reason": reason,
                "thresholds": evaluation_detail.get("thresholds", {}),
            },
        )
    )
    session.flush()
    _create_audit_log(
        session,
        entity_type="response",
        entity_id=str(response_action.id),
        action="response.builtin_automation_matched",
        details={
            "automation_rule": AUTOMATION_RULE_ID,
            "incident_id": str(incident.id),
            "alert_id": str(alert.id),
            "summary": "Built-in TensorFlow brute-force auto-block matched and queued execution.",
            "evaluation": evaluation_detail,
        },
    )
    return response_action


# Executes a queued response action and saves the final result.
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
                session=session,
                action_type=ResponseActionType(response_action.action_type),
                mode=response_action.mode,
                target_value=response_action.target_value,
                policy_name=_response_adapter_policy_name(response_action),
                payload=payload,
                normalized_alert=response_action.normalized_alert,
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
    notify_for_response_result(
        session,
        incident=response_action.incident,
        response_action=response_action,
    )
    return response_action


# Evaluates one matched policy and executes its configured action.
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


# Evaluates the built-in TensorFlow brute-force auto-block rule.
def _evaluate_builtin_ml_brute_force_auto_block(
    session: Session,
    alert: NormalizedAlert,
) -> list[ResponseAction]:
    settings = get_settings()
    if not settings.automated_response_ml_brute_force_enabled:
        return []
    if not settings.automated_response_builtin_adapters_enabled:
        return []
    if alert.detection_type != DetectionType.BRUTE_FORCE:
        return []
    rs = alert.risk_score
    if rs is None or rs.scoring_method != ScoreMethod.TENSORFLOW_MODEL:
        return []

    responses_repository = ResponsesRepository(session)
    if responses_repository.find_existing_policy_block_ip_for_alert(normalized_alert_id=alert.id):
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.builtin_ml_brute_force.skipped",
            details={
                "automation_rule": AUTOMATION_RULE_ID,
                "reason": "policy_block_ip_already_recorded",
                "summary": (
                    "Skipped built-in TensorFlow brute-force auto-block because a policy-backed "
                    "block_ip response already exists for this alert."
                ),
            },
        )
        return []

    passed, evaluation_detail = ml_brute_force_auto_block_evaluation(alert)
    _create_audit_log(
        session,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.builtin_ml_brute_force.evaluation",
        details={
            "automation_rule": AUTOMATION_RULE_ID,
            "passed": passed,
            "summary": evaluation_detail.get("summary"),
            "checks": evaluation_detail.get("checks"),
            "thresholds": evaluation_detail.get("thresholds"),
        },
    )
    if not passed:
        return []

    incident = alert.incident or _ensure_incident_for_alert(session, alert)
    target_ip = evaluation_detail.get("resolved_source_ip") or extract_source_ip(alert)
    if not target_ip:
        return []

    if responses_repository.find_existing_block_ip_for_alert_target(
        normalized_alert_id=alert.id,
        target_ip=target_ip,
    ):
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.builtin_ml_brute_force.skipped",
            details={
                "automation_rule": AUTOMATION_RULE_ID,
                "reason": "duplicate_block_ip",
                "target_ip": target_ip,
                "summary": "Built-in ML brute-force auto-block skipped: block_ip already exists for this alert and IP.",
            },
        )
        return []

    ip_ok, ip_msg = validate_automated_block_ip_target(
        target_ip,
        settings=settings,
        alert=alert,
        execution_payload=None,
    )
    if not ip_ok:
        _create_audit_log(
            session,
            entity_type="alert",
            entity_id=str(alert.id),
            action="alert.builtin_ml_brute_force.skipped",
            details={
                "automation_rule": AUTOMATION_RULE_ID,
                "reason": "unsafe_or_protected_ip",
                "target_ip": target_ip,
                "message": ip_msg,
                "summary": "Built-in ML brute-force auto-block skipped: IP safety validation failed.",
            },
        )
        return []

    thr = evaluation_detail.get("thresholds", {})
    failed_5m = (evaluation_detail.get("checks") or {}).get("failed_logins_5m")
    reason = (
        "Built-in TensorFlow brute-force auto-block: detection_type is brute_force, "
        f"scoring_method is tensorflow_model, incident priority High and model tier high, "
        f"failed_logins_5m is {failed_5m} (required >= {thr.get('required_failed_logins_5m')}), "
        "and source_ip is present."
    )

    response_action = _upsert_builtin_automation_action(
        session,
        incident=incident,
        alert=alert,
        target_value=target_ip,
        reason=reason,
        evaluation_detail=evaluation_detail,
    )
    payload = _build_builtin_ml_brute_force_payload(
        alert=alert,
        incident=incident,
        target_value=target_ip,
        reason=reason,
        evaluation_detail=evaluation_detail,
    )
    executed = _execute_response_action(
        session,
        response_action=response_action,
        payload=payload,
    )
    refresh_incident_priority(incident)
    return [executed]


# Public entry point for evaluating alert-level response policies.
def evaluate_alert_policies(
    session: Session,
    alert: NormalizedAlert,
) -> list[ResponseAction]:
    if alert.risk_score is None:
        return []

    # Finds enabled policies that match the alert type and risk score.
    policies = PoliciesRepository(session).find_matching_policies(
        target=ResponsePolicyTarget.ALERT,
        detection_type=alert.detection_type,
        risk_score=alert.risk_score.score,
    )
    responses: list[ResponseAction] = []
    policy_blocks_ip = False
    if policies:
        incident = _ensure_incident_for_alert(session, alert)
        policy_blocks_ip = any(p.action_type == ResponseActionType.BLOCK_IP for p in policies)
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
        notify_for_high_risk_incident(
            session,
            incident=incident,
            risk_score=alert.risk_score.score,
        )
        refresh_incident_priority(incident)

    if not policy_blocks_ip:
        responses.extend(_evaluate_builtin_ml_brute_force_auto_block(session, alert))
    return responses


# Checks incident-level policies using an alert as the starting context.
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


# Public entry point for evaluating policies against a full incident.
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
