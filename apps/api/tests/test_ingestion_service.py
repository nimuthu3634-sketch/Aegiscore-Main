import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.asset import Asset
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    IncidentStatus,
    ResponseMode,
    ResponseStatus,
    ScoreMethod,
)
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.role import Role
from app.models.user import User
from app.services.ingestion.parsers import parse_suricata_event, parse_wazuh_event
from app.services.ingestion.service import (
    _resolve_or_create_asset,
    ingest_suricata_event,
    ingest_wazuh_event,
)
from app.services.ingestion.types import IngestionParseError
from app.services.ingestion.types import ParsedSecurityEvent


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.flushed = 0
        self.rollbacks = 0
        self.raise_integrity_error_on_flush = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1

    def flush(self) -> None:
        self.flushed += 1
        if self.raise_integrity_error_on_flush:
            self.raise_integrity_error_on_flush = False
            raise IntegrityError("INSERT", {}, Exception("duplicate asset"))

    def rollback(self) -> None:
        self.rollbacks += 1


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("fixture_name", "parser", "expected_detection", "field_name", "expected_value"),
    [
        (
            "wazuh_brute_force.json",
            parse_wazuh_event,
            DetectionType.BRUTE_FORCE,
            "failed_attempts",
            24,
        ),
        (
            "wazuh_file_integrity_violation.json",
            parse_wazuh_event,
            DetectionType.FILE_INTEGRITY_VIOLATION,
            "file_path",
            "D:\\Operations\\Policies\\access-control.xlsx",
        ),
        (
            "suricata_port_scan.json",
            parse_suricata_event,
            DetectionType.PORT_SCAN,
            "destination_port",
            3389,
        ),
        (
            "wazuh_unauthorized_user_creation.json",
            parse_wazuh_event,
            DetectionType.UNAUTHORIZED_USER_CREATION,
            "username",
            "unknown-admin",
        ),
    ],
)
def test_supported_fixture_scenarios_parse_expected_identity_and_key_field(
    fixture_name: str,
    parser,
    expected_detection: DetectionType,
    field_name: str,
    expected_value: object,
) -> None:
    parsed = parser(_fixture(fixture_name))

    assert parsed.detection_type == expected_detection
    assert parsed.normalized_payload[field_name] == expected_value


def test_parse_wazuh_supported_detections_from_fixtures() -> None:
    brute_force = parse_wazuh_event(_fixture("wazuh_brute_force.json"))
    file_integrity = parse_wazuh_event(_fixture("wazuh_file_integrity_violation.json"))
    user_creation = parse_wazuh_event(_fixture("wazuh_unauthorized_user_creation.json"))

    assert brute_force.detection_type == DetectionType.BRUTE_FORCE
    assert brute_force.normalized_payload["failed_attempts"] == 24
    assert file_integrity.detection_type == DetectionType.FILE_INTEGRITY_VIOLATION
    assert "file_path" in file_integrity.normalized_payload
    assert user_creation.detection_type == DetectionType.UNAUTHORIZED_USER_CREATION
    assert user_creation.normalized_payload["username"] == "unknown-admin"


def test_parse_suricata_port_scan_fixture() -> None:
    parsed = parse_suricata_event(_fixture("suricata_port_scan.json"))

    assert parsed.detection_type == DetectionType.PORT_SCAN
    assert parsed.normalized_payload["source_ip"] == "198.51.100.55"
    assert parsed.normalized_payload["destination_port"] == 3389


def test_parse_suricata_rejects_unsupported_detection_fixture() -> None:
    with pytest.raises(IngestionParseError) as exc_info:
        parse_suricata_event(_fixture("suricata_unsupported_detection.json"))

    assert exc_info.value.error_type == "unsupported_detection"


