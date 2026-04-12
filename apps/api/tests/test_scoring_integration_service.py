"""``score_alert`` integration: model strategy + baseline fallback."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.asset import Asset
from app.models.enums import (
    AlertStatus,
    AssetCriticality,
    DetectionType,
    IncidentPriority,
    ScoreMethod,
)
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.risk_score import RiskScore
from app.services.scoring.ml import ModelArtifactUnavailableError
from app.services.scoring.service import score_alert
from app.services.scoring.types import AlertRiskFeatures, ScoringResult


@pytest.fixture
def minimal_alert() -> NormalizedAlert:
    now = datetime.now(UTC)
    asset = Asset(
        id=uuid4(),
        hostname="h1",
        ip_address="10.0.0.1",
        operating_system="Linux",
        criticality=AssetCriticality.MEDIUM,
        created_at=now,
        updated_at=now,
    )
    raw = RawAlert(
        id=uuid4(),
        asset=asset,
        source="wazuh",
        external_id="e1",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=5,
        raw_payload={"source_ip": "10.0.0.2"},
        received_at=now,
    )
    alert = NormalizedAlert(
        id=uuid4(),
        raw_alert=raw,
        asset=asset,
        source="wazuh",
        title="t",
        description="d",
        detection_type=DetectionType.BRUTE_FORCE,
        severity=5,
        status=AlertStatus.NEW,
        normalized_payload={"source_ip": "10.0.0.2", "failed_attempts": 3},
        created_at=now,
    )
    return alert


def test_score_alert_falls_back_to_baseline_when_model_artifacts_missing(
    monkeypatch: pytest.MonkeyPatch,
    minimal_alert: NormalizedAlert,
) -> None:
    session = MagicMock()

    features = AlertRiskFeatures(
        observed_at=datetime.now(UTC),
        source_type="wazuh",
        detection_type="brute_force",
        source_severity=5,
        source_rule_level=5,
        repeated_event_count=1,
        time_window_density=1,
        asset_criticality="medium",
        privileged_account_flag=False,
        sensitive_file_flag=False,
        repeated_source_ip=0,
        repeated_failed_logins=3,
        recurrence_history=0,
        destination_port=0,
        has_destination_port=False,
    )

    monkeypatch.setattr(
        "app.services.scoring.service.get_settings",
        lambda: SimpleNamespace(
            scoring_strategy="model",
            scoring_baseline_version="baseline_v1",
            scoring_model_path="/nonexistent/model.keras",
            scoring_model_metadata_path="/nonexistent/model.json",
        ),
    )
    monkeypatch.setattr(
        "app.services.scoring.service.extract_alert_features",
        lambda _session, _alert: features,
    )
    monkeypatch.setattr(
        "app.services.scoring.service.load_priority_model",
        MagicMock(side_effect=ModelArtifactUnavailableError("missing keras")),
    )
    monkeypatch.setattr(
        "app.services.scoring.service.evaluate_alert_policies",
        lambda *_a, **_k: [],
    )
    monkeypatch.setattr(
        "app.services.scoring.service.evaluate_incident_policies_for_alert",
        lambda *_a, **_k: [],
    )

    captured: dict[str, ScoringResult] = {}

    def capture_upsert(_self, alert: NormalizedAlert, result: ScoringResult) -> RiskScore:
        captured["result"] = result
        rs = RiskScore(
            id=uuid4(),
            normalized_alert=alert,
            score=result.score,
            confidence=result.confidence,
            priority_label=result.priority_label,
            scoring_method=result.scoring_method,
            baseline_version=result.baseline_version,
            model_version=result.model_version,
            reasoning=result.reasoning,
            explanation=result.explanation,
            feature_snapshot=result.feature_snapshot,
            calculated_at=datetime.now(UTC),
        )
        alert.risk_score = rs
        return rs

    monkeypatch.setattr(
        "app.services.scoring.service.RiskScoresRepository.upsert_for_alert",
        capture_upsert,
    )

    score_alert(session, minimal_alert)

    result = captured["result"]
    assert result.scoring_method == ScoreMethod.BASELINE_RULES
    assert "fallback_reason" in (result.explanation or {})
    assert "missing keras" in result.explanation["fallback_reason"]


def test_score_alert_uses_model_when_load_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    minimal_alert: NormalizedAlert,
    tmp_path,
) -> None:
    pytest.importorskip("tensorflow")

    from pathlib import Path

    from app.services.scoring.ml import train_priority_model

    repo_root = Path(__file__).resolve().parents[3]
    dataset = repo_root / "ai" / "datasets" / "alerts_dataset.csv"
    model_path = tmp_path / "m.keras"
    meta_path = tmp_path / "m.json"
    train_priority_model(
        dataset_path=dataset,
        model_output_path=model_path,
        metadata_output_path=meta_path,
        requested_version="integration_svc",
    )

    session = MagicMock()
    features = AlertRiskFeatures(
        observed_at=datetime.now(UTC),
        source_type="wazuh",
        detection_type="brute_force",
        source_severity=10,
        source_rule_level=12,
        repeated_event_count=4,
        time_window_density=2,
        asset_criticality="high",
        privileged_account_flag=False,
        sensitive_file_flag=False,
        repeated_source_ip=2,
        repeated_failed_logins=15,
        recurrence_history=0,
        destination_port=22,
        has_destination_port=True,
        username="u1",
        asset_hostname="auth.corp.local",
        source_ip="10.0.0.2",
    )

    monkeypatch.setattr(
        "app.services.scoring.service.get_settings",
        lambda: SimpleNamespace(
            scoring_strategy="model",
            scoring_baseline_version="baseline_v1",
            scoring_model_path=str(model_path),
            scoring_model_metadata_path=str(meta_path),
        ),
    )
    monkeypatch.setattr(
        "app.services.scoring.service.extract_alert_features",
        lambda _session, _alert: features,
    )
    monkeypatch.setattr(
        "app.services.scoring.service.evaluate_alert_policies",
        lambda *_a, **_k: [],
    )
    monkeypatch.setattr(
        "app.services.scoring.service.evaluate_incident_policies_for_alert",
        lambda *_a, **_k: [],
    )

    captured: dict[str, ScoringResult] = {}

    def capture_upsert(_self, alert: NormalizedAlert, result: ScoringResult) -> RiskScore:
        captured["result"] = result
        rs = RiskScore(
            id=uuid4(),
            normalized_alert=alert,
            score=result.score,
            confidence=result.confidence,
            priority_label=result.priority_label,
            scoring_method=result.scoring_method,
            baseline_version=result.baseline_version,
            model_version=result.model_version,
            reasoning=result.reasoning,
            explanation=result.explanation,
            feature_snapshot=result.feature_snapshot,
            calculated_at=datetime.now(UTC),
        )
        alert.risk_score = rs
        return rs

    monkeypatch.setattr(
        "app.services.scoring.service.RiskScoresRepository.upsert_for_alert",
        capture_upsert,
    )

    score_alert(session, minimal_alert)

    result = captured["result"]
    assert result.scoring_method == ScoreMethod.TENSORFLOW_MODEL
    assert result.priority_label != IncidentPriority.CRITICAL
    assert result.priority_label in {
        IncidentPriority.LOW,
        IncidentPriority.MEDIUM,
        IncidentPriority.HIGH,
    }
    exp = result.explanation or {}
    assert exp.get("scoring_method") == ScoreMethod.TENSORFLOW_MODEL.value
    assert result.model_version == "integration_svc"
    probs = exp.get("class_probabilities") or {}
    assert set(probs.keys()) == {"low", "medium", "high"}
    assert abs(sum(float(probs[k]) for k in probs) - 1.0) < 0.02
