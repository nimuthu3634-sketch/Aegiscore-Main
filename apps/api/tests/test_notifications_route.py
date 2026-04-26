from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import notifications as notifications_route
from app.db.session import get_db_session
from app.main import app
from app.repositories.notification_events import NotificationBellRow

USER_ID = uuid4()
NOTIFICATION_ID = uuid4()
INCIDENT_ID = uuid4()


class FakeSession:
    def commit(self) -> None:
        return None


def _override_dependencies(*, with_session: bool = False) -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(id=USER_ID)
    if with_session:
        app.dependency_overrides[get_db_session] = lambda: FakeSession()
    else:
        app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _sample_row(*, read: bool = False) -> NotificationBellRow:
    return NotificationBellRow(
        id=NOTIFICATION_ID,
        incident_id=INCIDENT_ID,
        incident_title="Brute-force spike",
        trigger_type="risk_threshold",
        trigger_value="85",
        subject="Incident crossed risk threshold",
        status="sent",
        created_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        read=read,
    )


def test_notifications_recent_returns_payload(monkeypatch) -> None:
    _override_dependencies()

    class FakeRepo:
        def __init__(self, _db: object) -> None:
            pass

        def list_recent(self, *, limit: int, unread_only: bool) -> list[NotificationBellRow]:
            assert limit == 10
            assert unread_only is True
            return [_sample_row()]

        def count_unread(self) -> int:
            return 4

        def count_matching(self, *, unread_only: bool) -> int:
            assert unread_only is True
            return 12

    monkeypatch.setattr(notifications_route, "NotificationEventsRepository", FakeRepo)

    try:
        client = TestClient(app)
        response = client.get("/notifications/recent", params={"limit": 10, "unread_only": "true"})
    finally:
        _clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["unread_count"] == 4
    assert body["total"] == 12
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["id"] == str(NOTIFICATION_ID)
    assert item["incident_id"] == str(INCIDENT_ID)
    assert item["incident_title"] == "Brute-force spike"
    assert item["trigger_type"] == "risk_threshold"
    assert item["read"] is False


def test_notifications_mark_read_returns_204(monkeypatch) -> None:
    _override_dependencies(with_session=True)
    captured: dict[str, object] = {}

    class FakeRepo:
        def __init__(self, _db: object) -> None:
            pass

        def mark_read(self, notification_id, user_id) -> bool:  # noqa: ANN001
            captured["nid"] = notification_id
            captured["uid"] = user_id
            return True

    monkeypatch.setattr(notifications_route, "NotificationEventsRepository", FakeRepo)

    try:
        client = TestClient(app)
        response = client.post(f"/notifications/{NOTIFICATION_ID}/read")
    finally:
        _clear_overrides()

    assert response.status_code == 204
    assert captured["nid"] == NOTIFICATION_ID
    assert captured["uid"] == USER_ID


def test_notifications_mark_read_missing_returns_404(monkeypatch) -> None:
    _override_dependencies(with_session=True)

    class FakeRepo:
        def __init__(self, _db: object) -> None:
            pass

        def mark_read(self, notification_id, user_id) -> bool:  # noqa: ANN001
            return False

    monkeypatch.setattr(notifications_route, "NotificationEventsRepository", FakeRepo)

    try:
        client = TestClient(app)
        response = client.post(f"/notifications/{uuid4()}/read")
    finally:
        _clear_overrides()

    assert response.status_code == 404


def test_notifications_read_all_returns_204(monkeypatch) -> None:
    _override_dependencies(with_session=True)
    captured: dict[str, object] = {}

    class FakeRepo:
        def __init__(self, _db: object) -> None:
            pass

        def mark_all_read(self, user_id) -> int:  # noqa: ANN001
            captured["uid"] = user_id
            return 5

    monkeypatch.setattr(notifications_route, "NotificationEventsRepository", FakeRepo)

    try:
        client = TestClient(app)
        response = client.post("/notifications/read-all")
    finally:
        _clear_overrides()

    assert response.status_code == 204
    assert captured["uid"] == USER_ID
