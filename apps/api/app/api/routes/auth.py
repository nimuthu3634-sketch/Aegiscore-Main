from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MfaSetupResponse,
    MfaValidateRequest,
    MfaVerifyRequest,
    TokenResponse,
)
from app.schemas.common import UserResponse
from app.services.auth import authenticate_user
from app.services.serializers import to_user_response
from app.services.totp_mfa import (
    confirm_totp_setup,
    disable_totp_for_user,
    issue_totp_setup,
    validate_totp_and_issue_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: DbSession) -> LoginResponse:
    return authenticate_user(db, payload.username, payload.password)


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> UserResponse:
    return to_user_response(current_user)


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(db: DbSession, current_user: CurrentUser) -> MfaSetupResponse:
    return issue_totp_setup(db, current_user)


@router.post("/mfa/verify-setup", status_code=204)
def mfa_verify_setup(
    payload: MfaVerifyRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    confirm_totp_setup(db, current_user, payload.code)


@router.post("/mfa/disable", status_code=204)
def mfa_disable(db: DbSession, current_user: AdminUser) -> None:
    disable_totp_for_user(db, current_user)


@router.post("/mfa/validate", response_model=TokenResponse)
def mfa_validate(payload: MfaValidateRequest, db: DbSession) -> TokenResponse:
    return validate_totp_and_issue_token(db, payload.mfa_token, payload.code)

