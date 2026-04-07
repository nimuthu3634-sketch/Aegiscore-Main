from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.models.asset import Asset
from app.models.enums import AssetCriticality, IncidentPriority, ScoreMethod
from app.models.risk_score import RiskScore
from app.services.integrations import suricata_connector

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ingestion"


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.flushed = 0
        self.rollbacks = 0

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1

    def flush(self) -> None:
        self.flushed += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _test_settings(**overrides):
    defaults = dict(
        suricata_connector_enabled=True,
        suricata_connector_mode="file_tail",
        suricata_eve_file_path="/tmp/eve.json",
        suricata_poll_interval_seconds=15,
        suricata_max_events_per_cycle=250,
        suricata_retry_attempts=2,
        suricata_retry_backoff_seconds=1.0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_run_suricata_poll_cycle_tails_eve_file_and_updates_checkpoint(
    monkeypatch,
    tmp_path,
) -> None:
    session = FakeSession()
    payload = _fixture("suricata_port_scan.json")
    payload["flow_id"] = "flow-live-1001"
    eve_path = tmp_path / "eve.json"
    eve_path.write_text(
        json.dumps(payload) + "\n" + "not-json\n",
        encoding="utf-8",
    )

    recorded: dict[str, object] = {}
    state_snapshot = {
        "checkpoint": {"offset": 0},
        "metrics": {
            "poll_count": 1,
            "total_fetched": 10,
            "total_ingested": 8,
            "total_duplicates": 1,
            "total_failed": 1,
        },
    }

    monkeypatch.setattr(
        suricata_connector,
        "get_settings",
        lambda: _test_settings(suricata_eve_file_path=str(eve_path)),
    )
    monkeypatch.setattr(
        suricata_connector,
        "mark_connector_running",
        lambda session, connector: SimpleNamespace(
            checkpoint=state_snapshot["checkpoint"],
            metrics=state_snapshot["metrics"],
        ),
    )
    monkeypatch.setattr(
        suricata_connector,
        "mark_connector_success",
        lambda session, connector, checkpoint, metrics: recorded.update(
            {"checkpoint": checkpoint, "metrics": metrics}
        ),
    )
    monkeypatch.setattr(
        suricata_connector,
        "_record_malformed_line_failure",
        lambda session, **kwargs: None,
    )

    created_asset = Asset(
        id=uuid4(),
        hostname="edge-gateway-01",
        ip_address="10.20.1.15",
        operating_system="Ubuntu 22.04",
        criticality=AssetCriticality.HIGH,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
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
            score=79,
            confidence=0.88,
            priority_label=IncidentPriority.HIGH,
            scoring_method=ScoreMethod.BASELINE_RULES,
            reasoning="Live port-scan integration scoring.",
            explanation={"summary": "Suricata connector scored event."},
            feature_snapshot={"source_ip": "198.51.100.55"},
            calculated_at=datetime.now(UTC),
        )
        return normalized_alert

    monkeypatch.setattr(
        "app.repositories.alerts.persist_and_score_alert",
        fake_persist_and_score_alert,
    )

    summary = suricata_connector.run_suricata_poll_cycle(session)

    assert summary == {"fetched": 2, "ingested": 1, "duplicates": 0, "failed": 1}
    assert recorded["checkpoint"]["offset"] > 0
    assert recorded["checkpoint"]["inode"] is not None
    assert recorded["metrics"]["poll_count"] == 2
    assert recorded["metrics"]["total_fetched"] == 12
    assert recorded["metrics"]["total_ingested"] == 9
    assert recorded["metrics"]["total_failed"] == 2


def test_run_suricata_poll_cycle_reuses_offset_checkpoint(monkeypatch, tmp_path) -> None:
    session = FakeSession()
    payload = _fixture("suricata_port_scan.json")
    payload["flow_id"] = "flow-live-2001"
    first_line = json.dumps(payload) + "\n"
    eve_path = tmp_path / "eve.json"
    eve_path.write_text(first_line, encoding="utf-8")

    checkpoint_offset = len(first_line)
    monkeypatch.setattr(
        suricata_connector,
        "get_settings",
        lambda: _test_settings(suricata_eve_file_path=str(eve_path)),
    )
    monkeypatch.setattr(
        suricata_connector,
        "mark_connector_running",
        lambda session, connector: SimpleNamespace(
            checkpoint={"offset": checkpoint_offset, "inode": eve_path.stat().st_ino},
            metrics={},
        ),
    )
    monkeypatch.setattr(
        suricata_connector,
        "mark_connector_success",
        lambda session, connector, checkpoint, metrics: None,
    )

    summary = suricata_connector.run_suricata_poll_cycle(session)
    assert summary == {"fetched": 0, "ingested": 0, "duplicates": 0, "failed": 0}


def test_get_suricata_connector_status_returns_checkpoint_and_metrics(monkeypatch) -> None:
    monkeypatch.setattr(suricata_connector, "get_settings", lambda: _test_settings())
    state = SimpleNamespace(
        status="healthy",
        checkpoint={"offset": 4096, "inode": 77512},
        metrics={
            "poll_count": 4,
            "total_fetched": 90,
            "total_ingested": 82,
            "total_duplicates": 5,
            "total_failed": 3,
        },
        last_success_at=datetime(2026, 4, 7, 4, 0, tzinfo=UTC),
        last_error_at=None,
        last_error_message=None,
    )
    monkeypatch.setattr(
        suricata_connector,
        "get_connector_state",
        lambda session, connector: state,
    )

    result = suricata_connector.get_suricata_connector_status(session=object())

    assert result.connector == "suricata_live_connector"
    assert result.enabled is True
    assert result.mode == "file_tail"
    assert result.status == "healthy"
    assert result.checkpoint_offset == 4096
    assert result.checkpoint_inode == 77512
    assert result.metrics["total_ingested"] == 82
