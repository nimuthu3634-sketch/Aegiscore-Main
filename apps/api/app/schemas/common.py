from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ScoreMethod,
    ResponseStatus,
    RoleName,
)
from app.schemas.base import APIModel
from app.schemas.listing import (
    AssetAgentStatusLabel,
    AssetEnvironmentLabel,
    ListMetaResponse,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
)


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
    agent_status: AssetAgentStatusLabel | None = None
    recent_alerts_count: int = 0
    last_seen_at: datetime | None = None
    open_incidents_count: int = 0
    environment: AssetEnvironmentLabel | None = None
    created_at: datetime
    updated_at: datetime


class AssetListResponse(APIModel):
    items: list[AssetSummaryResponse]
    meta: ListMetaResponse


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
    priority_label: IncidentPriority | None = None
    scoring_method: ScoreMethod | None = None
    baseline_version: str | None = None
    model_version: str | None = None
    explanation: dict[str, Any] | None = None
    feature_snapshot: dict[str, Any] | None = None
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
    policy_id: UUID | None = None
    policy_name: str | None = None
    target: str | None = None
    result_summary: str | None = None
    result_message: str | None = None
    attempt_count: int = 0
    details: dict
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None


class ResponseActionDetailResponse(APIModel):
    id: UUID
    action_type: str
    status: ResponseStatus
    policy_id: UUID | None = None
    policy_name: str | None = None
    target: str | None = None
    mode: ResponseModeLabel | None = None
    result_summary: str | None = None
    result_message: str | None = None
    attempt_count: int = 0
    details: dict[str, Any]
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None


class AnalystNoteResponse(APIModel):
    id: str
    author: UserBriefResponse | None
    content: str
    created_at: datetime
    updated_at: datetime | None = None


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
    source_type: str
    title: str
    description: str | None
    detection_type: DetectionType
    severity: int
    severity_label: str
    status: AlertStatus
    status_label: str
    normalized_payload: dict
    created_at: datetime
    asset: AssetSummaryResponse | None
    asset_name: str | None = None
    raw_alert: RawAlertSummaryResponse
    event_id: str | None = None
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    username: str | None = None
    risk_score: RiskScoreResponse | None
    risk_score_value: int | None = None
    incident: IncidentReferenceResponse | None


class AlertListResponse(APIModel):
    items: list[AlertSummaryResponse]
    meta: ListMetaResponse


class IncidentSummaryResponse(APIModel):
    id: UUID
    title: str
    summary: str | None
    status: IncidentStatus
    state_label: str
    priority: IncidentPriority
    created_at: datetime
    updated_at: datetime
    assigned_user: UserBriefResponse | None
    assignee_name: str | None = None
    linked_alerts_count: int = 0
    primary_asset_name: str | None = None
    detection_type: DetectionType
    source_type: str
    alert: AlertSummaryResponse


class IncidentListResponse(APIModel):
    items: list[IncidentSummaryResponse]
    meta: ListMetaResponse


class IncidentDetailResponse(IncidentSummaryResponse):
    response_actions: list[ResponseActionReferenceResponse]
    audit_logs: list[AuditLogResponse]


class ResponseActionSummaryResponse(APIModel):
    id: UUID
    action_type: str
    status: ResponseStatus
    execution_status_label: ResponseExecutionStatusLabel
    policy_id: UUID | None = None
    policy_name: str | None = None
    target: str | None = None
    mode: ResponseModeLabel | None = None
    result_summary: str | None = None
    result_message: str | None = None
    attempt_count: int = 0
    details: dict
    created_at: datetime
    executed_at: datetime | None
    requested_by: UserBriefResponse | None
    incident: IncidentReferenceResponse


class ResponseActionListResponse(APIModel):
    items: list[ResponseActionSummaryResponse]
    meta: ListMetaResponse
