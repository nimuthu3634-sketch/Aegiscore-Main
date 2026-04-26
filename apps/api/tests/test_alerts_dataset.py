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

    for lb in ("Critical", "High", "Medium", "Low"):
        assert labels[lb] > 0, f"Missing or empty label={lb!r}"

    extra = set(labels) - {"Critical", "High", "Medium", "Low"}
    assert not extra, f"label column must be only Critical/High/Medium/Low; found {sorted(extra)}"

    assert threats["brute_force"] > 0
    assert threats["normal"] > 0

    expected_cols = {
        "source_type",
        "threat_type",
        "asset_criticality",
        "integrity_change",
        "wazuh_rule_level",
        "suricata_severity",
        "failed_logins_1m",
        "failed_logins_5m",
        "unique_ports_1m",
        "repeated_event_count",
        "time_window_density",
        "recurrence_history",
        "new_user_created",
        "off_hours",
        "privileged_account",
        "blacklisted_ip",
        "label",
    }
    assert set(reader.fieldnames or []) == expected_cols


def test_generate_alerts_dataset_script_writes_contract_csv(tmp_path: Path) -> None:
    """CLI generator produces the same column schema and in-scope threat types."""
    script = _repo_root() / "ai" / "datasets" / "generate_alerts_dataset.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        check=True,
        capture_output=True,
        text=True,
    )
    # Generator writes to its default path; read from there
    default_csv = _dataset_csv()
    assert default_csv.is_file()
    with default_csv.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    assert len(rows) >= 1200
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
    for lb in ("Critical", "High", "Medium", "Low"):
        assert labels[lb] > 0
    assert not (set(labels) - {"Critical", "High", "Medium", "Low"})