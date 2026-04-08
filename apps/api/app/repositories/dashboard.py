from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import IncidentStatus, ResponseStatus
from app.repositories.dashboard_detection_counts import complete_alerts_by_detection_counts
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.asset import Asset
from app.models.raw_alert import RawAlert


@dataclass
class DashboardMetrics:
    asset_count: int
    raw_alert_count: int
    alert_count: int
    open_incident_count: int
    pending_response_count: int
    average_risk_score: float
    alerts_by_detection: list[tuple[str, int]]


class DashboardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_metrics(self) -> DashboardMetrics:
        asset_count = self.session.scalar(select(func.count(Asset.id))) or 0
        raw_alert_count = self.session.scalar(select(func.count(RawAlert.id))) or 0
        alert_count = self.session.scalar(select(func.count(NormalizedAlert.id))) or 0
        open_incident_count = (
            self.session.scalar(
                select(func.count(Incident.id)).where(
                    Incident.status.notin_(
                        [IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE]
                    )
                )
            )
            or 0
        )
        pending_response_count = (
            self.session.scalar(
                select(func.count(ResponseAction.id)).where(
                    ResponseAction.status.in_(
                        [ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS]
                    )
                )
            )
            or 0
        )
        average_risk_score = (
            self.session.scalar(select(func.avg(RiskScore.score))) or 0.0
        )
        grouped = self.session.execute(
            select(
                NormalizedAlert.detection_type,
                func.count(NormalizedAlert.id),
            ).group_by(NormalizedAlert.detection_type)
        )

        alerts_by_detection = complete_alerts_by_detection_counts(list(grouped.all()))

        return DashboardMetrics(
            asset_count=asset_count,
            raw_alert_count=raw_alert_count,
            alert_count=alert_count,
            open_incident_count=open_incident_count,
            pending_response_count=pending_response_count,
            average_risk_score=float(average_risk_score),
            alerts_by_detection=alerts_by_detection,
        )
