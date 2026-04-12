"""Synthetic alerts training CSV contract (see ``ai/datasets/``)."""

from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _generator_script() -> Path:
    return _repo_root() / "ai" / "datasets" / "generate_alerts_dataset.py"


def _dataset_csv() -> Path:
    return _repo_root() / "ai" / "datasets" / "alerts_dataset.csv"


def test_alerts_dataset_csv_exists() -> None:
    path = _dataset_csv()
    assert path.is_file(), f"Expected committed dataset at {path}"


def test_alerts_dataset_generator_script_exists() -> None:
    assert _generator_script().is_file()


def test_alerts_dataset_includes_threat_types_labels_and_counts() -> None:
    path = _dataset_csv()
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert len(rows) >= 1200, "Dataset should meet minimum row count for training"
    threats = Counter(r["threat_type"].strip() for r in rows)
    labels = Counter(r["label"].strip() for r in rows)

    for t in (
        "normal",
        "brute_force",
        "port_scan",
        "file_integrity",
        "unauthorized_user_creation",
    ):
        assert threats[t] > 0, f"Missing or empty threat_type={t!r}"

    for lb in ("Low", "Medium", "High"):
        assert labels[lb] > 0, f"Missing or empty label={lb!r}"

    extra = set(labels) - {"Low", "Medium", "High"}
    assert not extra, f"label column must be only Low/Medium/High; found {sorted(extra)}"

    assert threats["brute_force"] > 0
    assert threats["normal"] > 0

    expected_cols = {
        "timestamp",
        "threat_type",
        "source_ip",
        "target_host",
        "username",
        "failed_logins_1m",
        "failed_logins_5m",
        "unique_ports_1m",
        "integrity_change",
        "new_user_created",
        "off_hours",
        "privileged_account",
        "asset_criticality",
        "wazuh_rule_level",
        "suricata_severity",
        "blacklisted_ip",
        "label",
    }
    assert set(reader.fieldnames or []) == expected_cols


def test_generate_alerts_dataset_script_writes_contract_csv(tmp_path: Path) -> None:
    """CLI generator produces the same column schema and in-scope threat types."""
    script = _repo_root() / "ai" / "datasets" / "generate_alerts_dataset.py"
    out = tmp_path / "generated.csv"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--rows",
            "500",
            "--seed",
            "99",
            "--output",
            str(out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert out.is_file()
    with out.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) == 500
    threats = Counter(r["threat_type"].strip() for r in rows)
    labels = Counter(r["label"].strip() for r in rows)
    for t in (
        "normal",
        "brute_force",
        "port_scan",
        "file_integrity",
        "unauthorized_user_creation",
    ):
        assert threats[t] > 0
    for lb in ("Low", "Medium", "High"):
        assert labels[lb] > 0
    assert not (set(labels) - {"Low", "Medium", "High"})
