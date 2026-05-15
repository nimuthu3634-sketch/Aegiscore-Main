"""Schemas for user management endpoints."""

import re

from pydantic import Field, field_validator

from app.models.enums import RoleName
from app.schemas.base import APIModel
from app.schemas.common import UserResponse


class UserCreateRequest(APIModel):
    """Request body used when an admin creates a new SOC operator account."""

    username: str
    password: str
    full_name: str | None = None

    # New users are created as analysts by default unless another role is selected.
    role: RoleName = Field(default=RoleName.ANALYST)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        # Cleans and validates the username before saving it.
        value = value.strip()

        if len(value) < 3:
            raise ValueError("Username must be at least 3 characters.")
        if len(value) > 50:
            raise ValueError("Username must be at most 50 characters.")
        if not re.fullmatch(r"[a-zA-Z0-9_\-]+", value):
            raise ValueError(
                "Username may only contain letters, numbers, hyphens, and underscores."
            )

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        # Basic password length validation for newly created users.
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(value) > 128:
            raise ValueError("Password must be at most 128 characters.")

        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        # Keeps the full name within the database column limit.
        if value is not None and len(value) > 255:
            raise ValueError("Full name must be at most 255 characters.")

        return value


class UserCreateResponse(APIModel):
    """Response returned after the new user account is created."""

    user: UserResponse
    message: str