# This test file checks health service checks such as database and connector status.

from app.services.health import get_health_payload
from app.services import health as health_service


# Checks health payload is ok when database is available.
def test_health_payload_is_ok_when_database_is_available(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "up")

    payload = get_health_payload()

    assert payload.status == "ok"
    assert payload.database == "up"


# Checks health payload is degraded when database is unavailable.
def test_health_payload_is_degraded_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "down")

    payload = get_health_payload()

    assert payload.status == "degraded"
    assert payload.database == "down"


# Checks readiness payload is ready when database is available.
def test_readiness_payload_is_ready_when_database_is_available(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "up")
    monkeypatch.setattr(
        health_service,
        "_integration_dependency_status",
        lambda connector, enabled: health_service.DependencyStatusResponse(
            enabled=enabled,
            status="disabled" if not enabled else "healthy",
            detail=None,
        ),
    )
    monkeypatch.setattr(
        health_service,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "wazuh_connector_enabled": False,
                "suricata_connector_enabled": False,
            },
        )(),
    )

    payload = health_service.get_readiness_payload()

    assert payload.status == "ready"
    assert payload.database == "up"
    assert payload.dependencies["wazuh_connector"].status == "disabled"


# Checks readiness payload is not ready when database is down.
def test_readiness_payload_is_not_ready_when_database_is_down(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "down")
    monkeypatch.setattr(
        health_service,
        "_integration_dependency_status",
        lambda connector, enabled: health_service.DependencyStatusResponse(
            enabled=enabled,
            status="disabled",
            detail=None,
        ),
    )
    monkeypatch.setattr(
        health_service,
        "get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "wazuh_connector_enabled": False,
                "suricata_connector_enabled": False,
            },
        )(),
    )

    payload = health_service.get_readiness_payload()

    assert payload.status == "not_ready"
    assert payload.database == "down"
