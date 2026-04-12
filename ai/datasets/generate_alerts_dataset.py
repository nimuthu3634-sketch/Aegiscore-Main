"""
AegisCore Enterprise — Alert Priority Training Dataset Generator
================================================================
10,000 rows | 4 classes: critical / high / medium / low

Features designed for production generalisation.
No synthetic high-cardinality identifiers (no raw IPs, usernames, hostnames).

Label distribution target:
    critical ~10%  high ~29%  medium ~42%  low ~20%

Usage (from repo root):
    python ai/datasets/generate_alerts_dataset.py
"""
from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path
from typing import Any, Callable

SEED = 42
random.seed(SEED)

# ── scoring constants (mirrors production baseline) ────────────────────────

LABEL_RANGES: dict[str, tuple[float, float]] = {
    "critical": (85, 100),
    "high": (70, 84.9),
    "medium": (45, 69.9),
    "low": (0, 44.9),
}

PRIORITY_THRESHOLDS: list[tuple[float, str]] = [
    (85, "critical"),
    (70, "high"),
    (45, "medium"),
    (0, "low"),
]

DET_W: dict[str, int] = {
    "unauthorized_user_creation": 28,
    "file_integrity": 24,
    "brute_force": 18,
    "port_scan": 12,
    "normal": 0,
}
SRC_W: dict[str, int] = {"wazuh": 6, "suricata": 3}
CRIT_W: dict[str, int] = {"critical": 18, "high": 12, "medium": 6, "low": 0}
IC_W: dict[str, int] = {"critical": 12, "important": 7, "minor": 3, "none": 0}

FIELDS: list[str] = [
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
]


# ── scoring ────────────────────────────────────────────────────────────────

def calc_score(d: dict[str, Any]) -> float:
    score = 10.0
    score += DET_W.get(d["threat_type"], 0)
    score += SRC_W.get(d["source_type"], 0)
    score += CRIT_W.get(d["asset_criticality"], 0)
    score += IC_W.get(d["integrity_change"], 0)
    score += min(d["wazuh_rule_level"] * 0.9, 13)
    score += min(d["suricata_severity"] * 2.5, 10)
    score += min(d["failed_logins_1m"] * 0.4, 6)
    score += min(d["failed_logins_5m"] * 0.2, 6)
    score += min(d["unique_ports_1m"] * 0.15, 6)
    score += min(d["repeated_event_count"] * 0.4, 5)
    score += min(d["time_window_density"] * 0.3, 4)
    score += min(d["recurrence_history"] * 0.5, 3)
    if d["privileged_account"]:
        score += 5
    if d["blacklisted_ip"]:
        score += 6
    if d["off_hours"]:
        score += 3
    if d["new_user_created"]:
        score += 4
    return min(score, 100.0)


def get_label(score: float) -> str:
    for threshold, label in PRIORITY_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


# ── row builder ────────────────────────────────────────────────────────────

def mk(
    src: str,
    det: str,
    crit: str,
    ic: str,
    wrl: int,
    suri: int,
    fl1: int,
    fl5: int,
    up: int,
    rc: int,
    td: int,
    rh: int,
    nu: int,
    oh: int,
    priv: int,
    bl: int,
) -> dict[str, Any]:
    return {
        "source_type": src,
        "threat_type": det,
        "asset_criticality": crit,
        "integrity_change": ic,
        "wazuh_rule_level": wrl,
        "suricata_severity": suri,
        "failed_logins_1m": fl1,
        "failed_logins_5m": fl5,
        "unique_ports_1m": up,
        "repeated_event_count": rc,
        "time_window_density": td,
        "recurrence_history": rh,
        "new_user_created": nu,
        "off_hours": oh,
        "privileged_account": priv,
        "blacklisted_ip": bl,
    }


def ri(lo: int, hi: int) -> int:
    return random.randint(lo, hi)


def ch(options: list) -> Any:  # noqa: ANN401
    return random.choice(options)


# ── per-(detection × priority) generators ─────────────────────────────────

# brute_force
def bf_critical() -> dict[str, Any]:
    return mk(
        "wazuh", "brute_force",
        ch(["critical", "critical", "high"]), "none",
        ri(12, 15), 0, ri(30, 60), ri(50, 120), ri(0, 2),
        ri(8, 20), ri(6, 10), ri(4, 8),
        0, ch([0, 1]), 1, ch([0, 0, 1]),
    )


