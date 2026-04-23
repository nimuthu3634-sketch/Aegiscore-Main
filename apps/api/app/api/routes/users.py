"""API routes for user management (admin-only)."""

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.users import UserCreateRequest, UserCreateResponse
from app.services.users import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserCreateResponse, status_code=201)
def create_user_route(
    payload: UserCreateRequest,
    current_user: AdminUser,  # type: ignore[valid-type]
    db: DbSession,  # type: ignore[valid-type]
) -> UserCreateResponse:
    """Create a new SOC operator account.

    Restricted to admin users. Accepts a username, password,
    optional full name, and role assignment (defaults to analyst).
    """
    return create_user(db, payload, actor=current_user)