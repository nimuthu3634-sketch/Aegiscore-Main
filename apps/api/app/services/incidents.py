from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.schemas.common import IncidentListResponse
from app.schemas.incidents import IncidentDetailResponse
from app.schemas.listing import IncidentListQuery, ListMetaResponse
from app.services.serializers import (
    to_incident_detail_response,
    to_incident_summary_response,
)

def list_incidents(session: Session, query: IncidentListQuery) -> IncidentListResponse:
    incidents, total = IncidentsRepository(session).list_incidents(query)
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)
    warnings: list[str] = []
    if query.state and query.state.value == "contained":
        warnings.append(
            "state=contained is not supported by the current incident state model and was not applied."
        )

    return IncidentListResponse(
        items=[to_incident_summary_response(incident) for incident in incidents],
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


def get_incident(session: Session, incident_id: UUID) -> IncidentDetailResponse:
    incident = IncidentsRepository(session).get_incident_detail(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    audit_logs_repository = AuditLogsRepository(session)
    audit_logs = audit_logs_repository.list_for_entity("incident", str(incident.id))
    audit_logs.extend(
        audit_logs_repository.list_for_entity(
            "alert", str(incident.normalized_alert.id)
        )
    )

    return to_incident_detail_response(incident, audit_logs)
