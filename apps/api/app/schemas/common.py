from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ResponseStatus,
    RoleName,
)
from app.schemas.base import APIModel


class RoleResponse(APIModel):
    id: UUID
    name: RoleName


class UserResponse(APIModel):
    id: UUID
    username: str
    full_name: str | None
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    role: RoleResponse


class UserBriefResponse(APIModel):
    id: UUID
    username: str
    full_name: str | None
    role: RoleResponse


class AssetSummaryResponse(APIModel):
    id: UUID
    hostname: str
    ip_address: str
    operating_system: str | None
    criticality: AssetCriticality
    created_at: datetime
    updated_at: datetime


class AssetListResponse(APIModel):
    items: list[AssetSummaryResponse]


class RawAlertSummaryResponse(APIModel):
    id: UUID
    source: str
    external_id: str | None
    detection_type: DetectionType
    severity: int
    raw_payload: dict
    received_at: datetime


class RiskScoreResponse(APIModel):
    id: UUID
    score: float
    confidence: float
    reasoning: str
    calculated_at: datetime


class IncidentReferenceResponse(APIModel):
    id: UUID
    title: str
    status: IncidentStatus
    priority: IncidentPriority
    created_at: datetime
    updated_at: datetime


class AuditLogResponse(APIModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: str
    details: dict
    created_at: datetime
    actor: UserBriefResponse | None


class ResponseActionReferenceResponse(APIModel):
    id: UUID
    action_type: str
    status: ResponseStatus
    details: dict
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None


class ResponseActionDetailResponse(APIModel):
    id: UUID
    action_type: str
    status: ResponseStatus
    target: str | None
    mode: str | None
    result_summary: str | None
    details: dict[str, Any]
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None


class AnalystNoteResponse(APIModel):
    id: str
    author: UserBriefResponse | None
    content: str
    created_at: datetime


class ActivityEntryResponse(APIModel):
    id: str
    timestamp: datetime
    category: str
    title: str
    description: str | None
    actor: UserBriefResponse | None
    details: dict[str, Any]


class AlertSummaryResponse(APIModel):
    id: UUID
    source: str
    title: str
    description: str | None
    detection_type: DetectionType
    severity: int
    status: AlertStatus
    normalized_payload: dict
    created_at: datetime
    asset: AssetSummaryResponse | None
    raw_alert: RawAlertSummaryResponse
    risk_score: RiskScoreResponse | None
    incident: IncidentReferenceResponse | None


class AlertListResponse(APIModel):
    items: list[AlertSummaryResponse]


class IncidentSummaryResponse(APIModel):
    id: UUID
    title: str
    summary: str | None
    status: IncidentStatus
    priority: IncidentPriority
    created_at: datetime
    updated_at: datetime
    assigned_user: UserBriefResponse | None
    alert: AlertSummaryResponse


class IncidentListResponse(APIModel):
    items: list[IncidentSummaryResponse]


class IncidentDetailResponse(IncidentSummaryResponse):
    response_actions: list[ResponseActionReferenceResponse]
    audit_logs: list[AuditLogResponse]


class ResponseActionSummaryResponse(APIModel):
    id: UUID
    action_type: str
    status: ResponseStatus
    details: dict
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None
    incident: IncidentReferenceResponse


class ResponseActionListResponse(APIModel):
    items: list[ResponseActionSummaryResponse]
