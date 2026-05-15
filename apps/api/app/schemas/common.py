from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

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


# Common response schemas reused by many API routes.
class RoleResponse(APIModel):
    id: UUID
    name: RoleName


# Full user details returned by authentication and user-related APIs.
class UserResponse(APIModel):
    id: UUID
    username: str
    full_name: str | None
    is_active: bool
    mfa_enabled: bool = False
    last_login_at: datetime | None
    created_at: datetime
    role: RoleResponse


# Short user details used when showing owners, analysts, or actors.
class UserBriefResponse(APIModel):
    id: UUID
    username: str
    full_name: str | None
    role: RoleResponse


# Notification details returned for incidents and response actions.
class NotificationEventResponse(APIModel):
    id: UUID
    channel: str
    delivery_mode: str
    trigger_type: str
    trigger_value: str
    recipient: str
    subject: str
    status: str
    error_message: str | None
    created_at: datetime
    sent_at: datetime | None


# Basic asset details shown in alert, incident, and asset pages.
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
    # List response includes both asset rows and pagination details.
    items: list[AssetSummaryResponse]
    meta: ListMetaResponse


# Summary of the original raw alert before normalization.
class RawAlertSummaryResponse(APIModel):
    id: UUID
    source: str
    external_id: str | None
    detection_type: DetectionType
    severity: int
    raw_payload: dict
    received_at: datetime


# Risk scoring result returned with alert data.
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


# Small incident object used when linking alerts to incidents.
class IncidentReferenceResponse(APIModel):
    id: UUID
    title: str
    status: IncidentStatus
    priority: IncidentPriority
    created_at: datetime
    updated_at: datetime


# Audit log response used to show user/system activity history.
class AuditLogResponse(APIModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: str
    details: dict
    created_at: datetime
    actor: UserBriefResponse | None


# Short response action details used in incident summaries.
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


# Detailed response action object used in alert and incident detail pages.
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
    related_notifications: list[NotificationEventResponse] = Field(default_factory=list)


# Analyst note shown in alert and incident investigation pages.
class AnalystNoteResponse(APIModel):
    id: str
    author: UserBriefResponse | None
    content: str
    created_at: datetime
    updated_at: datetime | None = None


# Generic activity entry used for investigation timelines.
class ActivityEntryResponse(APIModel):
    id: str
    timestamp: datetime
    category: str
    title: str
    description: str | None
    actor: UserBriefResponse | None
    details: dict[str, Any]


# Alert summary used in alert lists and linked incident views.
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
    # Alert list response with rows and pagination metadata.
    items: list[AlertSummaryResponse]
    meta: ListMetaResponse


# Incident row data shown in the incident list page.
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
    # Incident list response with rows and pagination metadata.
    items: list[IncidentSummaryResponse]
    meta: ListMetaResponse


# Extends incident summary with response actions and audit history.
class IncidentDetailResponse(IncidentSummaryResponse):
    response_actions: list[ResponseActionReferenceResponse]
    audit_logs: list[AuditLogResponse]


# Response action row shown in the responses page.
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
    related_notifications: list[NotificationEventResponse] = Field(default_factory=list)


class ResponseActionListResponse(APIModel):
    # Response action list response with rows and pagination metadata.
    items: list[ResponseActionSummaryResponse]
    meta: ListMetaResponse