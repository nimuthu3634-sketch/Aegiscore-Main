import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
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
    RoleName,
)
from app.schemas.common import (
    AlertSummaryResponse,
    AssetSummaryResponse,
    IncidentReferenceResponse,
    RawAlertSummaryResponse,
)
from app.schemas.ingestion import (
    IngestionResultResponse,
    SuricataConnectorStatusResponse,
    WazuhConnectorStatusResponse,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


def _override_dependencies() -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(
        username="admin",
        role=SimpleNamespace(name=RoleName.ADMIN),
    )
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


def test_wazuh_connector_status_route_returns_connector_health(monkeypatch) -> None:
    _override_dependencies()
    monkeypatch.setattr(
        ingestion_route,
        "get_wazuh_connector_status",
        lambda db: WazuhConnectorStatusResponse(
            connector="wazuh_live_connector",
            enabled=True,
            status="healthy",
            last_success_at=datetime(2026, 4, 6, 12, 30, tzinfo=UTC),
            last_error_at=None,
            last_error_message=None,
            last_checkpoint_timestamp="2026-04-06T12:29:00+00:00",
            checkpoint_external_ids=["evt-1", "evt-2"],
            metrics={
                "poll_count": 5,
                "total_fetched": 80,
                "total_ingested": 73,
                "total_duplicates": 6,
                "total_failed": 1,
            },
        ),
    )

    try:
        client = TestClient(app)
        response = client.get("/integrations/wazuh/connector/status")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["connector"] == "wazuh_live_connector"
    assert response.json()["status"] == "healthy"


def test_suricata_connector_status_route_returns_connector_health(monkeypatch) -> None:
    _override_dependencies()
    monkeypatch.setattr(
        ingestion_route,
        "get_suricata_connector_status",
        lambda db: SuricataConnectorStatusResponse(
            connector="suricata_live_connector",
            enabled=True,
            mode="file_tail",
            source_path="/var/log/suricata/eve.json",
            status="healthy",
            last_success_at=datetime(2026, 4, 6, 12, 30, tzinfo=UTC),
            last_error_at=None,
            last_error_message=None,
            checkpoint_offset=9124,
            checkpoint_inode=77512,
            metrics={
                "poll_count": 6,
                "total_fetched": 140,
                "total_ingested": 130,
                "total_duplicates": 7,
                "total_failed": 3,
            },
        ),
    )

    try:
        client = TestClient(app)
        response = client.get("/integrations/suricata/connector/status")
    finally:
        _clear_overrides()

    assert response.status_code == 200
    assert response.json()["connector"] == "suricata_live_connector"
    assert response.json()["mode"] == "file_tail"


def test_ingestion_routes_reject_analyst_role() -> None:
    payload = _fixture_payload("wazuh_brute_force.json")
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(
        username="analyst",
        role=SimpleNamespace(name=RoleName.ANALYST),
    )
    app.dependency_overrides[get_db_session] = lambda: None

    try:
        client = TestClient(app)
        response = client.post("/integrations/wazuh/events", json=payload)
    finally:
        _clear_overrides()

    assert response.status_code == 403
    assert "Insufficient role permissions" in response.json()["detail"]


def test_connector_status_routes_allow_analyst_role(monkeypatch) -> None:
    app.dependency_overrides[deps.get_current_user] = lambda: SimpleNamespace(
        username="analyst",
        role=SimpleNamespace(name=RoleName.ANALYST),
    )
    app.dependency_overrides[get_db_session] = lambda: None
    monkeypatch.setattr(
        ingestion_route,
        "get_wazuh_connector_status",
        lambda db: WazuhConnectorStatusResponse(
            connector="wazuh_live_connector",
            enabled=True,
            status="healthy",
            last_success_at=None,
            last_error_at=None,
            last_error_message=None,
            last_checkpoint_timestamp=None,
            checkpoint_external_ids=[],
            metrics={"poll_count": 0, "total_fetched": 0, "total_ingested": 0},
        ),
    )
    monkeypatch.setattr(
        ingestion_route,
        "get_suricata_connector_status",
        lambda db: SuricataConnectorStatusResponse(
            connector="suricata_live_connector",
            enabled=True,
            mode="file_tail",
            source_path="/var/log/suricata/eve.json",
            status="healthy",
            last_success_at=None,
            last_error_at=None,
            last_error_message=None,
            checkpoint_offset=0,
            checkpoint_inode=0,
            metrics={"poll_count": 0, "total_fetched": 0, "total_ingested": 0},
        ),
    )

    try:
        client = TestClient(app)
        wazuh_response = client.get("/integrations/wazuh/connector/status")
        suricata_response = client.get("/integrations/suricata/connector/status")
    finally:
        _clear_overrides()

    assert wazuh_response.status_code == 200
    assert suricata_response.status_code == 200
