from app.services.health import get_health_payload
from app.services import health as health_service


def test_health_payload_is_ok_when_database_is_available(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "up")

    payload = get_health_payload()

    assert payload.status == "ok"
    assert payload.database == "up"


def test_health_payload_is_degraded_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "down")

    payload = get_health_payload()

    assert payload.status == "degraded"
    assert payload.database == "down"
