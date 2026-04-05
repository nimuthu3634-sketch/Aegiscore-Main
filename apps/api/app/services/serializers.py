from typing import Any

from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.schemas.alerts import (
    AlertDetailResponse,
    AlertLinkedIncidentResponse,
    AlertScoreExplanationResponse,
    AlertSeverityLabel,
    AlertSourceRuleResponse,
)
from app.schemas.common import (
    ActivityEntryResponse,
    AlertSummaryResponse,
    AnalystNoteResponse,
    AssetSummaryResponse,
    AuditLogResponse,
    IncidentReferenceResponse,
    IncidentSummaryResponse,
    RawAlertSummaryResponse,
    ResponseActionDetailResponse,
    ResponseActionReferenceResponse,
    ResponseActionSummaryResponse,
    RiskScoreResponse,
    RoleResponse,
    UserBriefResponse,
    UserResponse,
)
from app.schemas.incidents import (
    IncidentDetailResponse,
    IncidentGroupedEvidenceResponse,
    IncidentLinkedAlertResponse,
    IncidentPriorityExplanationResponse,
    IncidentStateTransitionCapabilitiesResponse,
)


def _titleize_source(source: str) -> str:
    labels = {
        "wazuh": "Wazuh",
        "suricata": "Suricata",
    }
    return labels.get(source.lower(), source.title())


def _severity_label_from_score(severity: int) -> AlertSeverityLabel:
    if severity >= 9:
        return AlertSeverityLabel.CRITICAL
    if severity >= 7:
        return AlertSeverityLabel.HIGH
    if severity >= 4:
        return AlertSeverityLabel.MEDIUM
    return AlertSeverityLabel.LOW


def _priority_label_from_risk(
    risk_score: RiskScore | None,
    severity: int,
) -> AlertSeverityLabel | None:
    if risk_score is None:
        return _severity_label_from_score(severity)

    scaled_score = round(risk_score.score * 100)
    if scaled_score >= 85:
        return AlertSeverityLabel.CRITICAL
    if scaled_score >= 70:
        return AlertSeverityLabel.HIGH
    if scaled_score >= 45:
        return AlertSeverityLabel.MEDIUM
    return AlertSeverityLabel.LOW


def _pick_payload_value(
    payloads: list[dict[str, Any] | None],
    *keys: str,
) -> Any | None:
    for payload in payloads:
        if not payload:
            continue
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
    return None


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _extract_source_ip(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "source_ip",
        "src_ip",
        "srcip",
        "scanner_ip",
    )


def _extract_destination_ip(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "destination_ip",
        "dest_ip",
        "dst_ip",
        "dstip",
        "target_ip",
    )


def _extract_destination_port(alert: NormalizedAlert) -> int | None:
    return _coerce_int(
        _pick_payload_value(
            [alert.normalized_payload, alert.raw_alert.raw_payload],
            "destination_port",
            "dest_port",
            "dst_port",
            "destinationPort",
        )
    )


def _extract_username(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "username",
        "new_user",
        "user",
    )


def _extract_source_rule(raw_alert: RawAlert) -> AlertSourceRuleResponse | None:
    raw_payload = raw_alert.raw_payload or {}
    nested_rule = raw_payload.get("rule")
    rule_payload = nested_rule if isinstance(nested_rule, dict) else {}

    rule_id = _pick_payload_value([raw_payload, rule_payload], "rule_id", "id", "sid")
    rule_name = _pick_payload_value(
        [raw_payload, rule_payload],
        "rule_name",
        "signature",
        "description",
        "name",
    )
    provider = _pick_payload_value([raw_payload, rule_payload], "provider", "engine")

    metadata = {
        key: value
        for key, value in raw_payload.items()
        if key in {"service", "signature", "signature_id", "agent", "group"}
    }
    if rule_payload:
        metadata["rule"] = rule_payload

    if rule_id is None and rule_name is None and provider is None and not metadata:
        return None

    return AlertSourceRuleResponse(
        rule_id=str(rule_id) if rule_id is not None else None,
        name=str(rule_name) if rule_name is not None else None,
        provider=str(provider) if provider is not None else _titleize_source(raw_alert.source),
        metadata=metadata,
    )


