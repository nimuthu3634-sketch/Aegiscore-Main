# Main scoring service that chooses baseline scoring or TensorFlow model scoring.
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.risk_score import RiskScore
from app.repositories.risk_scores import RiskScoresRepository
from app.services.response_automation.execution import (
    evaluate_alert_policies,
    evaluate_incident_policies,
    evaluate_incident_policies_for_alert,
    execute_ai_direct_block_if_required,
)
from app.services.scoring.baseline import score_with_baseline
from app.services.scoring.features import extract_alert_features
from app.services.scoring.ml import (
    ModelArtifactUnavailableError,
    load_priority_model,
    score_with_model,
)
from app.services.scoring.rollup import (
    build_incident_priority_summary,
    incident_rollup_score,
    refresh_incident_priority,
)

__all__ = [
    "build_incident_priority_summary",
    "incident_rollup_score",
    "persist_and_score_alert",
    "refresh_incident_priority",
    "score_alert",
]


# Scores one normalized alert and then evaluates response automation rules.
def score_alert(
    session: Session,
    alert: NormalizedAlert,
) -> RiskScore:
    """Score a normalized alert (baseline rules or TensorFlow, with safe fallback).

    Connectors and parsers set ``detection_type`` / threat context; the trainable
    ``alert_prioritization_v1`` model only emits **low / medium / high** priority tiers.
    """
    settings = get_settings()
    features = extract_alert_features(session, alert)

    # The scoring strategy can use TensorFlow or the deterministic baseline fallback.
    strategy = settings.scoring_strategy.lower().strip()
    if strategy == "model":
        try:
            model, metadata = load_priority_model(
                model_path=settings.scoring_model_path,
                metadata_path=settings.scoring_model_metadata_path,
            )
            result = score_with_model(
                features=features,
                model=model,
                metadata=metadata,
            )
        except ModelArtifactUnavailableError as exc:
            result = score_with_baseline(
                features,
                baseline_version=settings.scoring_baseline_version,
            )
            result.explanation["fallback_reason"] = str(exc)
    else:
        result = score_with_baseline(
            features,
            baseline_version=settings.scoring_baseline_version,
        )

    # Store the latest score so alerts and incidents can use it immediately.
    risk_score = RiskScoresRepository(session).upsert_for_alert(alert, result)
    session.flush()

    # AI-direct block_ip runs immediately after TensorFlow-backed scores are persisted (gated by env).
    execute_ai_direct_block_if_required(session, alert)

    # Policy automation + legacy built-in ML brute-force auto-block read ``alert.risk_score``.
    evaluate_alert_policies(session, alert)

    if alert.incident is not None:
        refresh_incident_priority(alert.incident)
        evaluate_incident_policies(session, alert.incident)
    else:
        evaluate_incident_policies_for_alert(session, alert)

    return risk_score


# Saves a raw/normalized alert pair and immediately calculates its risk score.
def persist_and_score_alert(
    session: Session,
    raw_alert: RawAlert,
    normalized_alert: NormalizedAlert,
) -> NormalizedAlert:
    # Link the raw event and normalized alert before saving them.
    raw_alert.normalized_alert = normalized_alert
    session.add(raw_alert)
    session.add(normalized_alert)
    session.flush()
    score_alert(session, normalized_alert)
    return normalized_alert
