# AegisCore student note: Repository layer for response action queries and duplicate prevention.

from uuid import UUID

import ipaddress

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.enums import ResponseActionType, ResponseMode, ResponseStatus
from app.models.user import User
from app.schemas.listing import (
    ResponseExecutionStatusLabel,
    ResponseListQuery,
    ResponseListSortField,
    ResponseModeLabel,
    SortDirection,
)


# Groups database queries related to response actions.
class ResponsesRepository:
    # Helper function used internally by this module.
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    # Normalizes IP values so duplicate response actions can be detected.
    def normalize_ip_for_dedup(ip: str | None) -> str | None:
        if not ip or not str(ip).strip():
            return None
        try:
            return str(ipaddress.ip_address(str(ip).strip()))
        except ValueError:
            return None

    # Handles the find existing block ip for alert target logic.
    def find_existing_block_ip_for_alert_target(
        self,
        *,
        normalized_alert_id: UUID,
        target_ip: str,
    ) -> ResponseAction | None:
        """Return an existing block_ip for this alert whose target matches ``target_ip`` (normalized)."""
        want = self.normalize_ip_for_dedup(target_ip)
        if want is None:
            return None

        statement = select(ResponseAction).where(
            ResponseAction.normalized_alert_id == normalized_alert_id,
            ResponseAction.action_type == ResponseActionType.BLOCK_IP.value,
        )
        for row in self.session.scalars(statement):
            if self.normalize_ip_for_dedup(row.target_value) == want:
                return row

        added = getattr(self.session, "added", None)
        if isinstance(added, list):
            for obj in added:
                if not isinstance(obj, ResponseAction):
                    continue
                if obj.normalized_alert_id != normalized_alert_id:
                    continue
                if obj.action_type != ResponseActionType.BLOCK_IP.value:
                    continue
                if self.normalize_ip_for_dedup(obj.target_value) == want:
                    return obj
        return None

    # Returns response actions using frontend filters and pagination.
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

    # Checks whether an automation action already exists.
    def find_existing_automation_action(
        self,
        *,
        incident_id: UUID,
        normalized_alert_id: UUID,
        automation_rule: str,
    ) -> ResponseAction | None:
        statement = select(ResponseAction).where(
            ResponseAction.incident_id == incident_id,
            ResponseAction.normalized_alert_id == normalized_alert_id,
        )
        for row in self.session.scalars(statement):
            if (row.details or {}).get("automation_rule") == automation_rule:
                return row
        added = getattr(self.session, "added", None)
        if isinstance(added, list):
            for obj in added:
                if not isinstance(obj, ResponseAction):
                    continue
                if obj.incident_id != incident_id or obj.normalized_alert_id != normalized_alert_id:
                    continue
                if (obj.details or {}).get("automation_rule") == automation_rule:
                    return obj
        return None

    # Handles the find existing policy block ip for alert logic.
    def find_existing_policy_block_ip_for_alert(
        self,
        *,
        normalized_alert_id: UUID,
    ) -> ResponseAction | None:
        """Any policy-backed block_ip already recorded for this alert (skip duplicate built-in ML block)."""
        statement = (
            select(ResponseAction)
            .where(
                ResponseAction.normalized_alert_id == normalized_alert_id,
                ResponseAction.action_type == ResponseActionType.BLOCK_IP.value,
                ResponseAction.policy_id.is_not(None),
            )
            .limit(1)
        )
        hit = self.session.scalar(statement)
        if hit is not None:
            return hit
        added = getattr(self.session, "added", None)
        if isinstance(added, list):
            for obj in added:
                if not isinstance(obj, ResponseAction):
                    continue
                if (
                    obj.normalized_alert_id == normalized_alert_id
                    and obj.action_type == ResponseActionType.BLOCK_IP.value
                    and obj.policy_id is not None
                ):
                    return obj
        return None

    # Checks whether a policy already created the same action.
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

    # Handles the create logic.
    def create(self, response_action: ResponseAction) -> ResponseAction:
        self.session.add(response_action)
        return response_action
