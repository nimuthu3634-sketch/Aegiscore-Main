from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.analyst_note import AnalystNote
from app.models.audit_log import AuditLog
from app.models.enums import (
    AlertStatus,
    IncidentPriority,
    IncidentStatus,
    NoteTargetType,
)
from app.models.incident import Incident
from app.models.user import User
from app.repositories.analyst_notes import AnalystNotesRepository
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.alerts import AlertsRepository
from app.repositories.incidents import IncidentsRepository
from app.schemas.alerts import AlertDetailResponse
from app.schemas.common import AlertListResponse, AlertSummaryResponse
from app.schemas.listing import AlertListQuery, ListMetaResponse
from app.schemas.workflows import (
    AlertLifecycleResponse,
    AlertLinkIncidentRequest,
    AlertLinkIncidentResponse,
    AnalystNoteCreateResponse,
)
from app.services.serializers import (
    to_alert_detail_response,
    to_alert_summary_response,
    to_analyst_note_response,
)
from app.services.scoring.baseline import priority_from_score
from app.services.scoring.service import refresh_incident_priority


def list_alerts(session: Session, query: AlertListQuery) -> AlertListResponse:
    alerts, total = AlertsRepository(session).list_alerts(query)
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)

    return AlertListResponse(
        items=[to_alert_summary_response(alert) for alert in alerts],
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

    analyst_notes = AnalystNotesRepository(session).list_for_target(
        NoteTargetType.ALERT,
        alert.id,
    )

    return to_alert_detail_response(alert, audit_logs, analyst_notes)


def _priority_from_alert(alert) -> IncidentPriority:
    if alert.risk_score and alert.risk_score.priority_label is not None:
        return alert.risk_score.priority_label
    if alert.risk_score:
        return priority_from_score(alert.risk_score.score)

    if alert.severity >= 9:
        return IncidentPriority.CRITICAL
    if alert.severity >= 7:
        return IncidentPriority.HIGH
    if alert.severity >= 4:
        return IncidentPriority.MEDIUM
    return IncidentPriority.LOW


def _linked_alerts(incident: Incident) -> list:
    return list(incident.alerts)


def _select_replacement_primary_alert(
    incident: Incident,
    *,
    exclude_alert_id: UUID | None = None,
):
    candidates = [
        linked_alert
        for linked_alert in _linked_alerts(incident)
        if exclude_alert_id is None or linked_alert.id != exclude_alert_id
    ]
    if not candidates:
        return None

    active_candidates = [
        linked_alert
        for linked_alert in candidates
        if linked_alert.status != AlertStatus.RESOLVED
    ]
    selection_pool = active_candidates or candidates
    return sorted(
        selection_pool,
        key=lambda linked_alert: (
            linked_alert.severity,
            linked_alert.created_at,
            str(linked_alert.id),
        ),
        reverse=True,
    )[0]


def _get_alert_for_workflow(session: Session, alert_id: UUID):
    alert = AlertsRepository(session).get_alert_detail(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    return alert


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


def acknowledge_alert(
    session: Session,
    alert_id: UUID,
    actor: User,
) -> AlertLifecycleResponse:
    alert = _get_alert_for_workflow(session, alert_id)
    previous_status = alert.status.value

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved alerts cannot be acknowledged.",
        )

    if alert.status == AlertStatus.INVESTIGATING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert is already acknowledged and under investigation.",
        )

    alert.status = AlertStatus.INVESTIGATING
    _create_audit_log(
        session,
        actor=actor,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.acknowledged",
        details={
            "previous_status": previous_status,
            "current_status": alert.status.value,
            "summary": "Alert acknowledged for analyst investigation.",
        },
    )
    session.commit()

    return AlertLifecycleResponse(
        alert_id=alert.id,
        previous_status=previous_status,
        current_status=alert.status.value,
        linked_incident_id=alert.incident.id if alert.incident else None,
        message="Alert acknowledged and moved into investigation.",
    )


