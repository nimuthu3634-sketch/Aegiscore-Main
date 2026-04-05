from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.alerts import AlertsRepository
from app.schemas.alerts import AlertDetailResponse
from app.schemas.common import AlertListResponse, AlertSummaryResponse
from app.services.serializers import to_alert_detail_response, to_alert_summary_response


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


def get_alert_detail(session: Session, alert_id: UUID) -> AlertDetailResponse:
    alert = AlertsRepository(session).get_alert_detail(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    audit_logs_repository = AuditLogsRepository(session)
    audit_logs = audit_logs_repository.list_for_entity("alert", str(alert.id))

    if alert.incident is not None:
        audit_logs.extend(
            audit_logs_repository.list_for_entity("incident", str(alert.incident.id))
        )

    return to_alert_detail_response(alert, audit_logs)
