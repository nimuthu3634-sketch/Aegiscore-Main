from __future__ import annotations

from app.models.enums import IncidentPriority, ScoreMethod
from app.services.scoring.constants import (
    ASSET_CRITICALITY_WEIGHTS,
    DETECTION_TYPE_WEIGHTS,
    MAX_RISK_SCORE,
    MIN_RISK_SCORE,
    PRIORITY_THRESHOLDS,
    SENSITIVE_PORTS,
    SOURCE_TYPE_WEIGHTS,
)
from app.services.scoring.types import (
    AlertRiskFeatures,
    ScoreContribution,
    ScoringResult,
)


def priority_from_score(score: float | int | None):
    normalized_score = int(round(score or 0))
    for minimum, priority in PRIORITY_THRESHOLDS:
        if normalized_score >= minimum:
            return priority
    return PRIORITY_THRESHOLDS[-1][1]


def incident_priority_from_three_class_tier(tier: str) -> IncidentPriority:
    """Legacy 3-class mapping — kept for backward compatibility."""
    key = (tier or "low").strip().lower()
    if key == "medium":
        return IncidentPriority.MEDIUM
    if key == "high":
        return IncidentPriority.HIGH
    return IncidentPriority.LOW


def incident_priority_from_model_tier(tier: str) -> IncidentPriority:
    """Map enterprise 4-class model output to IncidentPriority."""
    key = (tier or "low").strip().lower()
    if key == "critical": return IncidentPriority.CRITICAL
    if key == "high":     return IncidentPriority.HIGH
    if key == "medium":   return IncidentPriority.MEDIUM
    return IncidentPriority.LOW


def score_with_baseline(
    features: AlertRiskFeatures,
    *,
    baseline_version: str,
) -> ScoringResult:
    score = 10
    drivers: list[ScoreContribution] = []

    def add(feature: str, label: str, contribution: int) -> None:
        nonlocal score
        if contribution <= 0:
            return
        score += contribution
        drivers.append(
            ScoreContribution(
                feature=feature,
                label=label,
                contribution=contribution,
            )
        )

    add(
        "detection_type",
        f"Detection type {features.detection_type} elevated priority.",
        DETECTION_TYPE_WEIGHTS.get(features.detection_type, 8),
    )
    add(
        "source_type",
        f"Telemetry source {features.source_type} affected trust weighting.",
        SOURCE_TYPE_WEIGHTS.get(features.source_type, 2),
    )
    add(
        "source_severity",
        f"Source severity {features.source_severity} raised the alert score.",
        min(features.source_severity * 4, 32),
    )
    add(
        "source_rule_level",
        f"Source rule level {features.source_rule_level} increased risk context.",
        min(max(features.source_rule_level - features.source_severity, 0) * 2, 12),
    )
    add(
        "asset_criticality",
        f"Asset criticality {features.asset_criticality} amplified business impact.",
        ASSET_CRITICALITY_WEIGHTS.get(features.asset_criticality, 4),
    )
    add(
        "repeated_event_count",
        f"Repeated event count reached {features.repeated_event_count} in the last 24h.",
        min(max(features.repeated_event_count - 1, 0) * 4, 16),
    )
    add(
        "time_window_density",
        f"Time-window density reached {features.time_window_density} alerts in the last hour.",
        min(max(features.time_window_density - 1, 0) * 3, 12),
    )
    add(
        "repeated_source_ip",
        f"Source IP repetition reached {features.repeated_source_ip} observations.",
        min(max(features.repeated_source_ip - 1, 0) * 3, 12),
    )

    if features.repeated_failed_logins >= 20:
        add(
            "repeated_failed_logins",
            f"Repeated failed logins reached {features.repeated_failed_logins}.",
            12,
        )
    elif features.repeated_failed_logins >= 10:
        add(
            "repeated_failed_logins",
            f"Repeated failed logins reached {features.repeated_failed_logins}.",
            8,
        )
    elif features.repeated_failed_logins >= 5:
        add(
            "repeated_failed_logins",
            f"Repeated failed logins reached {features.repeated_failed_logins}.",
            4,
        )

    add(
        "recurrence_history",
        f"Recurrence history found {features.recurrence_history} similar historical events.",
        min(features.recurrence_history * 2, 10),
    )

    if features.privileged_account_flag:
        add(
            "privileged_account_flag",
            "Privileged or service-account context was observed.",
            12,
        )

    if features.sensitive_file_flag:
        add(
            "sensitive_file_flag",
            "Sensitive file or configuration path was involved.",
            10,
        )

    if features.has_destination_port and features.destination_port in SENSITIVE_PORTS:
        add(
            "destination_port",
            f"Sensitive destination port {features.destination_port} was targeted.",
            4,
        )

    normalized_score = max(MIN_RISK_SCORE, min(MAX_RISK_SCORE, score))
    priority_label = priority_from_score(normalized_score)

    feature_richness = len(drivers)
    confidence = round(min(0.95, 0.58 + feature_richness * 0.04), 2)
    top_drivers = sorted(
        drivers,
        key=lambda item: item.contribution,
        reverse=True,
    )[:5]
    factors = [driver.label for driver in top_drivers]
    reasoning = (
        f"Baseline rules assigned {priority_label.value} priority at "
        f"{normalized_score}/100 using normalized telemetry, recurrence, and asset context."
    )

    explanation = {
        "label": "Deterministic baseline score",
        "summary": (
            f"Alert scored {normalized_score}/100 and was classified as "
            f"{priority_label.value} priority."
        ),
        "rationale": (
            "The baseline engine combines approved detection scope, source severity, "
            "recurrence, asset context, and privileged or sensitive indicators."
        ),
        "factors": factors,
        "drivers": [driver.to_dict() for driver in top_drivers],
        "score": normalized_score,
        "priority_label": priority_label.value,
        "scoring_method": ScoreMethod.BASELINE_RULES.value,
        "baseline_version": baseline_version,
    }

    return ScoringResult(
        score=float(normalized_score),
        confidence=confidence,
        priority_label=priority_label,
        scoring_method=ScoreMethod.BASELINE_RULES,
        reasoning=reasoning,
        explanation=explanation,
        feature_snapshot=features.to_snapshot(),
        baseline_version=baseline_version,
        model_version=None,
    )