def bf_high() -> dict[str, Any]:
    return mk(
        "wazuh", "brute_force",
        ch(["high", "high", "critical", "medium"]), "none",
        ri(8, 13), 0, ri(10, 35), ri(18, 60), ri(0, 2),
        ri(4, 10), ri(3, 7), ri(1, 4),
        0, ch([0, 1]), ch([0, 1]), ch([0, 1]),
    )


def bf_medium() -> dict[str, Any]:
    return mk(
        "wazuh", "brute_force",
        ch(["medium", "medium", "low", "high"]), "none",
        ri(5, 9), 0, ri(3, 12), ri(5, 20), ri(0, 2),
        ri(2, 6), ri(1, 4), ri(0, 2),
        0, ch([0, 1]), 0, 0,
    )


def bf_low() -> dict[str, Any]:
    return mk(
        "wazuh", "brute_force",
        ch(["low", "low", "medium"]), "none",
        ri(1, 6), 0, ri(1, 5), ri(1, 8), 0,
        ri(1, 3), ri(0, 2), 0,
        0, 0, 0, 0,
    )


# file_integrity
def fi_critical() -> dict[str, Any]:
    return mk(
        "wazuh", "file_integrity",
        ch(["critical", "critical", "high"]),
        ch(["critical", "critical", "important"]),
        ri(11, 15), 0, 0, 0, 0,
        ri(3, 8), ri(3, 6), ri(4, 8),
        0, ch([0, 1]), ch([0, 1]), 0,
    )


def fi_high() -> dict[str, Any]:
    return mk(
        "wazuh", "file_integrity",
        ch(["high", "high", "critical", "medium"]),
        ch(["important", "important", "critical"]),
        ri(7, 12), 0, 0, 0, 0,
        ri(2, 5), ri(2, 4), ri(1, 4),
        0, ch([0, 1]), 0, 0,
    )


def fi_medium() -> dict[str, Any]:
    return mk(
        "wazuh", "file_integrity",
        ch(["medium", "medium", "low", "high"]),
        ch(["important", "minor", "important"]),
        ri(4, 9), 0, 0, 0, 0,
        ri(1, 3), ri(1, 3), ri(0, 2),
        0, ch([0, 1]), 0, 0,
    )


def fi_low() -> dict[str, Any]:
    return mk(
        "wazuh", "file_integrity",
        ch(["low", "low", "medium"]),
        ch(["minor", "none", "minor"]),
        ri(1, 6), 0, 0, 0, 0,
        ri(1, 2), ri(0, 2), 0,
        0, 0, 0, 0,
    )


# port_scan
def ps_critical() -> dict[str, Any]:
    return mk(
        "suricata", "port_scan",
        ch(["critical", "critical", "high"]), "none",
        0, ch([3, 4]), 0, 0, ri(80, 200),
        ri(15, 40), ri(10, 20), ri(4, 8),
        0, ch([0, 1]), 0, ch([0, 1]),
    )


def ps_high() -> dict[str, Any]:
    return mk(
        "suricata", "port_scan",
        ch(["high", "high", "critical", "medium"]), "none",
        0, ch([2, 3]), 0, 0, ri(25, 90),
        ri(8, 20), ri(6, 12), ri(1, 4),
        0, ch([0, 1]), 0, ch([0, 1]),
    )


def ps_medium() -> dict[str, Any]:
    return mk(
        "suricata", "port_scan",
        ch(["medium", "medium", "low", "high"]), "none",
        0, ch([1, 2]), 0, 0, ri(8, 30),
        ri(3, 10), ri(2, 7), ri(0, 2),
        0, 0, 0, 0,
    )


def ps_low() -> dict[str, Any]:
    return mk(
        "suricata", "port_scan",
        ch(["low", "low", "medium"]), "none",
        0, ch([1, 2]), 0, 0, ri(2, 10),
        ri(1, 5), ri(1, 4), 0,
        0, 0, 0, 0,
    )


# unauthorized_user_creation
def uu_critical() -> dict[str, Any]:
    return mk(
        "wazuh", "unauthorized_user_creation",
        ch(["critical", "critical", "high"]), "none",
        ri(12, 15), 0, 0, 0, 0,
        ri(3, 6), ri(2, 5), ri(4, 8),
        1, ch([0, 1]), 1, ch([0, 1]),
    )


