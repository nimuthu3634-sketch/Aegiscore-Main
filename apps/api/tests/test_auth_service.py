from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.enums import RoleName
from app.models.role import Role
from app.models.user import User
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.users import UsersRepository
from app.services.auth import authenticate_user
from app.core.security import hash_password


class DummySession:
    def __init__(self) -> None:
        self.did_commit = False

    def commit(self) -> None:
        self.did_commit = True


def build_user() -> User:
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


def test_authenticate_user_returns_token_response(monkeypatch) -> None:
    session = DummySession()
    user = build_user()
    created_logs = []

    monkeypatch.setattr(UsersRepository, "get_by_username", lambda self, username: user)
    monkeypatch.setattr(UsersRepository, "touch_last_login", lambda self, target_user: None)
    monkeypatch.setattr(
        AuditLogsRepository,
        "create",
        lambda self, audit_log: created_logs.append(audit_log),
    )

    response = authenticate_user(session, "admin", "AegisCore123!")

    assert response.user.username == "admin"
    assert response.token_type == "bearer"
    assert response.expires_in > 0
    assert created_logs[0].action == "auth.login"
    assert session.did_commit is True


def test_authenticate_user_raises_for_invalid_credentials(monkeypatch) -> None:
    session = DummySession()
    user = build_user()

    monkeypatch.setattr(UsersRepository, "get_by_username", lambda self, username: user)

    with pytest.raises(HTTPException) as exc_info:
        authenticate_user(session, "admin", "wrong-password")

    assert exc_info.value.status_code == 401
    assert session.did_commit is False

