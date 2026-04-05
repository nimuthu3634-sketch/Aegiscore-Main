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

