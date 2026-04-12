"""
Built-in automated response for **TensorFlow-scored brute_force** alerts only.

All conditions must pass before any block_ip action is queued (see
:func:`ml_brute_force_auto_block_evaluation`).
"""

from __future__ import annotations

from typing import Any

from app.models.enums import DetectionType, IncidentPriority, ScoreMethod
from app.models.normalized_alert import NormalizedAlert
from app.services.scoring.features import extract_source_ip

AUTOMATION_RULE_ID = "ml_brute_force_auto_block_v1"
REQUIRED_FAILED_LOGINS_5M = 10


def _snapshot_int(snapshot: dict[str, Any], key: str) -> int:
    raw = snapshot.get(key)
    if raw in (None, ""):
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def ml_brute_force_auto_block_evaluation(alert: NormalizedAlert) -> tuple[bool, dict[str, Any]]:
    """Return (all_preconditions_met, detail_payload for audits / API / dashboard)."""
    rs = alert.risk_score
    detail: dict[str, Any] = {
        "automation_rule": AUTOMATION_RULE_ID,
        "thresholds": {
            "required_failed_logins_5m": REQUIRED_FAILED_LOGINS_5M,
            "required_detection_type": DetectionType.BRUTE_FORCE.value,
            "required_ai_priority": IncidentPriority.HIGH.value,
            "required_scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
            "requires_source_ip": True,
        },
        "checks": {},
        "passed": False,
    }
    checks: dict[str, Any] = detail["checks"]

    if rs is None:
        detail["summary"] = "No risk score present; ML brute-force automation skipped."
        return False, detail

    checks["detection_type_brute_force"] = alert.detection_type == DetectionType.BRUTE_FORCE
    checks["scoring_method_tensorflow"] = rs.scoring_method == ScoreMethod.TENSORFLOW_MODEL
    checks["ai_priority_high"] = rs.priority_label == IncidentPriority.HIGH

    snapshot = rs.feature_snapshot or {}
    failed_5m = _snapshot_int(snapshot, "failed_logins_5m")
    checks["failed_logins_5m"] = failed_5m
    checks["failed_logins_5m_meets_threshold"] = failed_5m >= REQUIRED_FAILED_LOGINS_5M

    ip = (snapshot.get("source_ip") or "").strip() or (extract_source_ip(alert) or "").strip()
    checks["source_ip_present"] = bool(ip)
    detail["resolved_source_ip"] = ip if ip else None

    exp = rs.explanation or {}
    tier_raw = exp.get("model_priority_tier") or exp.get("predicted_class")
    tier = str(tier_raw).strip().lower() if tier_raw is not None else ""
    detail["model_priority_tier"] = tier or None
    if "model_priority_tier" in exp or "predicted_class" in exp:
        checks["model_tier_high"] = tier == "high"
    else:
        checks["model_tier_high"] = checks["ai_priority_high"]

    passed = all(
        (
            checks["detection_type_brute_force"],
            checks["scoring_method_tensorflow"],
            checks["ai_priority_high"],
            checks["failed_logins_5m_meets_threshold"],
            checks["source_ip_present"],
            checks["model_tier_high"],
        )
    )
    detail["passed"] = passed
    detail["summary"] = (
        "All ML brute-force auto-block preconditions satisfied."
        if passed
        else "ML brute-force auto-block preconditions not satisfied; no block executed."
    )
    return passed, detail
