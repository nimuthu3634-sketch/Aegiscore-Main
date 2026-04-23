"""Tests for POST /users user creation endpoint."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.enums import RoleName
from app.models.role import Role
from app.models.user import User
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.roles import RolesRepository
from app.repositories.users import UsersRepository
from app.services.users import create_user
from app.schemas.users import UserCreateRequest
from app.core.security import hash_password


class DummySession:
    """Minimal session stand-in that tracks commit calls."""

    def __init__(self) -> None:
        self.did_commit = False
        self._added: list = []

    def commit(self) -> None:
        self.did_commit = True

    def add(self, instance) -> None:
        self._added.append(instance)


def _build_admin() -> User:
    role = Role(
        id=uuid4(),
        name=RoleName.ADMIN,
        description="Admin role",
        created_at=datetime.now(UTC),
    )
    return User(
        id=uuid4(),
        role=role,
        username="admin",
        password_hash=hash_password("AegisCore123!"),
        full_name="Admin User",
        is_active=True,
        created_at=datetime.now(UTC),
    )


def _analyst_role() -> Role:
    return Role(
        id=uuid4(),
        name=RoleName.ANALYST,
        description="Analyst role",
        created_at=datetime.now(UTC),
    )


# ── Happy path ──────────────────────────────────────────────────────────────


def test_create_user_returns_new_user(monkeypatch) -> None:
    session = DummySession()
    admin = _build_admin()
    analyst_role = _analyst_role()
    created_logs: list = []

    monkeypatch.setattr(UsersRepository, "get_by_username", lambda self, username: None)
    monkeypatch.setattr(RolesRepository, "get_by_name", lambda self, name: analyst_role)
    monkeypatch.setattr(UsersRepository, "create", lambda self, user: _set_defaults(user))
    monkeypatch.setattr(
        AuditLogsRepository,
        "create",
        lambda self, audit_log: created_logs.append(audit_log),
    )

    payload = UserCreateRequest(
        username="new-analyst",
        password="SecurePass123!",
        full_name="New Analyst",
        role=RoleName.ANALYST,
    )

    response = create_user(session, payload, actor=admin)

    assert response.user.username == "new-analyst"
    assert response.user.full_name == "New Analyst"
    assert response.user.is_active is True
    assert response.message == "User 'new-analyst' created successfully."
    assert session.did_commit is True
    assert len(created_logs) == 1
    assert created_logs[0].action == "user.created"


# ── Duplicate username guard ────────────────────────────────────────────────


def test_create_user_rejects_duplicate_username(monkeypatch) -> None:
    session = DummySession()
    admin = _build_admin()
    existing_user = _build_admin()

    monkeypatch.setattr(UsersRepository, "get_by_username", lambda self, username: existing_user)

    payload = UserCreateRequest(
        username="admin-dup",
        password="AnotherPass123!",
        full_name="Duplicate Admin",
        role=RoleName.ADMIN,
    )

    with pytest.raises(HTTPException) as exc_info:
        create_user(session, payload, actor=admin)

    assert exc_info.value.status_code == 409
    assert "already taken" in exc_info.value.detail
    assert session.did_commit is False


# ── Missing role guard ──────────────────────────────────────────────────────


def test_create_user_rejects_missing_role(monkeypatch) -> None:
    session = DummySession()
    admin = _build_admin()

    monkeypatch.setattr(UsersRepository, "get_by_username", lambda self, username: None)
    monkeypatch.setattr(RolesRepository, "get_by_name", lambda self, name: None)

    payload = UserCreateRequest(
        username="ghost-user",
        password="SecurePass123!",
        full_name="Ghost",
        role=RoleName.ANALYST,
    )

    with pytest.raises(HTTPException) as exc_info:
        create_user(session, payload, actor=admin)

    assert exc_info.value.status_code == 400
    assert "does not exist" in exc_info.value.detail
    assert session.did_commit is False


# ── Schema validation ───────────────────────────────────────────────────────


def test_schema_rejects_short_username() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserCreateRequest(
            username="ab",
            password="SecurePass123!",
        )
    assert "at least 3 characters" in str(exc_info.value)


def test_schema_rejects_short_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserCreateRequest(
            username="valid-user",
            password="short",
        )
    assert "at least 8 characters" in str(exc_info.value)


def test_schema_rejects_invalid_username_chars() -> None:
    with pytest.raises(ValidationError) as exc_info:
        UserCreateRequest(
            username="bad user!",
            password="SecurePass123!",
        )
    assert "letters, numbers, hyphens" in str(exc_info.value)


def test_schema_defaults_role_to_analyst() -> None:
    payload = UserCreateRequest(
        username="default-role-user",
        password="SecurePass123!",
    )
    assert payload.role == RoleName.ANALYST


# ── Helpers ─────────────────────────────────────────────────────────────────


def _set_defaults(user: User) -> User:
    """Simulate what the DB would do on insert."""
    if user.id is None:
        user.id = uuid4()
    if user.created_at is None:
        user.created_at = datetime.now(UTC)
    return user