def uu_high() -> dict[str, Any]:
    return mk(
        "wazuh", "unauthorized_user_creation",
        ch(["high", "high", "critical", "medium"]), "none",
        ri(8, 13), 0, 0, 0, 0,
        ri(2, 4), ri(1, 4), ri(1, 4),
        1, ch([0, 1]), ch([0, 1]), ch([0, 1]),
    )


def uu_medium() -> dict[str, Any]:
    return mk(
        "wazuh", "unauthorized_user_creation",
        ch(["medium", "medium", "low", "high"]), "none",
        ri(5, 9), 0, 0, 0, 0,
        ri(1, 3), ri(0, 3), ri(0, 2),
        1, ch([0, 1]), 0, 0,
    )


def uu_low() -> dict[str, Any]:
    return mk(
        "wazuh", "unauthorized_user_creation",
        ch(["low", "low", "medium"]), "none",
        ri(2, 6), 0, 0, 0, 0,
        1, 0, 0,
        1, 0, 0, 0,
    )


# normal traffic noise
def nm_low() -> dict[str, Any]:
    return mk(
        ch(["wazuh", "suricata"]), "normal",
        ch(["low", "low", "medium"]), "none",
        ri(0, 3), ch([0, 1]), ri(0, 2), ri(0, 3), ri(0, 5),
        ri(0, 3), ri(0, 2), 0,
        0, 0, 0, 0,
    )


def nm_medium() -> dict[str, Any]:
    return mk(
        ch(["wazuh", "suricata"]), "normal",
        ch(["medium", "high", "critical"]), "none",
        ri(3, 7), ch([1, 2]), ri(0, 3), ri(0, 5), ri(0, 10),
        ri(1, 4), ri(0, 2), 0,
        ch([0, 1]), ch([0, 1]), 0, 0,
    )


# ── generation plan: (generator_fn, intended_label, row_count) ────────────

PLAN: list[tuple[Callable[[], dict[str, Any]], str, int]] = [
    # brute_force: 2500 rows
    (bf_critical, "critical", 350),
    (bf_high, "high", 700),
    (bf_medium, "medium", 900),
    (bf_low, "low", 550),
    # file_integrity: 2500 rows
    (fi_critical, "critical", 350),
    (fi_high, "high", 700),
    (fi_medium, "medium", 900),
    (fi_low, "low", 550),
    # port_scan: 2500 rows
    (ps_critical, "critical", 300),
    (ps_high, "high", 700),
    (ps_medium, "medium", 1000),
    (ps_low, "low", 500),
    # unauthorized_user_creation: 2000 rows
    (uu_critical, "critical", 300),
    (uu_high, "high", 600),
    (uu_medium, "medium", 750),
    (uu_low, "low", 350),
    # normal traffic noise: 500 rows
    (nm_low, "low", 350),
    (nm_medium, "medium", 150),
]


def gen_row(
    fn: Callable[[], dict[str, Any]],
    intended: str,
    max_tries: int = 500,
) -> dict[str, Any]:
    """Generate a row whose score falls in the intended label bucket."""
    lo, hi = LABEL_RANGES[intended]
    for _ in range(max_tries):
        row = fn()
        score = calc_score(row)
        if lo <= score <= hi:
            if random.random() < 0.06:
                score = max(0.0, min(100.0, score + random.uniform(-5, 5)))
            row["label"] = get_label(score)
            return row
    # Fallback: label whatever score the last attempt produced
    fallback = fn()
    fallback["label"] = get_label(calc_score(fallback))
    return fallback


def build_dataset() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for generator_fn, intended_label, count in PLAN:
        for _ in range(count):
            rows.append(gen_row(generator_fn, intended_label))
    random.shuffle(rows)
    return rows


def print_stats(rows: list[dict[str, Any]]) -> None:
    label_counts = Counter(row["label"] for row in rows)
    det_counts = Counter(row["threat_type"] for row in rows)
    total = len(rows)
    print(f"Total rows        : {total}")
    print("Label distribution:")
    for label in ["critical", "high", "medium", "low"]:
        count = label_counts.get(label, 0)
        print(f"  {label:10s}: {count:5d}  ({count / total * 100:.1f}%)")
    print(f"Threat type dist  : {dict(sorted(det_counts.items()))}")


if __name__ == "__main__":
    output_path = Path(__file__).parent / "alerts_dataset.csv"
    dataset = build_dataset()
    print_stats(dataset)
    with open(output_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(dataset)
    print(f"\nWritten: {output_path}")