from sqlalchemy.orm import Session

from app.repositories.dashboard import DashboardRepository
from app.schemas.dashboard import DashboardSummaryResponse, DetectionCountResponse


def get_dashboard_summary(session: Session) -> DashboardSummaryResponse:
    metrics = DashboardRepository(session).get_metrics()
    return DashboardSummaryResponse(
        asset_count=metrics.asset_count,
        raw_alert_count=metrics.raw_alert_count,
        alert_count=metrics.alert_count,
        open_incident_count=metrics.open_incident_count,
        pending_response_count=metrics.pending_response_count,
        average_risk_score=metrics.average_risk_score,
        alerts_by_detection=[
            DetectionCountResponse(detection_type=detection_type, total=total)
            for detection_type, total in metrics.alerts_by_detection
        ],
    )
