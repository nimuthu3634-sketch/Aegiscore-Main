from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.schemas.common import IncidentListResponse
from app.schemas.incidents import IncidentDetailResponse
from app.services.serializers import (
    to_incident_detail_response,
    to_incident_summary_response,
)

def list_incidents(session: Session) -> IncidentListResponse:
    incidents = IncidentsRepository(session).list_incidents()
    return IncidentListResponse(
        items=[to_incident_summary_response(incident) for incident in incidents]
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
