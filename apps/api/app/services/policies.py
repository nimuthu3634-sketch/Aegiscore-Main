from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.response_policy import ResponsePolicy
from app.repositories.policies import PoliciesRepository
from app.schemas.policies import (
    ResponsePolicyListResponse,
    ResponsePolicySummaryResponse,
    ResponsePolicyUpdateResponse,
)


def _to_policy_response(policy: ResponsePolicy) -> ResponsePolicySummaryResponse:
    return ResponsePolicySummaryResponse(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        enabled=policy.enabled,
        target=policy.target,
        detection_type=policy.detection_type,
        min_risk_score=policy.min_risk_score,
        action_type=policy.action_type,
        mode=policy.mode,
        config=policy.config,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


def list_policies(session: Session) -> ResponsePolicyListResponse:
    policies = PoliciesRepository(session).list_policies()
    return ResponsePolicyListResponse(
        items=[_to_policy_response(policy) for policy in policies]
    )


def update_policy_enabled(
    session: Session,
    policy_id: UUID,
    *,
    enabled: bool,
) -> ResponsePolicyUpdateResponse:
    repository = PoliciesRepository(session)
    policy = repository.get_policy(policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    policy.enabled = enabled
    session.commit()
    session.refresh(policy)
    return ResponsePolicyUpdateResponse(
        policy=_to_policy_response(policy),
        message=(
            f"Policy {'enabled' if enabled else 'disabled'} successfully."
        ),
    )
