from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.audit_log import AuditLog
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.users import UsersRepository
from app.schemas.auth import TokenResponse
from app.services.serializers import to_user_response


def authenticate_user(
    session: Session,
    username: str,
    password: str,
) -> TokenResponse:
    users_repository = UsersRepository(session)
    user = users_repository.get_by_username(username)

    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    users_repository.touch_last_login(user)
    AuditLogsRepository(session).create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.login",
            details={"username": user.username},
        )
    )
    session.commit()

    settings = get_settings()
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    return TokenResponse(
        access_token=create_access_token(str(user.id), expires_delta=expires_delta),
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=to_user_response(user),
    )

