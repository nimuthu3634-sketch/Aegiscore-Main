"""AI/ML submission readiness: script parity, artifact load, and automation test pointers."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load_validate_script():
    path = REPO_ROOT / "scripts" / "validate_ai_ml_readiness.py"
    spec = importlib.util.spec_from_file_location("validate_ai_ml_readiness", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_ai_ml_readiness"] = module
    spec.loader.exec_module(module)
    return module


def test_validate_ai_ml_script_reports_no_errors() -> None:
    mod = _load_validate_script()
    errors = mod.validate_ai_ml_readiness(REPO_ROOT)
    assert not errors, ";\n".join(errors)


def test_load_priority_model_from_committed_artifacts() -> None:
    pytest.importorskip("sqlalchemy", reason="API deps not installed (use Docker image for full run)")
    keras_path = REPO_ROOT / "ai" / "models" / "aegiscore-risk-priority-model.keras"
    meta_path = REPO_ROOT / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json"
    if not keras_path.is_file() or not meta_path.is_file():
        pytest.skip("Committed Keras artifacts not present in workspace")

    pytest.importorskip("tensorflow", reason="TensorFlow not installed")

    from app.services.scoring.ml import load_priority_model

    model, metadata = load_priority_model(model_path=keras_path, metadata_path=meta_path)
    assert model is not None
    assert metadata.get("training_schema") in ("alert_prioritization_v1", "alert_prioritization_v2")
    assert set(metadata.get("label_classes", [])) == {"low", "medium", "high", "critical"}


def test_load_priority_model_rejects_non_keras_suffix(tmp_path) -> None:
    pytest.importorskip("sqlalchemy", reason="API deps not installed (use Docker image for full run)")
    pytest.importorskip("tensorflow", reason="TensorFlow not installed")
    from app.services.scoring.ml import ModelArtifactUnavailableError, load_priority_model

    joblib_like = tmp_path / "not-a-model.joblib"
    joblib_like.write_bytes(b"")
    meta = REPO_ROOT / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json"
    if not meta.is_file():
        pytest.skip("metadata not present")
    with pytest.raises(ModelArtifactUnavailableError, match="Expected TensorFlow|joblib"):
        load_priority_model(model_path=joblib_like, metadata_path=meta)


def test_committed_metadata_json_has_valid_label_classes() -> None:
    meta_path = REPO_ROOT / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json"
    if not meta_path.is_file():
        pytest.skip("metadata not present")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    classes = [str(x).lower() for x in (meta.get("label_classes") or [])]
    assert set(classes) == {"low", "medium", "high", "critical"}


# Brute-force ML automation gates: implemented in tests/test_response_automation.py
#   - test_ml_brute_force_auto_block_executes_when_all_gates_met
#   - test_ml_brute_force_auto_block_skipped_when_failed_logins_below_threshold
#   - test_ml_brute_force_auto_block_skipped_for_non_brute_high_risk
# Baseline fallback when model path invalid: tests/test_scoring_integration_service.py