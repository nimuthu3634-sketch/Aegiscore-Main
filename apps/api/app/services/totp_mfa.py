from __future__ import annotations

# Service logic for setting up and validating TOTP-based multi-factor authentication.

import hashlib
from datetime import timedelta
from uuid import UUID

import jwt
import pyotp
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    JWT_PURPOSE_MFA,
    create_access_token,
    decode_access_token,
)
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.users import UsersRepository
from app.schemas.auth import MfaSetupResponse, TokenResponse
from app.services.serializers import to_user_response

TOTP_ISSUER = "AegisCore"


# Creates the TOTP object used to verify authenticator app codes.
def totp_for_secret(secret: str) -> pyotp.TOTP:
    return pyotp.TOTP(secret, digits=6, interval=30, digest=hashlib.sha1)


# Starts MFA setup by generating a new secret and provisioning URI.
def issue_totp_setup(session: Session, user: User) -> MfaSetupResponse:
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled. Disable it before generating a new secret.",
        )

    # A new secret is generated and later scanned through the authenticator app.
    secret = pyotp.random_base32()
    user.mfa_secret = secret

    AuditLogsRepository(session).create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.mfa.setup",
            details={"username": user.username},
        )
    )
    session.commit()
    session.refresh(user)

    totp = totp_for_secret(secret)
    provisioning_uri = totp.provisioning_uri(name=user.username, issuer_name=TOTP_ISSUER)

    return MfaSetupResponse(secret=secret, provisioning_uri=provisioning_uri)


# Confirms MFA setup after checking the user's authenticator code.
def confirm_totp_setup(session: Session, user: User, code: str) -> None:
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No MFA setup is in progress. Call POST /auth/mfa/setup first.",
        )
    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled for this account.",
        )

    totp = totp_for_secret(user.mfa_secret)
    # valid_window=1 allows a small time difference between server and phone clock.
    if not totp.verify(code.strip(), valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticator code",
        )

    # MFA is only enabled after the first code is verified successfully.
    user.mfa_enabled = True
    AuditLogsRepository(session).create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.mfa.enable",
            details={"username": user.username},
        )
    )
    session.commit()


# Disables MFA and clears the saved secret for the current user.
def disable_totp_for_user(session: Session, user: User) -> None:
    user.mfa_enabled = False
    user.mfa_secret = None
    AuditLogsRepository(session).create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.mfa.disable",
            details={"username": user.username},
        )
    )
    session.commit()


# Validates the MFA challenge and returns the final login token.
def validate_totp_and_issue_token(session: Session, mfa_token: str, code: str) -> TokenResponse:
    settings = get_settings()
    try:
        payload = decode_access_token(mfa_token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        ) from exc

    if payload.get("purpose") != JWT_PURPOSE_MFA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        )

    try:
        user_id = UUID(str(payload.get("sub")))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        ) from exc

    users_repo = UsersRepository(session)
    user = users_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA token",
        )
    if not user.mfa_enabled or not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account",
        )

    totp = totp_for_secret(user.mfa_secret)
    if not totp.verify(code.strip(), valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticator code",
        )

    users_repo.touch_last_login(user)
    audit_repo = AuditLogsRepository(session)
    audit_repo.create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.mfa.validate",
            details={"username": user.username},
        )
    )
    audit_repo.create(
        AuditLog(
            actor=user,
            entity_type="user",
            entity_id=str(user.id),
            action="auth.login",
            details={"username": user.username},
        )
    )
    session.commit()

    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return TokenResponse(
        access_token=create_access_token(str(user.id), expires_delta=expires_delta),
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=to_user_response(user),
    )
