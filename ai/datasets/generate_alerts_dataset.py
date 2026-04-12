"""
Synthetic SOC alert feature rows for academic / prototype alert-prioritization training.

Regenerates `alerts_dataset.csv` with a fixed random seed for reproducibility.
Uses only the Python standard library (no NumPy/Pandas required).

Usage (repo root):
  python ai/datasets/generate_alerts_dataset.py
  python ai/datasets/generate_alerts_dataset.py --rows 2000 --seed 99
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_SEED = 42
DEFAULT_ROWS = 1240
OUTPUT_REL = Path("ai/datasets/alerts_dataset.csv")


def _random_ip(rng: random.Random) -> str:
    return f"10.{rng.randint(0, 254)}.{rng.randint(0, 254)}.{rng.randint(1, 253)}"


def _random_host(rng: random.Random) -> str:
    names = ("web-01", "db-02", "dc01", "srv-app", "mail", "vpn", "file", "api")
    return f"{rng.choice(names)}.corp.local"


def _random_ts(rng: random.Random) -> str:
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    delta = timedelta(seconds=rng.randint(0, 90 * 24 * 3600 - 1))
    return (base + delta).strftime("%Y-%m-%dT%H:%M:%SZ")


def _label_normal(rng: random.Random) -> str:
    x = rng.random()
    if x < 0.88:
        return "Low"
    if x < 0.98:
        return "Medium"
    return "High"


def _label_brute_force(failed_5m: int) -> str:
    if 1 <= failed_5m <= 4:
        return "Low"
    if 5 <= failed_5m <= 9:
        return "Medium"
    return "High"


def _label_port_scan(unique_ports: int) -> str:
    if 5 <= unique_ports <= 9:
        return "Low"
    if 10 <= unique_ports <= 19:
        return "Medium"
    return "High"


def _label_file_integrity(integrity_change: str, off_hours: int, privileged: int) -> str:
    if integrity_change in ("none", "minor"):
        return "Low"
    if integrity_change == "important":
        return "Medium"
    if integrity_change == "critical" and (off_hours == 1 or privileged == 1):
        return "High"
    return "Medium"


def _harmless_username(name: str) -> bool:
    n = name.lower()
    prefixes = ("test_", "guest", "demo_", "readonly_", "svc_deploy")
    if n in ("guest", "nobody"):
        return True
    return any(n.startswith(p) for p in prefixes)


def _label_unauthorized(username: str, privileged: int, off_hours: int, crit: str) -> str:
    if privileged == 1 or (off_hours == 1 and crit in ("high", "critical")):
        return "High"
    if privileged == 0 and (_harmless_username(username) or crit == "low"):
        return "Low"
    return "Medium"


COLUMNS = [
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
]


def build_rows(n_rows: int, seed: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    counts = {
        "normal": int(n_rows * 0.42),
        "brute_force": int(n_rows * 0.22),
        "port_scan": int(n_rows * 0.18),
        "file_integrity": int(n_rows * 0.10),
        "unauthorized_user_creation": int(n_rows * 0.08),
    }
    counts["normal"] += n_rows - sum(counts.values())

    rows: list[dict[str, object]] = []

    crit_choices = ("low", "medium", "high", "critical")
    crit_weights = (0.35, 0.35, 0.2, 0.1)

    def pick_crit() -> str:
        return rng.choices(crit_choices, weights=crit_weights, k=1)[0]

    # --- normal ---
    for _ in range(counts["normal"]):
        label = _label_normal(rng)
        wl = rng.randint(3, 7) if label == "Low" else rng.randint(5, 11)
        rows.append(
            {
                "threat_type": "normal",
                "source_ip": _random_ip(rng),
                "target_host": _random_host(rng),
                "username": rng.choice(["", "alice", "bob", "svc_backup"]),
                "failed_logins_1m": rng.randint(0, 1),
                "failed_logins_5m": rng.randint(0, 2),
                "unique_ports_1m": rng.randint(0, 3),
                "integrity_change": "none",
                "new_user_created": 0,
                "off_hours": rng.randint(0, 1),
                "privileged_account": rng.randint(0, 1),
                "asset_criticality": pick_crit(),
                "wazuh_rule_level": wl,
                "suricata_severity": rng.randint(0, 1),
                "blacklisted_ip": 1 if rng.random() < 0.02 else 0,
                "label": label,
            }
        )

    # --- brute_force ---
    for _ in range(counts["brute_force"]):
        band = rng.choices(["low", "med", "high"], weights=[0.34, 0.33, 0.33], k=1)[0]
        if band == "low":
            f5 = rng.randint(1, 4)
        elif band == "med":
            f5 = rng.randint(5, 9)
        else:
            f5 = rng.randint(10, 39)
        f1 = max(0, min(f5 - rng.randint(0, 3), f5))
        label = _label_brute_force(f5)
        rows.append(
            {
                "threat_type": "brute_force",
                "source_ip": _random_ip(rng),
                "target_host": _random_host(rng),
                "username": rng.choice(["admin", "root", "azureuser", "jdoe"]),
                "failed_logins_1m": f1,
                "failed_logins_5m": f5,
                "unique_ports_1m": rng.randint(0, 2),
                "integrity_change": "none",
                "new_user_created": 0,
                "off_hours": rng.randint(0, 1),
                "privileged_account": rng.randint(0, 1),
                "asset_criticality": rng.choice(crit_choices),
                "wazuh_rule_level": rng.randint(5, 13),
                "suricata_severity": rng.randint(0, 1),
                "blacklisted_ip": 1 if rng.random() < 0.15 else 0,
                "label": label,
            }
        )

    # --- port_scan ---
    for _ in range(counts["port_scan"]):
        band = rng.choices(["low", "med", "high"], weights=[0.34, 0.33, 0.33], k=1)[0]
        if band == "low":
            ports = rng.randint(5, 9)
        elif band == "med":
            ports = rng.randint(10, 19)
        else:
            ports = rng.randint(20, 79)
        label = _label_port_scan(ports)
        rows.append(
            {
                "threat_type": "port_scan",
                "source_ip": _random_ip(rng),
                "target_host": _random_host(rng),
                "username": "",
                "failed_logins_1m": 0,
                "failed_logins_5m": 0,
                "unique_ports_1m": ports,
                "integrity_change": "none",
                "new_user_created": 0,
                "off_hours": rng.randint(0, 1),
                "privileged_account": 0,
                "asset_criticality": rng.choice(crit_choices),
                "wazuh_rule_level": rng.randint(0, 5),
                "suricata_severity": rng.randint(2, 4),
                "blacklisted_ip": 1 if rng.random() < 0.2 else 0,
                "label": label,
            }
        )

    # --- file_integrity ---
    ic_weights = [0.15, 0.35, 0.35, 0.15]
    ic_vals = ("none", "minor", "important", "critical")
    for _ in range(counts["file_integrity"]):
        ic = rng.choices(ic_vals, weights=ic_weights, k=1)[0]
        off_f = rng.randint(0, 1)
        pr_f = rng.randint(0, 1)
        if ic == "critical":
            if rng.random() < 0.55:
                off_f = 1
            if rng.random() < 0.45:
                pr_f = 1
        label = _label_file_integrity(ic, off_f, pr_f)
        rows.append(
            {
                "threat_type": "file_integrity",
                "source_ip": _random_ip(rng),
                "target_host": _random_host(rng),
                "username": rng.choice(["root", "SYSTEM", "deploy"]),
                "failed_logins_1m": 0,
                "failed_logins_5m": 0,
                "unique_ports_1m": 0,
                "integrity_change": ic,
                "new_user_created": 0,
                "off_hours": off_f,
                "privileged_account": pr_f,
                "asset_criticality": rng.choices(
                    ("medium", "high", "critical"), weights=[0.3, 0.4, 0.3], k=1
                )[0],
                "wazuh_rule_level": rng.randint(7, 14),
                "suricata_severity": rng.randint(0, 1),
                "blacklisted_ip": 1 if rng.random() < 0.05 else 0,
                "label": label,
            }
        )

    # --- unauthorized_user_creation ---
    for _ in range(counts["unauthorized_user_creation"]):
        if rng.random() < 0.35:
            user = rng.choice(["test_user1", "guest", "demo_account", "readonly_svc"])
        else:
            user = f"u_{rng.randint(1000, 9999)}"
        pr_u = rng.randint(0, 1)
        off_u = rng.randint(0, 1)
        if rng.random() < 0.25:
            pr_u = 1
        if rng.random() < 0.2:
            off_u = 1
        crit_u = rng.choices(crit_choices, weights=[0.2, 0.3, 0.3, 0.2], k=1)[0]
        label = _label_unauthorized(user, pr_u, off_u, crit_u)
        rows.append(
            {
                "threat_type": "unauthorized_user_creation",
                "source_ip": _random_ip(rng),
                "target_host": _random_host(rng),
                "username": user,
                "failed_logins_1m": 0,
                "failed_logins_5m": 0,
                "unique_ports_1m": 0,
                "integrity_change": "none",
                "new_user_created": 1,
                "off_hours": off_u,
                "privileged_account": pr_u,
                "asset_criticality": crit_u,
                "wazuh_rule_level": rng.randint(8, 14),
                "suricata_severity": 0,
                "blacklisted_ip": 1 if rng.random() < 0.03 else 0,
                "label": label,
            }
        )

    rng.shuffle(rows)
    for r in rows:
        r["timestamp"] = _random_ts(rng)

    ordered: list[dict[str, object]] = []
    for r in rows:
        ordered.append({c: r[c] for c in COLUMNS})
    return ordered


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def summarize(rows: list[dict[str, object]]) -> None:
    threat: dict[str, int] = {}
    labels: dict[str, int] = {}
    for r in rows:
        t = str(r["threat_type"])
        threat[t] = threat.get(t, 0) + 1
        lb = str(r["label"])
        labels[lb] = labels.get(lb, 0) + 1
    print("shape:", (len(rows), len(COLUMNS)))
    print("\nthreat_type counts:")
    for k in sorted(threat):
        print(f"  {k}: {threat[k]}")
    print("\nlabel counts:")
    for k in sorted(labels):
        print(f"  {k}: {labels[k]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic alerts_dataset.csv")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS, help="Total rows (default 1240)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed (default 42)")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV path (default: ai/datasets/alerts_dataset.csv from repo root)",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    out = args.output if args.output is not None else repo_root / OUTPUT_REL

    rows = build_rows(args.rows, args.seed)
    write_csv(out, rows)

    print(f"Wrote {out} (seed={args.seed}, rows={len(rows)})")
    summarize(rows)


if __name__ == "__main__":
    main()