def _extract_response_target(response_action: ResponseAction) -> str | None:
    return _pick_payload_value(
        [response_action.details],
        "target",
        "username",
        "path",
        "ip_address",
        "hostname",
        "asset_hostname",
    )


def _extract_response_mode(response_action: ResponseAction) -> str | None:
    mode = response_action.details.get("mode")
    return str(mode) if mode is not None else None


def _extract_response_summary(response_action: ResponseAction) -> str | None:
    summary = _pick_payload_value(
        [response_action.details],
        "summary",
        "result",
        "message",
        "reason",
    )
    return str(summary) if summary is not None else None


def _format_audit_title(action: str) -> str:
    return action.replace(".", " ").replace("_", " ").title()


def _build_analyst_notes(audit_logs: list[AuditLog]) -> list[AnalystNoteResponse]:
    notes: list[AnalystNoteResponse] = []
    for audit_log in audit_logs:
        content = _pick_payload_value([audit_log.details], "note", "content", "message")
        if "note" not in audit_log.action or content is None:
            continue

        notes.append(
            AnalystNoteResponse(
                id=str(audit_log.id),
                author=to_user_brief_response(audit_log.actor) if audit_log.actor else None,
                content=str(content),
                created_at=audit_log.created_at,
            )
        )
    return notes


def _build_alert_score_factors(alert: NormalizedAlert) -> list[str]:
    factors = [
        f"Detection type: {alert.detection_type.value}",
        f"Alert severity score: {alert.severity}",
    ]
    if alert.asset is not None:
        factors.append(f"Asset criticality: {alert.asset.criticality.value}")
    if source_ip := _extract_source_ip(alert):
        factors.append(f"Source IP observed: {source_ip}")
    if destination_port := _extract_destination_port(alert):
        factors.append(f"Destination port involved: {destination_port}")
    if alert.incident is not None:
        factors.append("Linked incident already exists for this alert")
    return factors[:4]


def _build_incident_priority_factors(incident: Incident) -> list[str]:
    factors = [f"Incident priority: {incident.priority.value}"]
    alert = incident.normalized_alert

    if alert.asset is not None:
        factors.append(f"Primary asset criticality: {alert.asset.criticality.value}")
    factors.append(f"Detection type: {alert.detection_type.value}")
    if alert.risk_score is not None:
        factors.append(f"Alert risk score: {round(alert.risk_score.score * 100)}")
    if incident.response_actions:
        factors.append(f"Linked response actions: {len(incident.response_actions)}")
    return factors[:4]


def _state_transition_capabilities(
    incident: Incident,
) -> IncidentStateTransitionCapabilitiesResponse:
    if incident.status.value == "open":
        available_actions = ["triage", "investigate", "mark_false_positive"]
        allowed_target_states = [IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED]
    elif incident.status.value == "investigating":
        available_actions = ["contain", "resolve", "mark_false_positive"]
        allowed_target_states = [IncidentStatus.RESOLVED]
    else:
        available_actions = ["reopen"]
        allowed_target_states = [IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]

    return IncidentStateTransitionCapabilitiesResponse(
        current_state=incident.status,
        available_actions=available_actions,
        allowed_target_states=allowed_target_states,
    )


def to_role_response(role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
    )


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        role=to_role_response(user.role),
    )


def to_user_brief_response(user: User) -> UserBriefResponse:
    return UserBriefResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=to_role_response(user.role),
    )


