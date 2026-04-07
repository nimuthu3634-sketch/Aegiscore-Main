from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analyst_note import AnalystNote
from app.models.audit_log import AuditLog
from app.models.enums import AlertStatus, IncidentStatus, NoteTargetType
from app.models.user import User
from app.repositories.analyst_notes import AnalystNotesRepository
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.incidents import IncidentsRepository
from app.schemas.common import IncidentListResponse
from app.schemas.incidents import IncidentDetailResponse
from app.schemas.listing import IncidentListQuery, ListMetaResponse
from app.schemas.workflows import (
    AnalystNoteCreateResponse,
    IncidentTransitionRequest,
    IncidentTransitionResponse,
)
from app.services.serializers import (
    to_incident_detail_response,
    to_incident_summary_response,
    to_analyst_note_response,
)
from app.services.response_automation.execution import evaluate_incident_policies
from app.services.notifications.service import notify_for_incident_state
from app.services.workflows import resolve_incident_transition


def list_incidents(session: Session, query: IncidentListQuery) -> IncidentListResponse:
    incidents, total = IncidentsRepository(session).list_incidents(query)
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)

    return IncidentListResponse(
        items=[to_incident_summary_response(incident) for incident in incidents],
        meta=ListMetaResponse(
            page=page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
            sort_by=query.sort_by.value,
            sort_direction=query.sort_direction,
            warnings=[],
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
    audit_logs_by_id = {
        str(audit_log.id): audit_log
        for audit_log in audit_logs_repository.list_for_entity("incident", str(incident.id))
    }
    for linked_alert in incident.alerts:
        for audit_log in audit_logs_repository.list_for_entity("alert", str(linked_alert.id)):
            audit_logs_by_id[str(audit_log.id)] = audit_log
    for response_action in incident.response_actions:
        for audit_log in audit_logs_repository.list_for_entity(
            "response",
            str(response_action.id),
        ):
            audit_logs_by_id[str(audit_log.id)] = audit_log
    for notification_event in incident.notification_events:
        for audit_log in audit_logs_repository.list_for_entity(
            "notification",
            str(notification_event.id),
        ):
            audit_logs_by_id[str(audit_log.id)] = audit_log

    analyst_notes = AnalystNotesRepository(session).list_for_target(
        NoteTargetType.INCIDENT,
        incident.id,
    )

    return to_incident_detail_response(
        incident,
        list(audit_logs_by_id.values()),
        analyst_notes,
    )


def _get_incident_for_workflow(session: Session, incident_id: UUID):
    incident = IncidentsRepository(session).get_incident_detail(incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident


def _create_audit_log(
    session: Session,
    *,
    actor: User,
    entity_type: str,
    entity_id: str,
    action: str,
    details: dict,
) -> None:
    AuditLogsRepository(session).create(
        AuditLog(
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details,
        )
    )


def transition_incident(
    session: Session,
    incident_id: UUID,
    payload: IncidentTransitionRequest,
    actor: User,
) -> IncidentTransitionResponse:
    incident = _get_incident_for_workflow(session, incident_id)
    previous_state = incident.status
    target_state = resolve_incident_transition(incident.status, payload.action)

    incident.status = target_state
    if incident.assigned_user is None:
        incident.assigned_user = actor

    alert_target_status: AlertStatus | None = None
    if target_state in {IncidentStatus.INVESTIGATING, IncidentStatus.CONTAINED}:
        alert_target_status = AlertStatus.INVESTIGATING
    elif target_state in {IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE}:
        alert_target_status = AlertStatus.RESOLVED

    if alert_target_status is not None:
        for linked_alert in incident.alerts:
            if linked_alert.status == alert_target_status:
                continue
            previous_alert_status = linked_alert.status
            linked_alert.status = alert_target_status
            _create_audit_log(
                session,
                actor=actor,
                entity_type="alert",
                entity_id=str(linked_alert.id),
                action="alert.status.synced_from_incident",
                details={
                    "incident_id": str(incident.id),
                    "previous_status": previous_alert_status.value,
                    "current_status": alert_target_status.value,
                    "summary": (
                        f"Alert status synced from incident transition to "
                        f"{target_state.value}."
                    ),
                },
            )

    _create_audit_log(
        session,
        actor=actor,
        entity_type="incident",
        entity_id=str(incident.id),
        action="incident.transition",
        details={
            "action": payload.action.value,
            "previous_state": previous_state.value,
            "current_state": target_state.value,
            "summary": (
                f"Incident moved from {previous_state.value} to {target_state.value}."
            ),
        },
    )
    evaluate_incident_policies(session, incident)
    notify_for_incident_state(
        session,
        incident=incident,
        previous_state=previous_state.value,
    )
    session.commit()

    return IncidentTransitionResponse(
        incident_id=incident.id,
        previous_state=previous_state,
        current_state=target_state,
        message=f"Incident transitioned to {target_state.value}.",
    )


def create_incident_note(
    session: Session,
    incident_id: UUID,
    content: str,
    actor: User,
) -> AnalystNoteCreateResponse:
    incident = _get_incident_for_workflow(session, incident_id)
    normalized_content = content.strip()
    if not normalized_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Note content cannot be empty.",
        )

    note = AnalystNotesRepository(session).create(
        AnalystNote(
            target_type=NoteTargetType.INCIDENT,
            target_id=incident.id,
            author=actor,
            content=normalized_content,
        )
    )
    session.flush()
    _create_audit_log(
        session,
        actor=actor,
        entity_type="incident",
        entity_id=str(incident.id),
        action="incident.note.created",
        details={
            "note_id": str(note.id),
            "content": normalized_content,
            "summary": "Analyst note added to incident.",
        },
    )
    session.commit()

    return AnalystNoteCreateResponse(
        note=to_analyst_note_response(note),
        message="Incident note saved successfully.",
    )
