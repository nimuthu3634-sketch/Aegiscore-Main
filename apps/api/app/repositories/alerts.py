from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User


class AlertsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_alerts(self) -> list[NormalizedAlert]:
        statement = (
            select(NormalizedAlert)
            .options(
                selectinload(NormalizedAlert.asset),
                selectinload(NormalizedAlert.raw_alert),
                selectinload(NormalizedAlert.risk_score),
                selectinload(NormalizedAlert.incident).selectinload(Incident.assigned_user),
            )
            .order_by(NormalizedAlert.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def get_alert(self, alert_id: UUID) -> NormalizedAlert | None:
        statement = (
            select(NormalizedAlert)
            .options(
                selectinload(NormalizedAlert.asset),
                selectinload(NormalizedAlert.raw_alert),
                selectinload(NormalizedAlert.risk_score),
                selectinload(NormalizedAlert.incident).selectinload(Incident.assigned_user),
            )
            .where(NormalizedAlert.id == alert_id)
        )
        return self.session.scalar(statement)

    def get_alert_detail(self, alert_id: UUID) -> NormalizedAlert | None:
        statement = (
            select(NormalizedAlert)
            .options(
                selectinload(NormalizedAlert.asset),
                selectinload(NormalizedAlert.raw_alert),
                selectinload(NormalizedAlert.risk_score),
                selectinload(NormalizedAlert.incident)
                .selectinload(Incident.assigned_user)
                .selectinload(User.role),
                selectinload(NormalizedAlert.incident)
                .selectinload(Incident.response_actions)
                .selectinload(ResponseAction.requested_by)
                .selectinload(User.role),
            )
            .where(NormalizedAlert.id == alert_id)
        )
        return self.session.scalar(statement)

    def create_raw_and_normalized(self, raw_alert, normalized_alert) -> None:
        self.session.add(raw_alert)
        self.session.add(normalized_alert)
