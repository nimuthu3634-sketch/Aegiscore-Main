"""API routes for user management.

This route file is mainly used by the admin to create new SOC operator accounts.
"""

from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession
from app.schemas.users import UserCreateRequest, UserCreateResponse
from app.services.users import create_user


# Groups all user-related endpoints under /users.
router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserCreateResponse, status_code=201)
def create_user_route(
    payload: UserCreateRequest,
    current_user: AdminUser,  # type: ignore[valid-type]
    db: DbSession,  # type: ignore[valid-type]
) -> UserCreateResponse:
    """Create a new SOC operator account.

    This endpoint is restricted to admin users only. It accepts the new user's
    username, password, optional full name, and assigned role.
    """

    # Passes the request data to the service layer where the user is created.
    return create_user(db, payload, actor=current_user)