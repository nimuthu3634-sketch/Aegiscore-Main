"""AI-direct brute-force IP blocking gates (invoked from scoring after TensorFlow scoring only).

Firewall execution stays in :mod:`app.services.response_automation.adapters`; this module only
evaluates whether the scoring pipeline should queue ``block_ip``.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import DetectionType, IncidentPriority, ScoreMethod
from app.models.normalized_alert import NormalizedAlert
from app.services.scoring.features import extract_source_ip

# Unique rule name used in audit logs and response action details.
AUTOMATION_RULE_ID = "ai_direct_brute_force_block"
REQUIRED_FAILED_LOGINS_5M = 10


# Safely reads numeric values from the saved scoring feature snapshot.
def _snapshot_int(snapshot: dict[str, Any], key: str) -> int:
    raw = snapshot.get(key)
    if raw in (None, ""):
        return 0
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


# Checks whether the alert is suitable for immediate AI-based block_ip automation.
def evaluate_ai_direct_brute_force_block(alert: NormalizedAlert) -> tuple[bool, dict[str, Any]]:
    """Return (all_gates_passed, detail for audits / ``response_actions.details``)."""
    rs = alert.risk_score
    detail: dict[str, Any] = {
        "automation_rule": AUTOMATION_RULE_ID,
        "thresholds": {
            "required_failed_logins_5m": REQUIRED_FAILED_LOGINS_5M,
            "required_detection_type": DetectionType.BRUTE_FORCE.value,
            "required_scoring_method": ScoreMethod.TENSORFLOW_MODEL.value,
            "required_model_tiers": ("high", "critical"),
            "requires_source_ip": True,
        },
        "checks": {},
        "passed": False,
    }
    checks: dict[str, Any] = detail["checks"]

    # A risk score is required before this automation can make a decision.
    if rs is None:
        detail["summary"] = "No risk score; AI-direct brute-force block skipped."
        return False, detail

    checks["detection_type_brute_force"] = alert.detection_type == DetectionType.BRUTE_FORCE
    checks["scoring_method_tensorflow"] = rs.scoring_method == ScoreMethod.TENSORFLOW_MODEL

    # Failed login count and source IP are taken from the model feature snapshot.
    snapshot = rs.feature_snapshot or {}
    failed_5m = _snapshot_int(snapshot, "failed_logins_5m")
    checks["failed_logins_5m"] = failed_5m
    checks["failed_logins_5m_meets_threshold"] = failed_5m >= REQUIRED_FAILED_LOGINS_5M

    ip = (snapshot.get("source_ip") or "").strip() or (extract_source_ip(alert) or "").strip()
    checks["source_ip_present"] = bool(ip)
    detail["resolved_source_ip"] = ip if ip else None

    # The model tier is used to make sure only high-risk predictions trigger blocking.
    exp = rs.explanation or {}
    tier_raw = exp.get("model_priority_tier") or exp.get("predicted_class")
    tier = str(tier_raw).strip().lower() if tier_raw is not None else ""
    detail["model_priority_tier"] = tier or None

    if tier:
        checks["model_tier_high_or_critical"] = tier in ("high", "critical")
    else:
        checks["model_tier_high_or_critical"] = rs.priority_label in (
            IncidentPriority.HIGH,
            IncidentPriority.CRITICAL,
        )

    # All safety gates must pass before the block action can be queued.
    passed = all(
        (
            checks["detection_type_brute_force"],
            checks["scoring_method_tensorflow"],
            checks["model_tier_high_or_critical"],
            checks["failed_logins_5m_meets_threshold"],
            checks["source_ip_present"],
        )
    )
    detail["passed"] = passed
    detail["summary"] = (
        "AI-direct brute-force block gates satisfied."
        if passed
        else "AI-direct brute-force block gates not satisfied."
    )
    return passed, detail
