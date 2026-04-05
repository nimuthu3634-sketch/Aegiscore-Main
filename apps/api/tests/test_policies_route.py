from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import policies as policies_route
from app.db.session import get_db_session
from app.main import app
from app.models.enums import (
    DetectionType,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
)
from app.schemas.policies import (
    ResponsePolicyListResponse,
    ResponsePolicySummaryResponse,
    ResponsePolicyUpdateResponse,
)


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _sample_policy() -> ResponsePolicySummaryResponse:
    now = datetime.now(UTC)
    return ResponsePolicySummaryResponse(
        id=uuid4(),
        name="Dry-run brute-force IP containment",
        description="Block hostile IPs only in dry-run during development.",
        enabled=True,
        target=ResponsePolicyTarget.ALERT,
        detection_type=DetectionType.BRUTE_FORCE,
        min_risk_score=85,
        action_type=ResponseActionType.BLOCK_IP,
        mode=ResponseMode.DRY_RUN,
        config={"source": "seed"},
        created_at=now,
        updated_at=now,
    )


def test_policies_route_returns_policy_list(monkeypatch) -> None:
    policy = _sample_policy()
    _override_dependencies()
    monkeypatch.setattr(
        policies_route,
        "list_policies",
        lambda db: ResponsePolicyListResponse(items=[policy]),
    )

    try:
        client = TestClient(app)
        response = client.get("/policies")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["name"] == policy.name
    assert payload["items"][0]["action_type"] == "block_ip"


def test_policies_route_updates_enabled_flag(monkeypatch) -> None:
    policy = _sample_policy()
    policy.enabled = False
    _override_dependencies()
    monkeypatch.setattr(
        policies_route,
        "update_policy_enabled",
        lambda db, policy_id, enabled: ResponsePolicyUpdateResponse(
            policy=policy,
            message="Policy disabled successfully.",
        ),
    )

    try:
        client = TestClient(app)
        response = client.patch(f"/policies/{policy.id}", json={"enabled": False})
    finally:
        _clear_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["policy"]["enabled"] is False
    assert payload["message"] == "Policy disabled successfully."


def test_policies_route_returns_not_found(monkeypatch) -> None:
    _override_dependencies()

    def raise_not_found(db, policy_id, enabled):
        raise HTTPException(status_code=404, detail="Policy not found")

    monkeypatch.setattr(policies_route, "update_policy_enabled", raise_not_found)

    try:
        client = TestClient(app)
        response = client.patch(f"/policies/{uuid4()}", json={"enabled": True})
    finally:
        _clear_overrides()

    assert response.status_code == 404
    assert response.json() == {"detail": "Policy not found"}
