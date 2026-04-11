from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def _bootstrap_api_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    api_root = repo_root / "apps" / "api"
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))
    return repo_root


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a normalized alert feature payload.")
    parser.add_argument(
        "--features-file",
        required=True,
        help="Path to a JSON file containing the alert feature snapshot.",
    )
    return parser.parse_args()


def main() -> None:
    repo_root = _bootstrap_api_path()

    from app.services.scoring.ml import load_priority_model, score_with_model
    from app.services.scoring.types import AlertRiskFeatures

    args = _parse_args()
    payload = json.loads(Path(args.features_file).read_text(encoding="utf-8"))

    features = AlertRiskFeatures(
        observed_at=datetime.fromisoformat(payload.get("observed_at", datetime.now(UTC).isoformat())),
        source_type=str(payload["source_type"]),
        detection_type=str(payload["detection_type"]),
        source_severity=int(payload["source_severity"]),
        source_rule_level=int(payload.get("source_rule_level", payload["source_severity"])),
        repeated_event_count=int(payload.get("repeated_event_count", 1)),
        time_window_density=int(payload.get("time_window_density", 1)),
        asset_criticality=str(payload.get("asset_criticality", "unknown")),
        privileged_account_flag=bool(payload.get("privileged_account_flag", False)),
        sensitive_file_flag=bool(payload.get("sensitive_file_flag", False)),
        repeated_source_ip=int(payload.get("repeated_source_ip", 0)),
        repeated_failed_logins=int(payload.get("repeated_failed_logins", 0)),
        recurrence_history=int(payload.get("recurrence_history", 0)),
        destination_port=int(payload.get("destination_port", 0)),
        has_destination_port=bool(payload.get("has_destination_port", False)),
        source_ip=payload.get("source_ip"),
        destination_ip=payload.get("destination_ip"),
        username=payload.get("username"),
        asset_hostname=payload.get("asset_hostname"),
        asset_id=payload.get("asset_id"),
        alert_id=payload.get("alert_id"),
        external_id=payload.get("external_id"),
    )

    model_path = Path(
        os.getenv(
            "AI_MODEL_PATH",
            repo_root / "ai" / "models" / "aegiscore-risk-priority-model.keras",
        )
    )
    metadata_path = Path(
        os.getenv(
            "AI_MODEL_METADATA_PATH",
            repo_root / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json",
        )
    )

    model, metadata = load_priority_model(
        model_path=model_path,
        metadata_path=metadata_path,
    )
    result = score_with_model(
        features=features,
        model=model,
        metadata=metadata,
    )
    print(
        json.dumps(
            {
                "score": result.score,
                "confidence": result.confidence,
                "priority_label": result.priority_label.value,
                "scoring_method": result.scoring_method.value,
                "model_version": result.model_version,
                "explanation": result.explanation,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
