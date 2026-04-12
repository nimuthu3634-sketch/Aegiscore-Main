import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

pytest.importorskip("tensorflow")

from app.models.enums import IncidentPriority, ScoreMethod
from app.services.scoring import alert_prioritization as ap
from app.services.scoring.ml import (
    load_priority_model,
    score_with_model,
    train_priority_model,
)
from app.services.scoring.types import AlertRiskFeatures


def test_train_alert_prioritization_model_and_score(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dataset_path = repo_root / "ai" / "datasets" / "alerts_dataset.csv"
    model_path = tmp_path / "alert-priority.keras"
    metadata_path = tmp_path / "alert-priority.metadata.json"
    eval_dir = tmp_path / "eval_out"
    os.environ["AI_EVAL_OUTPUT_DIR"] = str(eval_dir)
    try:
        metadata = train_priority_model(
            dataset_path=dataset_path,
            model_output_path=model_path,
            metadata_output_path=metadata_path,
            requested_version="test_alert_model_v1",
        )
    finally:
        os.environ.pop("AI_EVAL_OUTPUT_DIR", None)

    assert metadata["training_schema"] == ap.TRAINING_SCHEMA
    assert model_path.exists()
    assert metadata_path.exists()
    assert metadata["model_version"] == "test_alert_model_v1"
    assert metadata["training_rows"] >= 1200
    assert set(metadata["label_classes"]) == {"low", "medium", "high"}
    assert (eval_dir / "confusion_matrix.csv").exists()
    assert (eval_dir / "classification_report.txt").exists()
    assert metadata.get("metrics", {}).get("test_accuracy", 0) >= 0.0

    model, loaded_metadata = load_priority_model(
        model_path=model_path,
        metadata_path=metadata_path,
    )
    result = score_with_model(
        features=AlertRiskFeatures(
            observed_at=datetime.now(UTC),
            source_type="wazuh",
            detection_type="brute_force",
            source_severity=10,
            source_rule_level=12,
            repeated_event_count=6,
            time_window_density=4,
            asset_criticality="critical",
            privileged_account_flag=True,
            sensitive_file_flag=False,
            repeated_source_ip=4,
            repeated_failed_logins=22,
            recurrence_history=2,
            destination_port=22,
            has_destination_port=True,
            username="admin",
            asset_hostname="dc01.corp.local",
        ),
        model=model,
        metadata=loaded_metadata,
    )

    assert result.scoring_method == ScoreMethod.TENSORFLOW_MODEL
    assert result.model_version == "test_alert_model_v1"
    assert result.priority_label != IncidentPriority.CRITICAL
    assert result.priority_label in {
        IncidentPriority.LOW,
        IncidentPriority.MEDIUM,
        IncidentPriority.HIGH,
    }
    assert 0 <= result.score <= 100
    exp = result.explanation or {}
    assert exp.get("scoring_method") == ScoreMethod.TENSORFLOW_MODEL.value
    assert exp.get("model_priority_tier") in {"low", "medium", "high"}
    probs = exp.get("class_probabilities") or {}
    assert set(probs.keys()) == {"low", "medium", "high"}
    assert abs(sum(float(probs[k]) for k in probs) - 1.0) < 0.02
    assert "TensorFlow" in (exp.get("rationale") or "")

    out = ap.predict_alert_model_json(
        model=model,
        metadata=loaded_metadata,
        payload={
            "timestamp": "2025-02-01T14:00:00Z",
            "threat_type": "brute_force",
            "source_ip": "10.1.2.3",
            "target_host": "web-01.corp.local",
            "username": "root",
            "failed_logins_1m": 5,
            "failed_logins_5m": 12,
            "unique_ports_1m": 0,
            "integrity_change": "none",
            "new_user_created": 0,
            "off_hours": 1,
            "privileged_account": 1,
            "asset_criticality": "high",
            "wazuh_rule_level": 12,
            "suricata_severity": 0,
            "blacklisted_ip": 1,
        },
    )
    assert out["predicted_label"] in {"low", "medium", "high"}
    assert 0.0 <= out["confidence"] <= 1.0
    assert set(out["probabilities"]) == {"low", "medium", "high"}
    assert abs(sum(out["probabilities"].values()) - 1.0) < 0.01


def test_train_legacy_fixture_tensorflow_model(tmp_path: Path) -> None:
    """LEGACY: small fixture CSV with priority_label + MODEL_* columns (legacy 4-tier TensorFlow head)."""
    repo_root = Path(__file__).resolve().parents[3]
    dataset_path = repo_root / "ai" / "datasets" / "risk_training_fixture.csv"
    model_path = tmp_path / "risk-model.keras"
    metadata_path = tmp_path / "risk-model.metadata.json"

    metadata = train_priority_model(
        dataset_path=dataset_path,
        model_output_path=model_path,
        metadata_output_path=metadata_path,
        requested_version="test_model_legacy_fixture",
    )

    assert model_path.exists()
    assert metadata_path.exists()
    assert metadata["model_version"] == "test_model_legacy_fixture"
    assert metadata["training_rows"] >= 16
    assert metadata.get("training_schema") == "legacy_risk_fixture"

    model, loaded_metadata = load_priority_model(
        model_path=model_path,
        metadata_path=metadata_path,
    )
    result = score_with_model(
        features=AlertRiskFeatures(
            observed_at=datetime.now(UTC),
            source_type="wazuh",
            detection_type="unauthorized_user_creation",
            source_severity=9,
            source_rule_level=10,
            repeated_event_count=3,
            time_window_density=2,
            asset_criticality="critical",
            privileged_account_flag=True,
            sensitive_file_flag=False,
            repeated_source_ip=2,
            repeated_failed_logins=0,
            recurrence_history=2,
            destination_port=0,
            has_destination_port=False,
            username="svc-shadow",
            asset_hostname="acct-windows-01",
        ),
        model=model,
        metadata=loaded_metadata,
    )

    assert result.scoring_method == ScoreMethod.TENSORFLOW_MODEL
    assert result.model_version == "test_model_legacy_fixture"
    assert result.priority_label in {
        IncidentPriority.HIGH,
        IncidentPriority.CRITICAL,
    }
    assert 0 <= result.score <= 100
