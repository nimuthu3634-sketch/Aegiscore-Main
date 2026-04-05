from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.alerts import AlertsRepository
from app.schemas.alerts import AlertDetailResponse
from app.schemas.common import AlertListResponse, AlertSummaryResponse
from app.schemas.listing import AlertListQuery, ListMetaResponse
from app.services.serializers import to_alert_detail_response, to_alert_summary_response


def list_alerts(session: Session, query: AlertListQuery) -> AlertListResponse:
    alerts, total = AlertsRepository(session).list_alerts(query)
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)
    warnings: list[str] = []
    if query.status and query.status.value == "contained":
        warnings.append(
            "status=contained is not supported by alert workflow state yet and was not applied."
        )

    return AlertListResponse(
        items=[to_alert_summary_response(alert) for alert in alerts],
        meta=ListMetaResponse(
            page=page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
            sort_by=query.sort_by.value,
            sort_direction=query.sort_direction,
            warnings=warnings,
        ),
    )


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
