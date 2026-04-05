from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.schemas.common import (
    AlertSummaryResponse,
    AssetSummaryResponse,
    AuditLogResponse,
    IncidentReferenceResponse,
    IncidentSummaryResponse,
    RawAlertSummaryResponse,
    ResponseActionReferenceResponse,
    ResponseActionSummaryResponse,
    RiskScoreResponse,
    RoleResponse,
    UserBriefResponse,
    UserResponse,
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