def test_ingest_wazuh_event_persists_and_returns_scored_alert(monkeypatch) -> None:
    session = FakeSession()
    actor = User(
        id=uuid4(),
        role=Role(id=uuid4(), name="admin"),
        username="admin",
        password_hash="hashed",
        full_name="AegisCore Admin",
        is_active=True,
    )
    payload = _fixture("wazuh_brute_force.json")
    created_asset = Asset(
        id=uuid4(),
        hostname="edge-auth-01",
        ip_address="10.42.0.21",
        operating_system="Ubuntu 22.04",
        criticality=AssetCriticality.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "app.services.ingestion.service.AlertsRepository.get_raw_alert_by_source_external_id",
        lambda self, source, external_id: None,
    )
    monkeypatch.setattr(
        "app.services.ingestion.service._resolve_or_create_asset",
        lambda ingest_session, parsed_event: (created_asset, []),
    )
    monkeypatch.setattr(
        "app.services.ingestion.service.IngestionFailuresRepository.resolve_failure",
        lambda self, source, external_id: None,
    )
    monkeypatch.setattr(
        "app.services.ingestion.service.AuditLogsRepository.create",
        lambda self, audit_log: audit_log,
    )

    def fake_persist_and_score_alert(fake_session, raw_alert, normalized_alert):
        raw_alert.id = uuid4()
        normalized_alert.id = uuid4()
        raw_alert.normalized_alert = normalized_alert
        normalized_alert.raw_alert = raw_alert
        normalized_alert.asset = created_asset
        normalized_alert.risk_score = RiskScore(
            id=uuid4(),
            normalized_alert=normalized_alert,
            score=97,
            confidence=0.94,
            priority_label=IncidentPriority.CRITICAL,
            scoring_method=ScoreMethod.BASELINE_RULES,
            reasoning="Fixture scoring applied after ingestion.",
            explanation={"summary": "Fixture scoring summary."},
            feature_snapshot={"source_ip": "203.0.113.88"},
            calculated_at=datetime.now(UTC),
        )
        incident = Incident(
            id=uuid4(),
            title="Automated response context",
            summary="Created during fixture ingestion scoring.",
            status=IncidentStatus.TRIAGED,
            priority=IncidentPriority.CRITICAL,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        response_action = ResponseAction(
            id=uuid4(),
            incident=incident,
            normalized_alert=normalized_alert,
            action_type="block_ip",
            status=ResponseStatus.WARNING,
            mode=ResponseMode.DRY_RUN,
            target_value="203.0.113.88",
            result_summary="Dry-run completed.",
            result_message="Would block hostile source IP.",
            attempt_count=1,
            details={"summary": "Dry-run completed."},
            created_at=datetime.now(UTC),
            executed_at=datetime.now(UTC),
        )
        normalized_alert.incident = incident
        incident.primary_alert = normalized_alert
        incident.alerts = [normalized_alert]
        incident.response_actions = [response_action]
        normalized_alert.response_actions = [response_action]
        captured["raw_alert"] = raw_alert
        captured["normalized_alert"] = normalized_alert
        return normalized_alert

    monkeypatch.setattr(
        "app.repositories.alerts.persist_and_score_alert",
        fake_persist_and_score_alert,
    )

    result = ingest_wazuh_event(session, payload, actor=actor)

    assert result.status == "ingested"
    assert result.alert.detection_type == DetectionType.BRUTE_FORCE
    assert result.alert.risk_score_value == 97
    assert result.responses_created == 1
    assert captured["raw_alert"] is not None
    assert captured["normalized_alert"] is not None
    assert session.commits == 1


def test_ingest_suricata_event_returns_duplicate_existing_alert(monkeypatch) -> None:
    session = FakeSession()
    payload = _fixture("suricata_port_scan.json")
    asset = Asset(
        id=uuid4(),
        hostname="detected-10-20-1-15",
        ip_address="10.20.1.15",
        operating_system=None,
        criticality=AssetCriticality.MEDIUM,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    raw_alert = RawAlert(
        id=uuid4(),
        asset=asset,
        source="suricata",
        external_id="flow-pt-001",
        detection_type=DetectionType.PORT_SCAN,
        severity=7,
        raw_payload=payload,
        received_at=datetime.now(UTC),
    )
    normalized_alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw_alert,
        asset=asset,
        source="suricata",
        title="Existing port scan alert",
        description="Already ingested.",
        detection_type=DetectionType.PORT_SCAN,
        severity=7,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "198.51.100.55"},
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        "app.services.ingestion.service.AlertsRepository.get_raw_alert_by_source_external_id",
        lambda self, source, external_id: raw_alert,
    )
    monkeypatch.setattr(
        "app.services.ingestion.service.AuditLogsRepository.create",
        lambda self, audit_log: audit_log,
    )

    result = ingest_suricata_event(session, payload)

    assert result.status == "duplicate"
    assert result.alert.id == normalized_alert.id
    assert "Duplicate source event ignored" in result.warnings[0]


def test_ingest_suricata_event_logs_failure_for_malformed_payload(monkeypatch) -> None:
    session = FakeSession()
    recorded: dict[str, object] = {}

    def fake_upsert_failure(
        self,
        *,
        source,
        external_id,
        detection_hint,
        error_type,
        error_message,
        raw_payload,
    ):
        recorded["source"] = source
        recorded["external_id"] = external_id
        recorded["detection_hint"] = detection_hint
        recorded["error_type"] = error_type
        recorded["error_message"] = error_message
        return type("Failure", (), {"id": uuid4(), "retry_count": 1})()

    monkeypatch.setattr(
        "app.services.ingestion.service.IngestionFailuresRepository.upsert_failure",
        fake_upsert_failure,
    )
    monkeypatch.setattr(
        "app.services.ingestion.service.AuditLogsRepository.create",
        lambda self, audit_log: audit_log,
    )

    with pytest.raises(HTTPException) as exc_info:
        ingest_suricata_event(session, _fixture("suricata_unsupported_detection.json"))

    assert exc_info.value.status_code == 422
    assert recorded["source"] == "suricata"
    assert recorded["error_type"] == "unsupported_detection"
    assert session.commits == 1


def test_resolve_or_create_asset_reuses_existing_asset_after_unique_race(
    monkeypatch,
) -> None:
    session = FakeSession()
    session.raise_integrity_error_on_flush = True
    parsed_event = ParsedSecurityEvent(
        source="wazuh",
        external_id="wazuh-fixture-fim-001",
        detection_type=DetectionType.FILE_INTEGRITY_VIOLATION,
        severity=9,
        title="File integrity violation detected",
        description="Critical file integrity change detected.",
        observed_at=datetime.now(UTC),
        normalized_payload={"file_path": "D:\\Operations\\Policies\\access-control.xlsx"},
        raw_payload={},
        asset_hostname="ops-files-03",
        asset_ip="10.42.7.54",
        asset_operating_system="Windows Server 2022",
        asset_criticality=AssetCriticality.MEDIUM,
    )
    reused_asset = Asset(
        id=uuid4(),
        hostname="ops-files-03",
        ip_address="10.42.7.54",
        operating_system="Windows Server 2022",
        criticality=AssetCriticality.MEDIUM,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    lookup_calls = {"count": 0}

    def fake_lookup(self, *, hostname, ip_address):
        lookup_calls["count"] += 1
        return reused_asset if lookup_calls["count"] == 2 else None

    monkeypatch.setattr(
        "app.services.ingestion.service.AssetsRepository.get_by_hostname_or_ip",
        fake_lookup,
    )

    asset, warnings = _resolve_or_create_asset(session, parsed_event)

    assert asset is reused_asset
    assert session.rollbacks == 1
    assert any("asset-create race" in warning for warning in warnings)
