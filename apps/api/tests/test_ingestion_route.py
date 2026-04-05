import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import deps
from app.api.routes import ingestion as ingestion_route
from app.db.session import get_db_session
from app.main import app
from app.models.enums import (
    AlertStatus,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
)
from app.schemas.common import (
    AlertSummaryResponse,
    AssetSummaryResponse,
    IncidentReferenceResponse,
    RawAlertSummaryResponse,
)
from app.schemas.ingestion import IngestionResultResponse


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: object()
    app.dependency_overrides[get_db_session] = lambda: None


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def _fixture_payload(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _sample_result(source: str, detection_type: DetectionType) -> IngestionResultResponse:
    now = datetime.now(UTC)
    alert_id = uuid4()
    incident_id = uuid4()
    return IngestionResultResponse(
        source=source,
        external_id=f"{source}-fixture-1",
        status="ingested",
        alert=AlertSummaryResponse(
            id=alert_id,
            source=source,
            source_type=source.title(),
            title="Fixture alert",
            description="Fixture alert created through ingestion.",
            detection_type=detection_type,
            severity=9,
            severity_label="critical",
            status=AlertStatus.NEW,
            status_label="new",
            normalized_payload={"source_ip": "203.0.113.8"},
            created_at=now,
            asset=AssetSummaryResponse(
                id=uuid4(),
                hostname="fixture-asset-01",
                ip_address="10.20.1.15",
                operating_system="Ubuntu 22.04",
                criticality="high",
                created_at=now,
                updated_at=now,
            ),
            asset_name="fixture-asset-01",
            raw_alert=RawAlertSummaryResponse(
                id=uuid4(),
                source=source,
                external_id=f"{source}-fixture-1",
                detection_type=detection_type,
                severity=9,
                raw_payload={"source": source},
                received_at=now,
            ),
            event_id=f"{source}-fixture-1",
            source_ip="203.0.113.8",
            destination_ip="10.20.1.15",
            destination_port=22,
            username="svc-admin",
            risk_score=None,
            risk_score_value=94,
            incident=IncidentReferenceResponse(
                id=incident_id,
                title="Fixture incident",
                status=IncidentStatus.TRIAGED,
                priority=IncidentPriority.CRITICAL,
                created_at=now,
                updated_at=now,
            ),
        ),
        linked_incident=IncidentReferenceResponse(
            id=incident_id,
            title="Fixture incident",
            status=IncidentStatus.TRIAGED,
            priority=IncidentPriority.CRITICAL,
            created_at=now,
            updated_at=now,
        ),
        responses_created=1,
        warnings=[],
    )


def test_wazuh_ingestion_route_accepts_fixture_payload(monkeypatch) -> None:
    payload = _fixture_payload("wazuh_brute_force.json")
    result = _sample_result("wazuh", DetectionType.BRUTE_FORCE)
    _override_dependencies()
    monkeypatch.setattr(
        ingestion_route,
        "ingest_wazuh_event",
        lambda db, body, actor=None: result,
    )

    try:
        client = TestClient(app)
        response = client.post("/integrations/wazuh/events", json=payload)
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["source"] == "wazuh"
    assert response.json()["alert"]["detection_type"] == "brute_force"


def test_suricata_ingestion_route_returns_validation_error(monkeypatch) -> None:
    payload = _fixture_payload("suricata_unsupported_detection.json")
    _override_dependencies()

    def raise_invalid(db, body, actor=None):
        raise HTTPException(status_code=422, detail="Suricata payload did not match the supported AegisCore detection scope.")

    monkeypatch.setattr(ingestion_route, "ingest_suricata_event", raise_invalid)

    try:
        client = TestClient(app)
        response = client.post("/integrations/suricata/events", json=payload)
    finally:
        _clear_overrides()

    assert response.status_code == 422
    assert "supported AegisCore detection scope" in response.json()["detail"]
