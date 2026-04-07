from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.models.asset import Asset
from app.models.enums import AssetCriticality, DetectionType, IncidentPriority, ScoreMethod
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.risk_score import RiskScore
from app.services.integrations import wazuh_connector

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
        wazuh_timestamp_field="timestamp",
        wazuh_page_size=200,
        wazuh_since_param="since",
        wazuh_connector_enabled=True,
        wazuh_base_url="https://wazuh.local:55000",
        wazuh_auth_mode="bearer",
        wazuh_bearer_token="token-1",
        wazuh_timeout_seconds=10.0,
        wazuh_retry_attempts=0,
        wazuh_retry_backoff_seconds=0.0,
        wazuh_verify_tls=False,
        wazuh_ca_file=None,
        wazuh_username=None,
        wazuh_password=None,
        wazuh_auth_endpoint="/security/user/authenticate",
        wazuh_alerts_path="/alerts",
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_wazuh_api_client_fetches_alert_items_with_checkpoint_param(monkeypatch) -> None:
    client = wazuh_connector.WazuhAPIClient(_test_settings())
    captured: dict[str, object] = {}

    monkeypatch.setattr(client, "_auth_headers", lambda: {"Authorization": "Bearer token-1"})

    def fake_request_json(*, method, path, headers, params):
        captured["method"] = method
        captured["path"] = path
        captured["params"] = params
        return {"data": {"affected_items": [{"id": "evt-1"}, {"id": "evt-2"}]}}

    monkeypatch.setattr(client, "_request_json", fake_request_json)

    events = client.fetch_events(checkpoint={"last_timestamp": "2026-04-06T12:00:00+00:00"})

    assert [event["id"] for event in events] == ["evt-1", "evt-2"]
    assert captured["method"] == "GET"
    assert captured["path"] == "/alerts"
    assert captured["params"] == {
        "limit": "200",
        "since": "2026-04-06T12:00:00+00:00",
    }


def test_run_wazuh_poll_cycle_reuses_ingestion_pipeline(monkeypatch) -> None:
    session = FakeSession()
    payload = _fixture("wazuh_brute_force.json")
    payload["id"] = "evt-2001"
    payload["timestamp"] = "2026-04-06T12:15:00Z"

    state_snapshot = {
        "checkpoint": {
            "last_timestamp": "2026-04-06T12:00:00+00:00",
            "last_external_ids": ["evt-1000"],
        },
        "metrics": {
            "poll_count": 3,
            "total_fetched": 20,
            "total_ingested": 15,
            "total_duplicates": 4,
            "total_failed": 1,
        },
    }
    saved: dict[str, object] = {}

    monkeypatch.setattr(
        wazuh_connector,
        "get_settings",
        lambda: _test_settings(wazuh_timestamp_field="timestamp"),
    )
    monkeypatch.setattr(
        wazuh_connector,
        "mark_connector_running",
        lambda session, connector: SimpleNamespace(
            checkpoint=state_snapshot["checkpoint"],
            metrics=state_snapshot["metrics"],
        ),
    )
    monkeypatch.setattr(
        wazuh_connector,
        "mark_connector_success",
        lambda session, connector, checkpoint, metrics: saved.update(
            {"checkpoint": checkpoint, "metrics": metrics}
        ),
    )
    monkeypatch.setattr(
        wazuh_connector,
        "mark_connector_error",
        lambda session, connector, error_message: None,
    )

    class FakeClient:
        def fetch_events(self, *, checkpoint):
            return [payload]

    created_asset = Asset(
        id=uuid4(),
        hostname="edge-auth-01",
        ip_address="10.42.0.21",
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
            score=88,
            confidence=0.91,
            priority_label=IncidentPriority.HIGH,
            scoring_method=ScoreMethod.BASELINE_RULES,
            reasoning="Connector integration test scoring.",
            explanation={"summary": "Connector flow scored successfully."},
            feature_snapshot={"source_ip": "203.0.113.8"},
            calculated_at=datetime.now(UTC),
        )
        return normalized_alert

    monkeypatch.setattr(
        "app.repositories.alerts.persist_and_score_alert",
        fake_persist_and_score_alert,
    )

    summary = wazuh_connector.run_wazuh_poll_cycle(
        session,
        client=FakeClient(),
    )

    assert summary == {"fetched": 1, "ingested": 1, "duplicates": 0, "failed": 0}
    assert saved["checkpoint"]["last_timestamp"] == "2026-04-06T12:15:00+00:00"
    assert saved["checkpoint"]["last_external_ids"] == ["evt-2001"]
    assert saved["metrics"]["poll_count"] == 4
    assert saved["metrics"]["total_fetched"] == 21
    assert saved["metrics"]["total_ingested"] == 16
    assert saved["metrics"]["total_duplicates"] == 4
    assert saved["metrics"]["total_failed"] == 1


def test_get_wazuh_connector_status_returns_persisted_state(monkeypatch) -> None:
    monkeypatch.setattr(wazuh_connector, "get_settings", lambda: _test_settings())
    state = SimpleNamespace(
        status="healthy",
        checkpoint={
            "last_timestamp": "2026-04-06T12:15:00+00:00",
            "last_external_ids": ["evt-2001", "evt-2002"],
        },
        metrics={
            "poll_count": 6,
            "total_fetched": 91,
            "total_ingested": 80,
            "total_duplicates": 8,
            "total_failed": 3,
        },
        last_success_at=datetime(2026, 4, 6, 12, 16, tzinfo=UTC),
        last_error_at=None,
        last_error_message=None,
    )
    monkeypatch.setattr(
        wazuh_connector,
        "get_connector_state",
        lambda session, connector: state,
    )

    result = wazuh_connector.get_wazuh_connector_status(session=object())

    assert result.connector == "wazuh_live_connector"
    assert result.enabled is True
    assert result.status == "healthy"
    assert result.last_checkpoint_timestamp == "2026-04-06T12:15:00+00:00"
    assert result.checkpoint_external_ids == ["evt-2001", "evt-2002"]
    assert result.metrics["total_ingested"] == 80