def close_alert(
    session: Session,
    alert_id: UUID,
    actor: User,
) -> AlertLifecycleResponse:
    alert = _get_alert_for_workflow(session, alert_id)
    incident = alert.incident
    previous_status = alert.status.value

    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert is already closed.",
        )

    alert.status = AlertStatus.RESOLVED
    _create_audit_log(
        session,
        actor=actor,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.closed",
        details={
            "previous_status": previous_status,
            "current_status": alert.status.value,
            "summary": "Alert closed by analyst action.",
        },
    )

    if incident and incident.primary_alert_id == alert.id:
        replacement_primary = _select_replacement_primary_alert(
            incident,
            exclude_alert_id=alert.id,
        )
        if replacement_primary is not None:
            incident.primary_alert = replacement_primary
            _create_audit_log(
                session,
                actor=actor,
                entity_type="incident",
                entity_id=str(incident.id),
                action="incident.primary_alert.updated",
                details={
                    "previous_primary_alert_id": str(alert.id),
                    "current_primary_alert_id": str(replacement_primary.id),
                    "summary": "Incident primary alert was rotated after alert closure.",
                },
            )

    if incident and incident.status not in {
        IncidentStatus.RESOLVED,
        IncidentStatus.FALSE_POSITIVE,
    }:
        has_active_alerts = any(
            linked_alert.status != AlertStatus.RESOLVED
            for linked_alert in _linked_alerts(incident)
        )
        if not has_active_alerts:
            previous_incident_state = incident.status.value
            incident.status = IncidentStatus.RESOLVED
            _create_audit_log(
                session,
                actor=actor,
                entity_type="incident",
                entity_id=str(incident.id),
                action="incident.transition",
                details={
                    "action": "resolve",
                    "previous_state": previous_incident_state,
                    "current_state": incident.status.value,
                    "summary": (
                        "Incident resolved automatically because all linked alerts "
                        "have been closed."
                    ),
                },
            )

    session.commit()

    return AlertLifecycleResponse(
        alert_id=alert.id,
        previous_status=previous_status,
        current_status=alert.status.value,
        linked_incident_id=incident.id if incident else None,
        message="Alert closed successfully.",
    )


def link_alert_incident(
    session: Session,
    alert_id: UUID,
    payload: AlertLinkIncidentRequest,
    actor: User,
) -> AlertLinkIncidentResponse:
    alert = _get_alert_for_workflow(session, alert_id)
    if alert.status == AlertStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Closed alerts cannot be linked to an incident.",
        )

    if alert.incident is not None:
        if payload.incident_id and alert.incident.id == payload.incident_id:
            detail = "Alert is already linked to the requested incident."
        else:
            detail = "Alert is already linked to an incident."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )

    incidents_repository = IncidentsRepository(session)

    if payload.incident_id is not None:
        incident = incidents_repository.get_incident_detail(payload.incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )
        if incident.status in {IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Terminal incidents cannot accept additional linked alerts.",
            )
        link_mode = "existing"
        creation_message = "Alert linked into an existing incident."
    else:
        incident = incidents_repository.create(
            Incident(
                assigned_user=actor,
                title=payload.title or alert.title,
                summary=payload.summary
                or alert.description
                or f"Incident created from {alert.detection_type.value} alert.",
                status=IncidentStatus.TRIAGED,
                priority=_priority_from_alert(alert),
            )
        )
        session.flush()
        _create_audit_log(
            session,
            actor=actor,
            entity_type="incident",
            entity_id=str(incident.id),
            action="incident.created",
            details={
                "alert_id": str(alert.id),
                "primary_alert_id": str(alert.id),
                "priority": incident.priority.value,
                "state": incident.status.value,
                "summary": "Incident created from alert workflow linkage.",
            },
        )
        link_mode = "new"
        creation_message = "Alert linked into a new incident."

    alert.incident = incident
    if incident.primary_alert is None:
        incident.primary_alert = alert
    refresh_incident_priority(incident)

    linked_alerts_count = len(_linked_alerts(incident))
    _create_audit_log(
        session,
        actor=actor,
        entity_type="incident",
        entity_id=str(incident.id),
        action="incident.alert_linked",
        details={
            "alert_id": str(alert.id),
            "link_mode": link_mode,
            "linked_alerts_count": linked_alerts_count,
            "summary": "Alert linked into incident investigation scope.",
        },
    )
    _create_audit_log(
        session,
        actor=actor,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.linked_incident",
        details={
            "incident_id": str(incident.id),
            "link_mode": link_mode,
            "linked_alerts_count": linked_alerts_count,
            "summary": creation_message,
        },
    )
    session.commit()

    return AlertLinkIncidentResponse(
        incident_id=incident.id,
        title=incident.title,
        state=incident.status,
        priority=incident.priority,
        linked_alerts_count=linked_alerts_count,
        message=creation_message,
    )


def create_alert_note(
    session: Session,
    alert_id: UUID,
    content: str,
    actor: User,
) -> AnalystNoteCreateResponse:
    alert = _get_alert_for_workflow(session, alert_id)
    normalized_content = content.strip()
    if not normalized_content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Note content cannot be empty.",
        )

    note = AnalystNotesRepository(session).create(
        AnalystNote(
            target_type=NoteTargetType.ALERT,
            target_id=alert.id,
            author=actor,
            content=normalized_content,
        )
    )
    session.flush()
    _create_audit_log(
        session,
        actor=actor,
        entity_type="alert",
        entity_id=str(alert.id),
        action="alert.note.created",
        details={
            "note_id": str(note.id),
            "content": normalized_content,
            "summary": "Analyst note added to alert.",
        },
    )
    session.commit()

    return AnalystNoteCreateResponse(
        note=to_analyst_note_response(note),
        message="Alert note saved successfully.",
    )
