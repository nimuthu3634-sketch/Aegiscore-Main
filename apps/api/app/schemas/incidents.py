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


class IncidentLinkedAlertResponse(APIModel):
    id: UUID
    title: str
    detection_type: DetectionType
    source_type: str
    severity: AlertSeverityLabel
    status: AlertStatus
    risk_score: int | None
    timestamp: datetime
    asset_hostname: str | None
    source_ip: str | None
    destination_ip: str | None
    destination_port: int | None
    username: str | None


class IncidentGroupedEvidenceResponse(APIModel):
    summary: str
    evidence_items: list[str]
    correlation_keys: dict[str, Any]


class IncidentPriorityExplanationResponse(APIModel):
    label: str
    summary: str
    rationale: str
    factors: list[str]


class IncidentStateTransitionCapabilitiesResponse(APIModel):
    current_state: IncidentStatus
    available_actions: list[str]
    allowed_target_states: list[IncidentStatus]


class IncidentDetailResponse(APIModel):
    id: UUID
    title: str
    summary: str | None
    priority: IncidentPriority
    state: IncidentStatus
    assignee: UserBriefResponse | None
    created_at: datetime
    updated_at: datetime
    primary_asset: AssetSummaryResponse | None
    affected_assets: list[AssetSummaryResponse]
    linked_alerts: list[IncidentLinkedAlertResponse]
    grouped_evidence: IncidentGroupedEvidenceResponse
    response_history: list[ResponseActionDetailResponse]
    analyst_notes: list[AnalystNoteResponse]
    timeline: list[ActivityEntryResponse]
    priority_explanation: IncidentPriorityExplanationResponse
    state_transition_capabilities: IncidentStateTransitionCapabilitiesResponse
