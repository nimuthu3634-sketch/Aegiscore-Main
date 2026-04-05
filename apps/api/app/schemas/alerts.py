from datetime import datetime
from typing import Any
from uuid import UUID

from app.models.enums import AlertStatus, DetectionType, IncidentPriority, IncidentStatus
from app.schemas.base import APIModel
from app.schemas.common import (
    ActivityEntryResponse,
    AnalystNoteResponse,
    AssetSummaryResponse,
    ResponseActionDetailResponse,
    UserBriefResponse,
)
from app.schemas.listing import AlertSeverityLabel


class AlertLinkedIncidentResponse(APIModel):
    id: UUID
    title: str
    status: IncidentStatus
    priority: IncidentPriority
    created_at: datetime
    updated_at: datetime
    assigned_user: UserBriefResponse | None


class AlertSourceRuleResponse(APIModel):
    rule_id: str | None
    name: str | None
    provider: str | None
    metadata: dict[str, Any]


class AlertScoreExplanationResponse(APIModel):
    label: str
    summary: str
    rationale: str
    factors: list[str]
    confidence: float | None


class AlertDetailResponse(APIModel):
    id: UUID
    title: str
    description: str | None
    detection_type: DetectionType
    source_type: str
    severity: AlertSeverityLabel
    severity_score: int
    status: AlertStatus
    risk_score: int | None
    risk_confidence: float | None
    priority_label: AlertSeverityLabel | None
    linked_incident: AlertLinkedIncidentResponse | None
    asset: AssetSummaryResponse | None
    source_ip: str | None
    destination_ip: str | None
    destination_port: int | None
    username: str | None
    timestamp: datetime
    source_rule: AlertSourceRuleResponse | None
    normalized_details: dict[str, Any]
    raw_payload: dict[str, Any]
    score_explanation: AlertScoreExplanationResponse | None
    related_responses: list[ResponseActionDetailResponse]
    analyst_notes: list[AnalystNoteResponse]
    audit_history: list[ActivityEntryResponse]
