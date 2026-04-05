from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.common import UserResponse
from app.services.auth import authenticate_user
from app.services.serializers import to_user_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    return authenticate_user(db, payload.username, payload.password)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> UserResponse:
    return to_user_response(current_user)

