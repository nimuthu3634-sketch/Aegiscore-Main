from datetime import datetime
from uuid import UUID

from app.models.enums import (
    DetectionType,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
)
from app.schemas.base import APIModel


class ResponsePolicySummaryResponse(APIModel):
    id: UUID
    name: str
    description: str | None
    enabled: bool
    target: ResponsePolicyTarget
    detection_type: DetectionType
    min_risk_score: int
    action_type: ResponseActionType
    mode: ResponseMode
    config: dict
    created_at: datetime
    updated_at: datetime


class ResponsePolicyListResponse(APIModel):
    items: list[ResponsePolicySummaryResponse]


class ResponsePolicyUpdateRequest(APIModel):
    enabled: bool


class ResponsePolicyUpdateResponse(APIModel):
    policy: ResponsePolicySummaryResponse
    message: str
