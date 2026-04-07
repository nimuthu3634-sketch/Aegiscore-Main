from uuid import UUID

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.asset import Asset
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.notification_event import NotificationEvent
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User
from app.schemas.listing import (
    IncidentListQuery,
    IncidentListSortField,
    IncidentListStateFilter,
    SortDirection,
)


class IncidentsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_incidents(self, query: IncidentListQuery) -> tuple[list[Incident], int]:
        statement = (
            select(Incident)
            .outerjoin(Incident.primary_alert)
            .outerjoin(Incident.assigned_user)
            .outerjoin(NormalizedAlert.asset)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.primary_alert).selectinload(
                    NormalizedAlert.risk_score
                ),
                selectinload(Incident.primary_alert).selectinload(
                    NormalizedAlert.raw_alert
                ),
                selectinload(Incident.primary_alert).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.asset),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.alerts).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
            )
        )

        conditions = []
        if query.search:
            search_term = f"%{query.search.strip()}%"
            conditions.append(
                or_(
                    cast(Incident.id, String).ilike(search_term),
                    Incident.title.ilike(search_term),
                    Incident.summary.ilike(search_term),
                    User.username.ilike(search_term),
                    User.full_name.ilike(search_term),
                    Asset.hostname.ilike(search_term),
                    cast(NormalizedAlert.detection_type, String).ilike(search_term),
                )
            )

        if query.priority is not None:
            conditions.append(Incident.priority == query.priority.value)

        if query.state == IncidentListStateFilter.NEW:
            conditions.append(Incident.status == IncidentStatus.NEW)
        elif query.state == IncidentListStateFilter.TRIAGED:
            conditions.append(Incident.status == IncidentStatus.TRIAGED)
        elif query.state == IncidentListStateFilter.INVESTIGATING:
            conditions.append(Incident.status == IncidentStatus.INVESTIGATING)
        elif query.state == IncidentListStateFilter.CONTAINED:
            conditions.append(Incident.status == IncidentStatus.CONTAINED)
        elif query.state == IncidentListStateFilter.RESOLVED:
            conditions.append(Incident.status == IncidentStatus.RESOLVED)

        if query.assignee:
            assignee_term = f"%{query.assignee.strip()}%"
            conditions.append(
                or_(User.username.ilike(assignee_term), User.full_name.ilike(assignee_term))
            )

        if query.detection_type is not None:
            conditions.append(NormalizedAlert.detection_type == query.detection_type)

        if conditions:
            statement = statement.where(*conditions)

        priority_rank = case(
            (Incident.priority == "critical", 4),
            (Incident.priority == "high", 3),
            (Incident.priority == "medium", 2),
            else_=1,
        )
        sort_expression = {
            IncidentListSortField.UPDATED_AT: Incident.updated_at,
            IncidentListSortField.CREATED_AT: Incident.created_at,
            IncidentListSortField.PRIORITY: priority_rank,
        }[query.sort_by]
        direction = (
            sort_expression.asc()
            if query.sort_direction == SortDirection.ASC
            else sort_expression.desc()
        )
        statement = statement.order_by(direction, Incident.updated_at.desc())

        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0

        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        page = min(query.page, total_pages)
        offset = (page - 1) * query.page_size
        paged_statement = statement.offset(offset).limit(query.page_size)

        return list(self.session.scalars(paged_statement)), total

    def get_incident(self, incident_id: UUID) -> Incident | None:
        statement = (
            select(Incident)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.primary_alert).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.asset),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.alerts).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
                selectinload(Incident.response_actions)
                .selectinload(ResponseAction.policy),
                selectinload(Incident.response_actions)
                .selectinload(ResponseAction.requested_by)
                .selectinload(User.role),
                selectinload(Incident.notification_events).selectinload(
                    NotificationEvent.response_action
                ),
            )
            .where(Incident.id == incident_id)
        )
        return self.session.scalar(statement)

    def get_incident_detail(self, incident_id: UUID) -> Incident | None:
        statement = (
            select(Incident)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.primary_alert).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.asset),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.alerts).selectinload(
                    NormalizedAlert.response_actions
                ).selectinload(ResponseAction.policy),
                selectinload(Incident.response_actions)
                .selectinload(ResponseAction.policy),
                selectinload(Incident.response_actions)
                .selectinload(ResponseAction.requested_by)
                .selectinload(User.role),
                selectinload(Incident.notification_events).selectinload(
                    NotificationEvent.response_action
                ),
            )
            .where(Incident.id == incident_id)
        )
        return self.session.scalar(statement)

    def create(self, incident: Incident) -> Incident:
        self.session.add(incident)
        return incident
