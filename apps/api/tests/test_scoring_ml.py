from datetime import UTC, datetime
from pathlib import Path

from app.models.enums import IncidentPriority
from app.services.scoring.ml import (
    load_priority_model,
    score_with_model,
    train_priority_model,
)
from app.services.scoring.types import AlertRiskFeatures


def test_train_priority_model_and_score_fixture(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    dataset_path = repo_root / "ai" / "datasets" / "risk_training_fixture.csv"
    model_path = tmp_path / "risk-model.joblib"
    metadata_path = tmp_path / "risk-model.metadata.json"

    metadata = train_priority_model(
        dataset_path=dataset_path,
        model_output_path=model_path,
        metadata_output_path=metadata_path,
        requested_version="test_model_v1",
    )

    assert model_path.exists()
    assert metadata_path.exists()
    assert metadata["model_version"] == "test_model_v1"
    assert metadata["training_rows"] >= 16

    pipeline, loaded_metadata = load_priority_model(
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
        pipeline=pipeline,
        metadata=loaded_metadata,
    )

    assert result.model_version == "test_model_v1"
    assert result.priority_label in {
        IncidentPriority.HIGH,
        IncidentPriority.CRITICAL,
    }
    assert 0 <= result.score <= 100
