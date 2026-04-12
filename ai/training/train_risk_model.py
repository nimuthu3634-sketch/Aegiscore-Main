from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _bootstrap_api_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    api_root = repo_root / "apps" / "api"
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))
    return repo_root


def main() -> None:
    repo_root = _bootstrap_api_path()

    from app.services.scoring.ml import train_priority_model

    dataset_path = Path(
        os.getenv(
            "AI_DATASET_PATH",
            repo_root / "ai" / "datasets" / "alerts_dataset.csv",
        )
    )
    model_output_path = Path(
        os.getenv(
            "AI_MODEL_PATH",
            repo_root / "ai" / "models" / "aegiscore-risk-priority-model.keras",
        )
    )
    metadata_output_path = Path(
        os.getenv(
            "AI_MODEL_METADATA_PATH",
            repo_root / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json",
        )
    )
    requested_version = os.getenv("AI_MODEL_VERSION")

    metadata = train_priority_model(
        dataset_path=dataset_path,
        model_output_path=model_output_path,
        metadata_output_path=metadata_output_path,
        requested_version=requested_version,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
