from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import auth as auth_route
from app.main import app
from app.models.enums import RoleName
from app.schemas.auth import TokenResponse
from app.schemas.common import RoleResponse, UserResponse


def test_login_route_returns_token_payload(monkeypatch) -> None:
    expected = TokenResponse(
        access_token="token-123",
        token_type="bearer",
        expires_in=3600,
        user=UserResponse(
            id=uuid4(),
            username="admin",
            full_name="AegisCore Administrator",
            is_active=True,
            mfa_enabled=False,
            last_login_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            role=RoleResponse(id=uuid4(), name=RoleName.ADMIN),
        ),
    )

    monkeypatch.setattr(
        auth_route,
        "authenticate_user",
        lambda db, username, password: expected,
    )

    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "AegisCore123!"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "token-123"
    assert response.json()["user"]["role"]["name"] == "admin"
