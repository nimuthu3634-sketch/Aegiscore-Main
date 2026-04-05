from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.normalized_alert import NormalizedAlert
from app.models.risk_score import RiskScore
from app.services.scoring.types import ScoringResult


class RiskScoresRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_for_alert(
        self,
        alert: NormalizedAlert,
        result: ScoringResult,
    ) -> RiskScore:
        risk_score = alert.risk_score or RiskScore(normalized_alert=alert)
        risk_score.score = float(result.score)
        risk_score.confidence = result.confidence
        risk_score.priority_label = result.priority_label
        risk_score.scoring_method = result.scoring_method
        risk_score.baseline_version = result.baseline_version
        risk_score.model_version = result.model_version
        risk_score.reasoning = result.reasoning
        risk_score.explanation = result.explanation
        risk_score.feature_snapshot = result.feature_snapshot
        risk_score.calculated_at = datetime.now(UTC)
        self.session.add(risk_score)
        return risk_score
