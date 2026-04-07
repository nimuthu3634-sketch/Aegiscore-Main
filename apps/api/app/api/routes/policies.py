from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.policies import (
    ResponsePolicyListResponse,
    ResponsePolicyUpdateRequest,
    ResponsePolicyUpdateResponse,
)
from app.services.policies import list_policies, update_policy_enabled

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=ResponsePolicyListResponse)
def read_policies(_: CurrentUser, db: DbSession) -> ResponsePolicyListResponse:
    return list_policies(db)


@router.patch("/{policy_id}", response_model=ResponsePolicyUpdateResponse)
def update_policy_route(
    policy_id: UUID,
    payload: ResponsePolicyUpdateRequest,
    _: AdminUser,
    db: DbSession,
) -> ResponsePolicyUpdateResponse:
    return update_policy_enabled(db, policy_id, enabled=payload.enabled)
