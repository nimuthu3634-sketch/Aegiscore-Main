from uuid import UUID

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.enums import ResponseMode, ResponseStatus
from app.models.user import User
from app.schemas.listing import (
    ResponseExecutionStatusLabel,
    ResponseListQuery,
    ResponseListSortField,
    ResponseModeLabel,
    SortDirection,
)


class ResponsesRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_response_actions(
        self, query: ResponseListQuery
    ) -> tuple[list[ResponseAction], int]:
        details_text = cast(ResponseAction.details, String)
        executed_at_expression = func.coalesce(
            ResponseAction.executed_at, ResponseAction.created_at
        )

        statement = (
            select(ResponseAction)
            .join(ResponseAction.incident)
            .outerjoin(ResponseAction.requested_by)
            .options(
                selectinload(ResponseAction.requested_by).selectinload(User.role),
                selectinload(ResponseAction.policy),
                selectinload(ResponseAction.notification_events),
                selectinload(ResponseAction.incident)
                .selectinload(Incident.primary_alert)
                .selectinload(NormalizedAlert.asset),
            )
        )

        conditions = []
        if query.search:
            search_term = f"%{query.search.strip()}%"
            conditions.append(
                or_(
                    cast(ResponseAction.id, String).ilike(search_term),
                    ResponseAction.action_type.ilike(search_term),
                    Incident.title.ilike(search_term),
                    details_text.ilike(search_term),
                )
            )

        if query.mode == ResponseModeLabel.DRY_RUN:
            conditions.append(ResponseAction.mode == ResponseMode.DRY_RUN)
        elif query.mode == ResponseModeLabel.LIVE:
            conditions.append(ResponseAction.mode == ResponseMode.LIVE)

        if query.execution_status == ResponseExecutionStatusLabel.SUCCEEDED:
            conditions.append(ResponseAction.status == ResponseStatus.COMPLETED)
        elif query.execution_status == ResponseExecutionStatusLabel.WARNING:
            conditions.append(ResponseAction.status == ResponseStatus.WARNING)
        elif query.execution_status == ResponseExecutionStatusLabel.FAILED:
            conditions.append(ResponseAction.status == ResponseStatus.FAILED)
        elif query.execution_status == ResponseExecutionStatusLabel.PENDING:
            conditions.append(
                ResponseAction.status.in_(
                    [ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS]
                )
            )

        if query.action_type:
            conditions.append(ResponseAction.action_type == query.action_type)

        if conditions:
            statement = statement.where(*conditions)

        status_rank = case(
            (ResponseAction.status.in_([ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS]), 1),
            (ResponseAction.status == ResponseStatus.WARNING, 2),
            (ResponseAction.status == ResponseStatus.COMPLETED, 3),
            (ResponseAction.status == ResponseStatus.FAILED, 4),
            else_=5,
        )
        sort_expression = {
            ResponseListSortField.EXECUTED_AT: executed_at_expression,
            ResponseListSortField.STATUS: status_rank,
        }[query.sort_by]
        direction = (
            sort_expression.asc()
            if query.sort_direction == SortDirection.ASC
            else sort_expression.desc()
        )
        statement = statement.order_by(direction, executed_at_expression.desc())

        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0

        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        page = min(query.page, total_pages)
        offset = (page - 1) * query.page_size
        paged_statement = statement.offset(offset).limit(query.page_size)
        return list(self.session.scalars(paged_statement)), total

    def find_existing_policy_action(
        self,
        *,
        policy_id: UUID,
        incident_id: UUID,
        normalized_alert_id: UUID | None,
    ) -> ResponseAction | None:
        statement = select(ResponseAction).where(
            ResponseAction.policy_id == policy_id,
            ResponseAction.incident_id == incident_id,
        )
        if normalized_alert_id is None:
            statement = statement.where(ResponseAction.normalized_alert_id.is_(None))
        else:
            statement = statement.where(
                ResponseAction.normalized_alert_id == normalized_alert_id
            )
        return self.session.scalar(statement)

    def create(self, response_action: ResponseAction) -> ResponseAction:
        self.session.add(response_action)
        return response_action
