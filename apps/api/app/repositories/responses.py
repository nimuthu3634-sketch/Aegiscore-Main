from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User


class ResponsesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_response_actions(self) -> list[ResponseAction]:
        statement = (
            select(ResponseAction)
            .options(
                selectinload(ResponseAction.requested_by).selectinload(User.role),
                selectinload(ResponseAction.incident)
                .selectinload(Incident.normalized_alert)
                .selectinload(NormalizedAlert.asset),
            )
            .order_by(ResponseAction.created_at.desc())
        )
        return list(self.session.scalars(statement))

    def create(self, response_action: ResponseAction) -> ResponseAction:
        self.session.add(response_action)
        return response_action

