from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.alerts import AlertsRepository
from app.schemas.common import AlertListResponse, AlertSummaryResponse
from app.services.serializers import to_alert_summary_response


def list_alerts(session: Session) -> AlertListResponse:
    alerts = AlertsRepository(session).list_alerts()
    return AlertListResponse(items=[to_alert_summary_response(alert) for alert in alerts])


def get_alert(session: Session, alert_id: UUID) -> AlertSummaryResponse:
    alert = AlertsRepository(session).get_alert(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return to_alert_summary_response(alert)