def to_asset_summary_response(asset: Asset) -> AssetSummaryResponse:
    return AssetSummaryResponse(
        id=asset.id,
        hostname=asset.hostname,
        ip_address=asset.ip_address,
        operating_system=asset.operating_system,
        criticality=asset.criticality,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def to_raw_alert_summary_response(raw_alert: RawAlert) -> RawAlertSummaryResponse:
    return RawAlertSummaryResponse(
        id=raw_alert.id,
        source=raw_alert.source,
        external_id=raw_alert.external_id,
        detection_type=raw_alert.detection_type,
        severity=raw_alert.severity,
        raw_payload=raw_alert.raw_payload,
        received_at=raw_alert.received_at,
    )


def to_risk_score_response(risk_score: RiskScore) -> RiskScoreResponse:
    return RiskScoreResponse(
        id=risk_score.id,
        score=risk_score.score,
        confidence=risk_score.confidence,
        reasoning=risk_score.reasoning,
        calculated_at=risk_score.calculated_at,
    )


def to_incident_reference_response(incident: Incident) -> IncidentReferenceResponse:
    return IncidentReferenceResponse(
        id=incident.id,
        title=incident.title,
        status=incident.status,
        priority=incident.priority,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


def to_alert_summary_response(alert: NormalizedAlert) -> AlertSummaryResponse:
    return AlertSummaryResponse(
        id=alert.id,
        source=alert.source,
        title=alert.title,
        description=alert.description,
        detection_type=alert.detection_type,
        severity=alert.severity,
        status=alert.status,
        normalized_payload=alert.normalized_payload,
        created_at=alert.created_at,
        asset=to_asset_summary_response(alert.asset) if alert.asset else None,
        raw_alert=to_raw_alert_summary_response(alert.raw_alert),
        risk_score=to_risk_score_response(alert.risk_score) if alert.risk_score else None,
        incident=to_incident_reference_response(alert.incident) if alert.incident else None,
    )


def to_incident_summary_response(incident: Incident) -> IncidentSummaryResponse:
    return IncidentSummaryResponse(
        id=incident.id,
        title=incident.title,
        summary=incident.summary,
        status=incident.status,
        priority=incident.priority,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        assigned_user=to_user_brief_response(incident.assigned_user)
        if incident.assigned_user
        else None,
        alert=to_alert_summary_response(incident.normalized_alert),
    )


def to_response_action_reference_response(
    response_action: ResponseAction,
) -> ResponseActionReferenceResponse:
    return ResponseActionReferenceResponse(
        id=response_action.id,
        action_type=response_action.action_type,
        status=response_action.status,
        details=response_action.details,
        created_at=response_action.created_at,
        executed_at=response_action.executed_at,
        requested_by=to_user_brief_response(response_action.requested_by)
        if response_action.requested_by
        else None,
    )


def to_response_action_summary_response(
    response_action: ResponseAction,
) -> ResponseActionSummaryResponse:
    return ResponseActionSummaryResponse(
        id=response_action.id,
        action_type=response_action.action_type,
        status=response_action.status,
        details=response_action.details,
        created_at=response_action.created_at,
        executed_at=response_action.executed_at,
        requested_by=to_user_brief_response(response_action.requested_by)
        if response_action.requested_by
        else None,
        incident=to_incident_reference_response(response_action.incident),
    )


def to_audit_log_response(audit_log: AuditLog) -> AuditLogResponse:
    return AuditLogResponse(
        id=audit_log.id,
        action=audit_log.action,
        entity_type=audit_log.entity_type,
        entity_id=audit_log.entity_id,
        details=audit_log.details,
        created_at=audit_log.created_at,
        actor=to_user_brief_response(audit_log.actor) if audit_log.actor else None,
    )


def to_response_action_detail_response(
    response_action: ResponseAction,
) -> ResponseActionDetailResponse:
    return ResponseActionDetailResponse(
        id=response_action.id,
        action_type=response_action.action_type,
        status=response_action.status,
        target=_extract_response_target(response_action),
        mode=_extract_response_mode(response_action),
        result_summary=_extract_response_summary(response_action),
        details=response_action.details,
        created_at=response_action.created_at,
        executed_at=response_action.executed_at,
        requested_by=to_user_brief_response(response_action.requested_by)
        if response_action.requested_by
        else None,
    )


def to_activity_entry_response(audit_log: AuditLog) -> ActivityEntryResponse:
    description = (
        _pick_payload_value([audit_log.details], "summary", "result", "message", "note", "content")
        if audit_log.details
        else None
    )
    return ActivityEntryResponse(
        id=str(audit_log.id),
        timestamp=audit_log.created_at,
        category=audit_log.entity_type,
        title=_format_audit_title(audit_log.action),
        description=str(description) if description is not None else None,
        actor=to_user_brief_response(audit_log.actor) if audit_log.actor else None,
        details=audit_log.details,
    )


def to_alert_detail_response(
    alert: NormalizedAlert,
    audit_logs: list[AuditLog],
) -> AlertDetailResponse:
    priority_label = _priority_label_from_risk(alert.risk_score, alert.severity)

    return AlertDetailResponse(
        id=alert.id,
        title=alert.title,
        description=alert.description,
        detection_type=alert.detection_type,
        source_type=_titleize_source(alert.source),
        severity=_severity_label_from_score(alert.severity),
        severity_score=alert.severity,
        status=alert.status,
        risk_score=round(alert.risk_score.score * 100) if alert.risk_score else None,
        risk_confidence=alert.risk_score.confidence if alert.risk_score else None,
        priority_label=priority_label,
        linked_incident=AlertLinkedIncidentResponse(
            id=alert.incident.id,
            title=alert.incident.title,
            status=alert.incident.status,
            priority=alert.incident.priority,
            created_at=alert.incident.created_at,
            updated_at=alert.incident.updated_at,
            assigned_user=to_user_brief_response(alert.incident.assigned_user)
            if alert.incident.assigned_user
            else None,
        )
        if alert.incident
        else None,
        asset=to_asset_summary_response(alert.asset) if alert.asset else None,
        source_ip=_extract_source_ip(alert),
        destination_ip=_extract_destination_ip(alert),
        destination_port=_extract_destination_port(alert),
        username=_extract_username(alert),
        timestamp=alert.created_at,
        source_rule=_extract_source_rule(alert.raw_alert),
        normalized_details=alert.normalized_payload,
        raw_payload=alert.raw_alert.raw_payload,
        score_explanation=AlertScoreExplanationResponse(
            label="Alert risk explanation",
            summary=(
                f"Alert is currently scored {priority_label.value if priority_label else 'unrated'} "
                "based on normalized telemetry and asset context."
            ),
            rationale=alert.risk_score.reasoning,
            factors=_build_alert_score_factors(alert),
            confidence=alert.risk_score.confidence,
        )
        if alert.risk_score
        else None,
        related_responses=[
            to_response_action_detail_response(action)
            for action in sorted(
                alert.incident.response_actions if alert.incident else [],
                key=lambda action: action.created_at,
                reverse=True,
            )
        ],
        analyst_notes=_build_analyst_notes(audit_logs),
        audit_history=[
            to_activity_entry_response(audit_log)
            for audit_log in sorted(audit_logs, key=lambda log: log.created_at, reverse=True)
        ],
    )


def to_incident_linked_alert_response(
    alert: NormalizedAlert,
) -> IncidentLinkedAlertResponse:
    return IncidentLinkedAlertResponse(
        id=alert.id,
        title=alert.title,
        detection_type=alert.detection_type,
        source_type=_titleize_source(alert.source),
        severity=_severity_label_from_score(alert.severity),
        status=alert.status,
        risk_score=round(alert.risk_score.score * 100) if alert.risk_score else None,
        timestamp=alert.created_at,
        asset_hostname=alert.asset.hostname if alert.asset else None,
        source_ip=_extract_source_ip(alert),
        destination_ip=_extract_destination_ip(alert),
        destination_port=_extract_destination_port(alert),
        username=_extract_username(alert),
    )


def to_incident_detail_response(
    incident: Incident,
    audit_logs: list[AuditLog],
) -> IncidentDetailResponse:
    primary_asset = (
        to_asset_summary_response(incident.normalized_alert.asset)
        if incident.normalized_alert.asset
        else None
    )

    correlation_keys = {
        "detection_type": incident.normalized_alert.detection_type.value,
        "source_type": _titleize_source(incident.normalized_alert.source),
        "asset_hostname": incident.normalized_alert.asset.hostname
        if incident.normalized_alert.asset
        else None,
        "source_ip": _extract_source_ip(incident.normalized_alert),
        "destination_port": _extract_destination_port(incident.normalized_alert),
    }
    evidence_items = [
        f"Detection type: {incident.normalized_alert.detection_type.value}",
        f"Source type: {_titleize_source(incident.normalized_alert.source)}",
    ]
    if incident.normalized_alert.asset is not None:
        evidence_items.append(
            f"Primary asset: {incident.normalized_alert.asset.hostname}"
        )
    if source_ip := _extract_source_ip(incident.normalized_alert):
        evidence_items.append(f"Source IP: {source_ip}")
    if incident.response_actions:
        evidence_items.append(
            f"Linked response actions: {len(incident.response_actions)}"
        )

    timeline_entries = [
        ActivityEntryResponse(
            id=f"incident-created-{incident.id}",
            timestamp=incident.created_at,
            category="incident",
            title="Incident created",
            description=incident.summary or incident.title,
            actor=to_user_brief_response(incident.assigned_user)
            if incident.assigned_user
            else None,
            details={
                "priority": incident.priority.value,
                "state": incident.status.value,
            },
        )
    ]
    timeline_entries.extend(
        ActivityEntryResponse(
            id=f"response-{response_action.id}",
            timestamp=response_action.executed_at or response_action.created_at,
            category="response",
            title=response_action.action_type.replace("_", " ").title(),
            description=_extract_response_summary(response_action),
            actor=to_user_brief_response(response_action.requested_by)
            if response_action.requested_by
            else None,
            details=response_action.details,
        )
        for response_action in incident.response_actions
    )
    timeline_entries.extend(to_activity_entry_response(audit_log) for audit_log in audit_logs)

    return IncidentDetailResponse(
        id=incident.id,
        title=incident.title,
        summary=incident.summary,
        priority=incident.priority,
        state=incident.status,
        assignee=to_user_brief_response(incident.assigned_user)
        if incident.assigned_user
        else None,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        primary_asset=primary_asset,
        affected_assets=[primary_asset] if primary_asset else [],
        linked_alerts=[to_incident_linked_alert_response(incident.normalized_alert)],
        grouped_evidence=IncidentGroupedEvidenceResponse(
            summary=incident.summary
            or "Correlation is currently grouped around the primary normalized alert and linked workflow evidence.",
            evidence_items=evidence_items,
            correlation_keys={
                key: value for key, value in correlation_keys.items() if value is not None
            },
        ),
        response_history=[
            to_response_action_detail_response(action)
            for action in sorted(
                incident.response_actions,
                key=lambda action: action.created_at,
                reverse=True,
            )
        ],
        analyst_notes=_build_analyst_notes(audit_logs),
        timeline=sorted(timeline_entries, key=lambda entry: entry.timestamp),
        priority_explanation=IncidentPriorityExplanationResponse(
            label="Incident priority explanation",
            summary=(
                f"Incident is currently prioritized {incident.priority.value} based on the "
                "primary alert, asset context, and linked workflow evidence."
            ),
            rationale=incident.summary
            or incident.normalized_alert.description
            or "Priority is derived from the normalized alert and current investigation context.",
            factors=_build_incident_priority_factors(incident),
        ),
        state_transition_capabilities=_state_transition_capabilities(incident),
    )
