"""
AegisCore Enterprise — Model Training Entry Point
=================================================
Trains the enterprise TensorFlow Keras 4-class alert priority classifier.

Architecture: Dense(256)+BN+Drop(0.3) → Dense(128)+BN+Drop(0.2)
            → Dense(64)+BN+Drop(0.1) → Dense(32) → Dense(4, softmax)

Usage:
    python ai/training/train_risk_model.py

Environment variables (all optional):
    AI_DATASET_PATH          default: ai/datasets/alerts_dataset.csv
    AI_MODEL_PATH            default: ai/models/aegiscore-risk-priority-model.keras
    AI_MODEL_METADATA_PATH   default: ai/models/aegiscore-risk-priority-model.metadata.json
    AI_MODEL_VERSION         default: auto timestamp
    AI_EVAL_OUTPUT_DIR       default: ai/outputs/alert_prioritization
    AI_SEED                  default: 42
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _bootstrap_api_path() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    api_root  = repo_root / "apps" / "api"
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))
    return repo_root


def main() -> None:
    repo_root = _bootstrap_api_path()
    from app.services.scoring.ml import train_priority_model

    dataset_path = Path(os.getenv(
        "AI_DATASET_PATH", str(repo_root / "ai" / "datasets" / "alerts_dataset.csv")
    ))
    model_output_path = Path(os.getenv(
        "AI_MODEL_PATH",
        str(repo_root / "ai" / "models" / "aegiscore-risk-priority-model.keras")
    ))
    metadata_output_path = Path(os.getenv(
        "AI_MODEL_METADATA_PATH",
        str(repo_root / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json")
    ))
    requested_version = os.getenv("AI_MODEL_VERSION")
    seed = int(os.getenv("AI_SEED", "42"))

    if not dataset_path.exists():
        print(f"[ERROR] Dataset not found: {dataset_path}")
        print("Regenerate it: python ai/datasets/generate_alerts_dataset.py")
        sys.exit(1)

    row_count = sum(1 for _ in open(dataset_path)) - 1
    print("=" * 65)
    print("  AegisCore Enterprise — Alert Priority Model Training")
    print("=" * 65)
    print(f"  Dataset       : {dataset_path.name}  ({row_count:,} rows)")
    print(f"  Architecture  : Dense(256)+BN+Drop(0.3) → Dense(128)+BN+Drop(0.2)")
    print(f"                  → Dense(64)+BN+Drop(0.1) → Dense(32) → Dense(4, softmax)")
    print(f"  Classes       : critical / high / medium / low")
    print(f"  Split         : 60% train / 20% val / 20% test (stratified)")
    print(f"  Max epochs    : 150  (EarlyStopping patience=20)")
    print(f"  LR schedule   : ReduceLROnPlateau (patience=10, factor=0.5)")
    print(f"  Seed          : {seed}")
    print()

    metadata = train_priority_model(
        dataset_path=dataset_path,
        model_output_path=model_output_path,
        metadata_output_path=metadata_output_path,
        requested_version=requested_version,
    )

    print("=" * 65)
    print("  Training Complete")
    print("=" * 65)
    print(f"  Version         : {metadata.get('model_version')}")
    print(f"  Epochs trained  : {metadata.get('epochs_trained', 'N/A')}")
    print(f"  Train rows      : {metadata.get('training_rows', metadata.get('train_rows'))}")
    print(f"  Val rows        : {metadata.get('validation_rows')}")
    print(f"  Test rows       : {metadata.get('test_rows')}")
    print(f"  Train accuracy  : {metadata.get('train_accuracy', 0):.1%}")
    print(f"  Val accuracy    : {metadata.get('validation_accuracy', 0):.1%}")
    print(f"  Test accuracy   : {metadata.get('test_accuracy', 0):.1%}")
    print()
    print("  Per-class test accuracy:")
    per_class = metadata.get("per_class_test_accuracy", {})
    for cls in ["critical", "high", "medium", "low"]:
        acc = per_class.get(cls)
        bar = "█" * int((acc or 0) * 20)
        print(f"    {cls:10s}: {bar:20s}  {f'{acc:.1%}' if acc is not None else 'N/A'}")
    print()
    cm = metadata.get("confusion_matrix", {})
    if cm:
        labels = list(cm.keys())
        print("  Confusion matrix (test set):")
        print(f"    {'true\\pred':12s}" + "".join(f"{l:>10s}" for l in labels))
        for t in labels:
            row = "".join(f"{cm[t].get(p,0):>10d}" for p in labels)
            print(f"    {t:12s}{row}")
    print()
    print(f"  Model saved : {model_output_path}")
    print(f"  Metadata    : {metadata_output_path}")


if __name__ == "__main__":
    main()
