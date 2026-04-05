from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.schemas.common import IncidentDetailResponse, IncidentListResponse
from app.services.serializers import (
    to_audit_log_response,
    to_incident_summary_response,
    to_response_action_reference_response,
)

def list_incidents(session: Session) -> IncidentListResponse:
    incidents = IncidentsRepository(session).list_incidents()
    return IncidentListResponse(
        items=[to_incident_summary_response(incident) for incident in incidents]
    )


def get_incident(session: Session, incident_id: UUID) -> IncidentDetailResponse:
    incident = IncidentsRepository(session).get_incident(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    audit_logs = AuditLogsRepository(session).list_for_entity("incident", str(incident.id))
    summary = to_incident_summary_response(incident)

    return IncidentDetailResponse(
        **summary.model_dump(),
        response_actions=[
            to_response_action_reference_response(action)
            for action in incident.response_actions
        ],
        audit_logs=[to_audit_log_response(log) for log in audit_logs],
    )
