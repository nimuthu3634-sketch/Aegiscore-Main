from fastapi.testclient import TestClient

from app.main import app
from app.services import health as health_service


def test_health_route_reports_api_status(monkeypatch) -> None:
    monkeypatch.setattr(health_service, "get_database_status", lambda: "up")

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "aegiscore-api",
        "database": "up",
    }


def test_health_live_route_reports_liveness() -> None:
    client = TestClient(app)
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "aegiscore-api"


def test_health_ready_route_reports_readiness(monkeypatch) -> None:
    monkeypatch.setattr(
        health_service,
        "get_readiness_payload",
        lambda: health_service.ReadinessResponse(
            status="ready",
            service="aegiscore-api",
            database="up",
            dependencies={
                "wazuh_connector": health_service.DependencyStatusResponse(
                    enabled=False,
                    status="disabled",
                    detail=None,
                ),
                "suricata_connector": health_service.DependencyStatusResponse(
                    enabled=False,
                    status="disabled",
                    detail=None,
                ),
            },
        ),
    )
    client = TestClient(app)
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["dependencies"]["wazuh_connector"]["status"] == "disabled"

