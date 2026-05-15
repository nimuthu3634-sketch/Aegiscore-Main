# AegisCore student note: Security helpers for password hashing, JWT tokens, and MFA challenge tokens.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

JWT_PURPOSE_MFA = "mfa"
MFA_TOKEN_EXPIRE_MINUTES = 5

password_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# Handles the hash password logic.
def hash_password(password: str) -> str:
    return password_context.hash(password)


# Checks a plain password against the stored password hash.
def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


# Creates a JWT access token after successful authentication.
def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expiration = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


# Creates a short-lived token used during MFA login.
def create_mfa_challenge_token(subject: str) -> str:
    settings = get_settings()
    expiration = datetime.now(UTC) + timedelta(minutes=MFA_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expiration,
        "purpose": JWT_PURPOSE_MFA,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


# Handles the decode access token logic.
def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# Decodes and validates a bearer access token.
def decode_bearer_access_token(token: str) -> dict[str, Any]:
    """Decode a JWT intended for API access; reject short-lived MFA challenge tokens."""
    payload = decode_access_token(token)
    if payload.get("purpose") == JWT_PURPOSE_MFA:
        raise jwt.InvalidTokenError("Token is not a valid access token")
    return payload
