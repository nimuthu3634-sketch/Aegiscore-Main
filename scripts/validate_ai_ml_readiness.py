#!/usr/bin/env python3
"""
Lightweight AI/ML submission readiness checks (stdlib only).

Validates dataset contract, committed Keras metadata design, and prints
how to run pytest for brute-force ML automation gates.

Usage (repo root):

    py -3 scripts/validate_ai_ml_readiness.py

Exit code 0 if all checks pass; non-zero with messages on stderr otherwise.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


REQUIRED_THREAT_TYPES = (
    "normal",
    "brute_force",
    "port_scan",
    "file_integrity",
    "unauthorized_user_creation",
)
ALLOWED_LABELS = frozenset({"Critical", "High", "Medium", "Low"})
MIN_TRAINING_ROWS = 200  # excludes stale tiny fixtures (e.g. 20-row sklearn era)
EXPECTED_LABEL_CLASSES = ["low", "medium", "high", "critical"]


def validate_ai_ml_readiness(repo_root: Path | None = None) -> list[str]:
    """Return a list of human-readable errors; empty list means success."""
    root = repo_root or _repo_root()
    errors: list[str] = []

    dataset = root / "ai" / "datasets" / "alerts_dataset.csv"
    if not dataset.is_file():
        errors.append(f"Missing dataset: {dataset}")
        return errors

    with dataset.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            errors.append("Dataset has no header row")
            return errors
        rows = list(reader)

    if not rows:
        errors.append("Dataset is empty")
        return errors

    threats = Counter(r.get("threat_type", "").strip() for r in rows)
    labels = Counter(r.get("label", "").strip() for r in rows)

    for t in REQUIRED_THREAT_TYPES:
        if threats.get(t, 0) <= 0:
            errors.append(f"Dataset missing threat_type rows for {t!r}")

    unknown_labels = set(labels) - ALLOWED_LABELS
    if unknown_labels:
        errors.append(f"Dataset label column has values outside Critical/High/Medium/Low: {sorted(unknown_labels)}")

    for lb in ("Critical", "High", "Medium", "Low"):
        if labels.get(lb, 0) <= 0:
            errors.append(f"Dataset missing label rows for {lb!r}")

    keras_path = root / "ai" / "models" / "aegiscore-risk-priority-model.keras"
    meta_path = root / "ai" / "models" / "aegiscore-risk-priority-model.metadata.json"

    if not keras_path.is_file():
        errors.append(f"Missing Keras model: {keras_path}")
    if not meta_path.is_file():
        errors.append(f"Missing metadata JSON: {meta_path}")
    if errors:
        return errors

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in metadata: {exc}")
        return errors

    if meta.get("framework") != "tensorflow":
        errors.append('metadata "framework" must be "tensorflow"')
    mf = meta.get("ml_framework")
    if mf is not None and mf != "tensorflow":
        errors.append('metadata "ml_framework" must be "tensorflow" when present')

    if meta.get("training_schema") != "alert_prioritization_v1":
        errors.append(
            f'metadata training_schema must be "alert_prioritization_v1", got {meta.get("training_schema")!r}'
        )

    lc = meta.get("label_classes")
    if lc != EXPECTED_LABEL_CLASSES:
        errors.append(f'metadata label_classes must be {EXPECTED_LABEL_CLASSES}, got {lc!r}')

    tr = meta.get("training_rows")
    if not isinstance(tr, int) or tr < MIN_TRAINING_ROWS:
        errors.append(
            f"metadata training_rows must be an integer >= {MIN_TRAINING_ROWS} (got {tr!r})"
        )

    return errors


def main() -> int:
    errs = validate_ai_ml_readiness()
    if errs:
        print("AI/ML readiness validation FAILED:", file=sys.stderr)
        for line in errs:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print("AI/ML readiness validation passed.")
    print("  - ai/datasets/alerts_dataset.csv contract OK")
    print("  - ai/models/aegiscore-risk-priority-model.{keras,metadata.json} OK")
    print("  - metadata matches alert_prioritization_v1 / 4-class TensorFlow design")
    print("Optional: run brute-force ML gate tests:")
    print(
        "  docker compose run --rm --no-deps --entrypoint pytest api "
        "tests/test_response_automation.py -k ml_brute_force -q"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())