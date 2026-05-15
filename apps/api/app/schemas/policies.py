from datetime import datetime
from uuid import UUID

from app.models.enums import (
    DetectionType,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
)
from app.schemas.base import APIModel


# Summary details of one automated response policy.
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


# Response returned when listing all response policies.
class ResponsePolicyListResponse(APIModel):
    items: list[ResponsePolicySummaryResponse]


# Request body used when enabling or disabling a policy.
class ResponsePolicyUpdateRequest(APIModel):
    enabled: bool


# Response returned after a policy is updated.
class ResponsePolicyUpdateResponse(APIModel):
    policy: ResponsePolicySummaryResponse
    message: str