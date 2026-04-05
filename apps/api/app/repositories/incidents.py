from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User


class IncidentsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_incidents(self) -> list[Incident]:
        statement = (
            select(Incident)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.normalized_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.normalized_alert).selectinload(NormalizedAlert.risk_score),
            )
            .order_by(Incident.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get_incident(self, incident_id: UUID) -> Incident | None:
        statement = (
            select(Incident)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.normalized_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.normalized_alert).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.normalized_alert).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.response_actions)
                .selectinload(ResponseAction.requested_by)
                .selectinload(User.role),
            )
            .where(Incident.id == incident_id)
        )
        return self.session.scalar(statement)

    def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        return incident

