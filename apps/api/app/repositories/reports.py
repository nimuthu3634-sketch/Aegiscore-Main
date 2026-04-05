from datetime import datetime

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.asset import Asset
from app.models.enums import AlertStatus, IncidentStatus, ResponseMode, ResponseStatus
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User
from app.schemas.listing import (
    AlertListStatusFilter,
    AlertSeverityLabel,
    IncidentListStateFilter,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
)
from app.schemas.reports import (
    AlertReportExportQuery,
    IncidentReportExportQuery,
    ReportSummaryQuery,
    ResponseReportExportQuery,
)


class ReportsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _base_alert_statement(self):
        return (
            select(NormalizedAlert)
            .join(NormalizedAlert.raw_alert)
            .outerjoin(NormalizedAlert.asset)
            .outerjoin(NormalizedAlert.risk_score)
            .outerjoin(NormalizedAlert.incident)
            .options(
                selectinload(NormalizedAlert.asset),
                selectinload(NormalizedAlert.raw_alert),
                selectinload(NormalizedAlert.risk_score),
                selectinload(NormalizedAlert.response_actions).selectinload(
                    ResponseAction.policy
                ),
                selectinload(NormalizedAlert.incident).selectinload(Incident.assigned_user),
                selectinload(NormalizedAlert.incident)
                .selectinload(Incident.response_actions)
                .selectinload(ResponseAction.policy),
            )
        )

    def _apply_alert_status_filter(self, statement, status: AlertListStatusFilter | None):
        if status is None:
            return statement

        if status == AlertListStatusFilter.NEW:
            return statement.where(
                NormalizedAlert.status == AlertStatus.NEW,
                Incident.id.is_(None),
            )
        if status == AlertListStatusFilter.TRIAGED:
            return statement.where(Incident.status == IncidentStatus.TRIAGED)
        if status == AlertListStatusFilter.INVESTIGATING:
            return statement.where(
                or_(
                    NormalizedAlert.status == AlertStatus.INVESTIGATING,
                    Incident.status == IncidentStatus.INVESTIGATING,
                )
            )
        if status == AlertListStatusFilter.CONTAINED:
            return statement.where(Incident.status == IncidentStatus.CONTAINED)
        if status == AlertListStatusFilter.RESOLVED:
            return statement.where(
                or_(
                    NormalizedAlert.status == AlertStatus.RESOLVED,
                    Incident.status.in_(
                        [IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE]
                    ),
                )
            )
        if status == AlertListStatusFilter.PENDING_RESPONSE:
            pending_response_exists = (
                select(ResponseAction.id)
                .where(
                    ResponseAction.incident_id == Incident.id,
                    ResponseAction.status.in_(
                        [ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS]
                    ),
                )
                .exists()
            )
            return statement.where(Incident.id.is_not(None), pending_response_exists)

        return statement

    def list_alerts_for_summary(
        self,
        query: ReportSummaryQuery,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[NormalizedAlert]:
        statement = self._base_alert_statement().where(
            NormalizedAlert.created_at >= window_start,
            NormalizedAlert.created_at <= window_end,
        )
        if query.detection_type is not None:
            statement = statement.where(
                NormalizedAlert.detection_type == query.detection_type
            )
        if query.source_type is not None:
            statement = statement.where(
                func.lower(NormalizedAlert.source) == query.source_type.value
            )
        statement = statement.order_by(NormalizedAlert.created_at.asc())
        return list(self.session.execute(statement).scalars().unique().all())

    def list_alerts_for_export(
        self,
        query: AlertReportExportQuery,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[NormalizedAlert]:
        statement = self._base_alert_statement().where(
            NormalizedAlert.created_at >= window_start,
            NormalizedAlert.created_at <= window_end,
        )

        if query.detection_type is not None:
            statement = statement.where(
                NormalizedAlert.detection_type == query.detection_type
            )
        if query.source_type is not None:
            statement = statement.where(
                func.lower(NormalizedAlert.source) == query.source_type.value
            )
        if query.severity is not None:
            if query.severity == AlertSeverityLabel.CRITICAL:
                statement = statement.where(NormalizedAlert.severity >= 9)
            elif query.severity == AlertSeverityLabel.HIGH:
                statement = statement.where(NormalizedAlert.severity.between(7, 8))
            elif query.severity == AlertSeverityLabel.MEDIUM:
                statement = statement.where(NormalizedAlert.severity.between(4, 6))
            else:
                statement = statement.where(NormalizedAlert.severity <= 3)
        if query.asset:
            asset_term = f"%{query.asset.strip()}%"
            statement = statement.where(
                or_(
                    Asset.hostname.ilike(asset_term),
                    Asset.ip_address.ilike(asset_term),
                    cast(Asset.id, String).ilike(asset_term),
                )
            )

        statement = self._apply_alert_status_filter(statement, query.status)
        statement = statement.order_by(NormalizedAlert.created_at.desc())
        return list(self.session.execute(statement).scalars().unique().all())

    def list_incidents_for_export(
        self,
        query: IncidentReportExportQuery,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[Incident]:
        statement = (
            select(Incident)
            .outerjoin(Incident.alerts)
            .outerjoin(Incident.assigned_user)
            .outerjoin(Asset, NormalizedAlert.asset_id == Asset.id)
            .options(
                selectinload(Incident.assigned_user).selectinload(User.role),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.asset),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.primary_alert).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.asset),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.risk_score),
                selectinload(Incident.alerts).selectinload(NormalizedAlert.raw_alert),
                selectinload(Incident.response_actions).selectinload(ResponseAction.policy),
            )
            .where(
                Incident.updated_at >= window_start,
                Incident.updated_at <= window_end,
            )
        )

        if query.priority is not None:
            statement = statement.where(Incident.priority == query.priority.value)
        if query.state == IncidentListStateFilter.NEW:
            statement = statement.where(Incident.status == IncidentStatus.NEW)
        elif query.state == IncidentListStateFilter.TRIAGED:
            statement = statement.where(Incident.status == IncidentStatus.TRIAGED)
        elif query.state == IncidentListStateFilter.INVESTIGATING:
            statement = statement.where(Incident.status == IncidentStatus.INVESTIGATING)
        elif query.state == IncidentListStateFilter.CONTAINED:
            statement = statement.where(Incident.status == IncidentStatus.CONTAINED)
        elif query.state == IncidentListStateFilter.RESOLVED:
            statement = statement.where(Incident.status == IncidentStatus.RESOLVED)
        if query.assignee:
            assignee_term = f"%{query.assignee.strip()}%"
            statement = statement.where(
                or_(
                    User.username.ilike(assignee_term),
                    User.full_name.ilike(assignee_term),
                )
            )
        if query.detection_type is not None:
            statement = statement.where(
                NormalizedAlert.detection_type == query.detection_type
            )

        statement = statement.order_by(Incident.updated_at.desc()).distinct()
        return list(self.session.execute(statement).scalars().unique().all())

    def list_responses_for_export(
        self,
        query: ResponseReportExportQuery,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ResponseAction]:
        executed_at_expression = func.coalesce(
            ResponseAction.executed_at,
            ResponseAction.created_at,
        )

        statement = (
            select(ResponseAction)
            .join(ResponseAction.incident)
            .outerjoin(ResponseAction.requested_by)
            .outerjoin(ResponseAction.policy)
            .options(
                selectinload(ResponseAction.requested_by).selectinload(User.role),
                selectinload(ResponseAction.policy),
                selectinload(ResponseAction.incident)
                .selectinload(Incident.primary_alert)
                .selectinload(NormalizedAlert.asset),
                selectinload(ResponseAction.normalized_alert)
                .selectinload(NormalizedAlert.asset),
            )
            .where(
                executed_at_expression >= window_start,
                executed_at_expression <= window_end,
            )
        )

        if query.mode == ResponseModeLabel.DRY_RUN:
            statement = statement.where(ResponseAction.mode == ResponseMode.DRY_RUN)
        elif query.mode == ResponseModeLabel.LIVE:
            statement = statement.where(ResponseAction.mode == ResponseMode.LIVE)

        if query.execution_status == ResponseExecutionStatusLabel.SUCCEEDED:
            statement = statement.where(ResponseAction.status == ResponseStatus.COMPLETED)
        elif query.execution_status == ResponseExecutionStatusLabel.WARNING:
            statement = statement.where(ResponseAction.status == ResponseStatus.WARNING)
        elif query.execution_status == ResponseExecutionStatusLabel.FAILED:
            statement = statement.where(ResponseAction.status == ResponseStatus.FAILED)
        elif query.execution_status == ResponseExecutionStatusLabel.PENDING:
            statement = statement.where(
                ResponseAction.status.in_(
                    [ResponseStatus.QUEUED, ResponseStatus.IN_PROGRESS]
                )
            )

        if query.action_type:
            action_term = query.action_type.strip()
            if action_term:
                statement = statement.where(ResponseAction.action_type == action_term)

        statement = statement.order_by(
            executed_at_expression.desc(),
            ResponseAction.created_at.desc(),
        )
        return list(self.session.execute(statement).scalars().unique().all())
