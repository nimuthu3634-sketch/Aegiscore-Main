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


def score_alert(
    session: Session,
    alert: NormalizedAlert,
) -> RiskScore:
    settings = get_settings()
    features = extract_alert_features(session, alert)

    strategy = settings.scoring_strategy.lower().strip()
    if strategy == "model":
        try:
            pipeline, metadata = load_priority_model(
                model_path=settings.scoring_model_path,
                metadata_path=settings.scoring_model_metadata_path,
            )
            result = score_with_model(
                features=features,
                pipeline=pipeline,
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

    risk_score = RiskScoresRepository(session).upsert_for_alert(alert, result)
    session.flush()

    evaluate_alert_policies(session, alert)

    if alert.incident is not None:
        refresh_incident_priority(alert.incident)
        evaluate_incident_policies(session, alert.incident)
    else:
        evaluate_incident_policies_for_alert(session, alert)

    return risk_score


def persist_and_score_alert(
    session: Session,
    raw_alert: RawAlert,
    normalized_alert: NormalizedAlert,
) -> NormalizedAlert:
    raw_alert.normalized_alert = normalized_alert
    session.add(raw_alert)
    session.add(normalized_alert)
    session.flush()
    score_alert(session, normalized_alert)
    return normalized_alert
