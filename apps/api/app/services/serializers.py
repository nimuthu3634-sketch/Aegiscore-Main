from datetime import UTC, datetime, timedelta
from typing import Any

from app.models.analyst_note import AnalystNote
from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import ResponseMode, ResponseStatus
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
from app.schemas.listing import (
    AlertSeverityLabel,
    AssetAgentStatusLabel,
    AssetEnvironmentLabel,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
)
from app.schemas.incidents import (
    IncidentDetailResponse,
    IncidentGroupedEvidenceResponse,
    IncidentLinkedAlertResponse,
    IncidentPriorityExplanationResponse,
    IncidentStateTransitionCapabilitiesResponse,
)
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.features import (
    extract_destination_ip,
    extract_destination_port,
    extract_source_ip,
    extract_username,
)
from app.services.scoring.service import build_incident_priority_summary
from app.services.workflows import (
    get_allowed_incident_target_states,
    get_available_incident_actions,
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


def _asset_agent_status_from_timestamp(updated_at: datetime) -> AssetAgentStatusLabel:
    now = datetime.now(UTC)
    age = now - updated_at.astimezone(UTC)
    if age <= timedelta(minutes=30):
        return AssetAgentStatusLabel.ONLINE
    if age <= timedelta(hours=2):
        return AssetAgentStatusLabel.DEGRADED
    return AssetAgentStatusLabel.OFFLINE


def _asset_environment_from_hostname(hostname: str) -> AssetEnvironmentLabel:
    lowered = hostname.lower()
    if "branch" in lowered or "office" in lowered:
        return AssetEnvironmentLabel.OFFICE
    if "edge" in lowered or "warehouse" in lowered or "vpn" in lowered or "remote" in lowered:
        return AssetEnvironmentLabel.REMOTE
    return AssetEnvironmentLabel.PRODUCTION


def _response_execution_status_label(
    response_action: ResponseAction,
) -> ResponseExecutionStatusLabel:
    if response_action.status == ResponseStatus.COMPLETED:
        return ResponseExecutionStatusLabel.SUCCEEDED
    if response_action.status == ResponseStatus.FAILED:
        return ResponseExecutionStatusLabel.FAILED
    return ResponseExecutionStatusLabel.PENDING


def _response_mode_label(response_action: ResponseAction) -> ResponseModeLabel | None:
    mode = _extract_response_mode(response_action)
    if mode in {"dry-run", "dry_run"}:
        return ResponseModeLabel.DRY_RUN
    if mode is None:
        return None
    return ResponseModeLabel.LIVE


def _alert_status_label(alert: NormalizedAlert) -> str:
    if alert.status.value == "resolved":
        return "resolved"
    if alert.incident is not None:
        if alert.incident.status.value in {"resolved", "false_positive"}:
            return "resolved"
        if alert.incident.status.value == "contained":
            return "contained"

    has_pending_response = bool(
        alert.incident
        and any(
            action.status in {ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS}
            for action in alert.incident.response_actions
        )
    )
    if has_pending_response:
        return "pending_response"
    if alert.status.value == "investigating" or (
        alert.incident is not None and alert.incident.status.value == "investigating"
    ):
        return "investigating"
    if alert.incident is not None and alert.incident.status.value == "triaged":
        return "triaged"
    return "new"


def _incident_state_label(incident: Incident) -> str:
    return incident.status.value


def _priority_label_from_risk(
    risk_score: RiskScore | None,
    severity: int,
) -> AlertSeverityLabel | None:
    if risk_score is None:
        return _severity_label_from_score(severity)

    if risk_score.priority_label is not None:
        return AlertSeverityLabel(risk_score.priority_label.value)

    return AlertSeverityLabel(priority_from_score(risk_score.score).value)


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
    return extract_source_ip(alert)


def _extract_destination_ip(alert: NormalizedAlert) -> str | None:
    return extract_destination_ip(alert)


def _extract_destination_port(alert: NormalizedAlert) -> int | None:
    return extract_destination_port(alert)


def _extract_username(alert: NormalizedAlert) -> str | None:
    return extract_username(alert)


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
    if response_action.mode == ResponseMode.DRY_RUN:
        return ResponseMode.DRY_RUN.value
    if response_action.mode == ResponseMode.LIVE:
        return ResponseMode.LIVE.value

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


def _build_analyst_notes(notes: list[AnalystNote]) -> list[AnalystNoteResponse]:
    return [to_analyst_note_response(note) for note in notes]


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


def _incident_alerts(incident: Incident) -> list[NormalizedAlert]:
    return sorted(
        incident.alerts,
        key=lambda alert: (alert.created_at, str(alert.id)),
        reverse=True,
    )


def _incident_primary_alert(incident: Incident) -> NormalizedAlert | None:
    if incident.primary_alert is not None:
        return incident.primary_alert

    alerts = _incident_alerts(incident)
    if not alerts:
        return None

    return sorted(
        alerts,
        key=lambda alert: (alert.severity, alert.created_at, str(alert.id)),
        reverse=True,
    )[0]


def _unique_assets_for_incident(incident: Incident) -> list[Asset]:
    seen_asset_ids: set[str] = set()
    assets: list[Asset] = []
    for alert in _incident_alerts(incident):
        if alert.asset is None:
            continue
        asset_key = str(alert.asset.id)
        if asset_key in seen_asset_ids:
            continue
        seen_asset_ids.add(asset_key)
        assets.append(alert.asset)
    return assets


def _build_incident_priority_factors(incident: Incident) -> list[str]:
    factors = [f"Incident priority: {incident.priority.value}"]
    primary_alert = _incident_primary_alert(incident)
    if primary_alert is None:
        return factors

    linked_alerts = _incident_alerts(incident)

    if primary_alert.asset is not None:
        factors.append(
            f"Primary asset criticality: {primary_alert.asset.criticality.value}"
        )
    factors.append(f"Detection type: {primary_alert.detection_type.value}")
    if primary_alert.risk_score is not None:
        factors.append(
            f"Alert risk score: {round(primary_alert.risk_score.score)}"
        )
    if len(linked_alerts) > 1:
        factors.append(f"Correlated alerts: {len(linked_alerts)}")
    if incident.response_actions:
        factors.append(f"Linked response actions: {len(incident.response_actions)}")
    return factors[:4]


def _state_transition_capabilities(
    incident: Incident,
) -> IncidentStateTransitionCapabilitiesResponse:
    return IncidentStateTransitionCapabilitiesResponse(
        current_state=incident.status,
        available_actions=get_available_incident_actions(incident.status),
        allowed_target_states=get_allowed_incident_target_states(incident.status),
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


def to_asset_summary_response(
    asset: Asset,
    *,
    recent_alerts_count: int = 0,
    open_incidents_count: int = 0,
) -> AssetSummaryResponse:
    return AssetSummaryResponse(
        id=asset.id,
        hostname=asset.hostname,
        ip_address=asset.ip_address,
        operating_system=asset.operating_system,
        criticality=asset.criticality,
        agent_status=_asset_agent_status_from_timestamp(asset.updated_at),
        recent_alerts_count=recent_alerts_count,
        last_seen_at=asset.updated_at,
        open_incidents_count=open_incidents_count,
        environment=_asset_environment_from_hostname(asset.hostname),
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
        score=round(risk_score.score, 2),
        confidence=risk_score.confidence,
        reasoning=risk_score.reasoning,
        priority_label=risk_score.priority_label,
        scoring_method=risk_score.scoring_method,
        baseline_version=risk_score.baseline_version,
        model_version=risk_score.model_version,
        explanation=risk_score.explanation,
        feature_snapshot=risk_score.feature_snapshot,
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
        source_type=_titleize_source(alert.source),
        title=alert.title,
        description=alert.description,
        detection_type=alert.detection_type,
        severity=alert.severity,
        severity_label=_severity_label_from_score(alert.severity).value,
        status=alert.status,
        status_label=_alert_status_label(alert),
        normalized_payload=alert.normalized_payload,
        created_at=alert.created_at,
        asset=to_asset_summary_response(alert.asset) if alert.asset else None,
        asset_name=alert.asset.hostname if alert.asset else None,
        raw_alert=to_raw_alert_summary_response(alert.raw_alert),
        event_id=alert.raw_alert.external_id or str(alert.raw_alert.id),
        source_ip=_extract_source_ip(alert),
        destination_ip=_extract_destination_ip(alert),
        destination_port=_extract_destination_port(alert),
        username=_extract_username(alert),
        risk_score=to_risk_score_response(alert.risk_score) if alert.risk_score else None,
        risk_score_value=round(alert.risk_score.score) if alert.risk_score else None,
        incident=to_incident_reference_response(alert.incident) if alert.incident else None,
    )


def to_incident_summary_response(incident: Incident) -> IncidentSummaryResponse:
    primary_alert = _incident_primary_alert(incident)
    if primary_alert is None:
        raise ValueError(f"Incident {incident.id} does not have a primary alert.")

    return IncidentSummaryResponse(
        id=incident.id,
        title=incident.title,
        summary=incident.summary,
        status=incident.status,
        state_label=_incident_state_label(incident),
        priority=incident.priority,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        assigned_user=to_user_brief_response(incident.assigned_user)
        if incident.assigned_user
        else None,
        assignee_name=incident.assigned_user.full_name
        if incident.assigned_user and incident.assigned_user.full_name
        else incident.assigned_user.username
        if incident.assigned_user
        else None,
        linked_alerts_count=len(_incident_alerts(incident)),
        primary_asset_name=primary_alert.asset.hostname
        if primary_alert.asset
        else None,
        detection_type=primary_alert.detection_type,
        source_type=_titleize_source(primary_alert.source),
        alert=to_alert_summary_response(primary_alert),
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
        execution_status_label=_response_execution_status_label(response_action),
        target=_extract_response_target(response_action),
        mode=_response_mode_label(response_action),
        result_summary=_extract_response_summary(response_action),
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


def to_analyst_note_response(note: AnalystNote) -> AnalystNoteResponse:
    return AnalystNoteResponse(
        id=str(note.id),
        author=to_user_brief_response(note.author) if note.author else None,
        content=note.content,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def to_response_action_detail_response(
    response_action: ResponseAction,
) -> ResponseActionDetailResponse:
    return ResponseActionDetailResponse(
        id=response_action.id,
        action_type=response_action.action_type,
        status=response_action.status,
        target=_extract_response_target(response_action),
        mode=_response_mode_label(response_action),
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


def _build_alert_score_explanation(
    alert: NormalizedAlert,
    priority_label: AlertSeverityLabel | None,
) -> AlertScoreExplanationResponse | None:
    if alert.risk_score is None:
        return None

    explanation = alert.risk_score.explanation or {}
    factors = explanation.get("factors")
    drivers = explanation.get("drivers")

    return AlertScoreExplanationResponse(
        label=str(explanation.get("label") or "Alert risk explanation"),
        summary=str(
            explanation.get("summary")
            or (
                f"Alert is currently scored {priority_label.value if priority_label else 'unrated'} "
                "based on normalized telemetry and asset context."
            )
        ),
        rationale=str(explanation.get("rationale") or alert.risk_score.reasoning),
        factors=[str(factor) for factor in (factors or _build_alert_score_factors(alert))],
        confidence=alert.risk_score.confidence,
        scoring_method=alert.risk_score.scoring_method,
        baseline_version=alert.risk_score.baseline_version,
        model_version=alert.risk_score.model_version,
        drivers=drivers if isinstance(drivers, list) else None,
        feature_snapshot=alert.risk_score.feature_snapshot,
    )


def to_alert_detail_response(
    alert: NormalizedAlert,
    audit_logs: list[AuditLog],
    analyst_notes: list[AnalystNote],
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
        status_label=_alert_status_label(alert),
        risk_score=round(alert.risk_score.score) if alert.risk_score else None,
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
        score_explanation=_build_alert_score_explanation(alert, priority_label),
        related_responses=[
            to_response_action_detail_response(action)
            for action in sorted(
                alert.incident.response_actions if alert.incident else [],
                key=lambda action: action.created_at,
                reverse=True,
            )
        ],
        analyst_notes=_build_analyst_notes(analyst_notes),
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
        risk_score=round(alert.risk_score.score) if alert.risk_score else None,
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
    analyst_notes: list[AnalystNote],
) -> IncidentDetailResponse:
    primary_alert = _incident_primary_alert(incident)
    if primary_alert is None:
        raise ValueError(f"Incident {incident.id} does not have a primary alert.")

    linked_alerts = _incident_alerts(incident)
    unique_assets = _unique_assets_for_incident(incident)
    primary_asset = (
        to_asset_summary_response(primary_alert.asset) if primary_alert.asset else None
    )
    priority_summary = build_incident_priority_summary(incident)

    detection_types = sorted({alert.detection_type.value for alert in linked_alerts})
    source_types = sorted({_titleize_source(alert.source) for alert in linked_alerts})
    asset_hostnames = sorted(
        {alert.asset.hostname for alert in linked_alerts if alert.asset is not None}
    )
    source_ips = sorted(
        {
            source_ip
            for alert in linked_alerts
            if (source_ip := _extract_source_ip(alert)) is not None
        }
    )
    destination_ports = sorted(
        {
            destination_port
            for alert in linked_alerts
            if (destination_port := _extract_destination_port(alert)) is not None
        }
    )

    correlation_keys = {
        "linked_alert_count": len(linked_alerts),
        "detection_types": detection_types,
        "source_types": source_types,
        "asset_hostnames": asset_hostnames,
        "source_ips": source_ips,
        "destination_ports": destination_ports,
    }
    evidence_items = [
        f"Linked alerts: {len(linked_alerts)}",
        f"Detection types: {', '.join(detection_types)}",
        f"Source types: {', '.join(source_types)}",
    ]
    if asset_hostnames:
        evidence_items.append(f"Affected assets: {', '.join(asset_hostnames)}")
    if source_ips:
        evidence_items.append(f"Observed source IPs: {', '.join(source_ips)}")
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
        affected_assets=[
            to_asset_summary_response(asset) for asset in unique_assets
        ],
        linked_alerts=[
            to_incident_linked_alert_response(alert) for alert in linked_alerts
        ],
        grouped_evidence=IncidentGroupedEvidenceResponse(
            summary=incident.summary
            or (
                f"{len(linked_alerts)} linked alerts have been grouped into a single "
                "investigation based on shared asset and detection context."
            ),
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
        analyst_notes=_build_analyst_notes(analyst_notes),
        timeline=sorted(timeline_entries, key=lambda entry: entry.timestamp),
        priority_explanation=IncidentPriorityExplanationResponse(
            label="Incident priority explanation",
            summary=(
                f"Incident is currently prioritized {incident.priority.value} with a "
                f"rollup score of {priority_summary['score']} based on linked alert risk, "
                "correlated evidence, and workflow history."
            ),
            rationale=incident.summary
            or primary_alert.description
            or "Priority is derived from the normalized alert and current investigation context.",
            factors=priority_summary["factors"],
            rollup_score=priority_summary["score"],
            linked_alerts_count=len(linked_alerts),
            scoring_methods=priority_summary["scoring_methods"],
        ),
        state_transition_capabilities=_state_transition_capabilities(incident),
    )
