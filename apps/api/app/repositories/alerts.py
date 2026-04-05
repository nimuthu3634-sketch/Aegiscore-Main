from uuid import UUID

from datetime import UTC, datetime, timedelta

from sqlalchemy import String, case, cast, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.asset import Asset
from app.models.incident import Incident
from app.models.enums import AlertStatus, IncidentStatus, ResponseStatus
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.response_action import ResponseAction
from app.models.risk_score import RiskScore
from app.models.user import User
from app.schemas.listing import (
    AlertDateRange,
    AlertListQuery,
    AlertListSortField,
    AlertListStatusFilter,
    SortDirection,
)


class AlertsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_alerts(self, query: AlertListQuery) -> tuple[list[NormalizedAlert], int]:
        statement = (
            select(NormalizedAlert)
            .join(NormalizedAlert.raw_alert)
            .outerjoin(NormalizedAlert.asset)
            .outerjoin(NormalizedAlert.risk_score)
            .outerjoin(NormalizedAlert.incident)
            .options(
                selectinload(NormalizedAlert.asset),
                selectinload(NormalizedAlert.raw_alert),
                selectinload(NormalizedAlert.risk_score),
                selectinload(NormalizedAlert.incident).selectinload(Incident.assigned_user),
                selectinload(NormalizedAlert.incident).selectinload(Incident.response_actions),
            )
        )

        conditions = []
        if query.search:
            search_term = f"%{query.search.strip()}%"
            conditions.append(
                or_(
                    cast(NormalizedAlert.id, String).ilike(search_term),
                    NormalizedAlert.title.ilike(search_term),
                    NormalizedAlert.description.ilike(search_term),
                    RawAlert.external_id.ilike(search_term),
                    Asset.hostname.ilike(search_term),
                    Asset.ip_address.ilike(search_term),
                    cast(NormalizedAlert.normalized_payload, String).ilike(search_term),
                    cast(RawAlert.raw_payload, String).ilike(search_term),
                )
            )

        if query.severity is not None:
            if query.severity.value == "critical":
                conditions.append(NormalizedAlert.severity >= 9)
            elif query.severity.value == "high":
                conditions.append(NormalizedAlert.severity.between(7, 8))
            elif query.severity.value == "medium":
                conditions.append(NormalizedAlert.severity.between(4, 6))
            else:
                conditions.append(NormalizedAlert.severity <= 3)

        if query.status == AlertListStatusFilter.NEW:
            conditions.extend(
                [NormalizedAlert.status == AlertStatus.NEW, Incident.id.is_(None)]
            )
        elif query.status == AlertListStatusFilter.TRIAGED:
            conditions.append(Incident.status == IncidentStatus.TRIAGED)
        elif query.status == AlertListStatusFilter.INVESTIGATING:
            conditions.append(
                or_(
                    NormalizedAlert.status == AlertStatus.INVESTIGATING,
                    Incident.status == IncidentStatus.INVESTIGATING,
                )
            )
        elif query.status == AlertListStatusFilter.CONTAINED:
            conditions.append(Incident.status == IncidentStatus.CONTAINED)
        elif query.status == AlertListStatusFilter.RESOLVED:
            conditions.append(
                or_(
                    NormalizedAlert.status == AlertStatus.RESOLVED,
                    Incident.status.in_(
                        [IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE]
                    ),
                )
            )
        elif query.status == AlertListStatusFilter.PENDING_RESPONSE:
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
            conditions.extend([Incident.id.is_not(None), pending_response_exists])

        if query.detection_type is not None:
            conditions.append(NormalizedAlert.detection_type == query.detection_type)

        if query.source_type is not None:
            conditions.append(
                func.lower(NormalizedAlert.source) == query.source_type.value
            )

        if query.asset:
            asset_term = f"%{query.asset.strip()}%"
            conditions.append(
                or_(
                    Asset.hostname.ilike(asset_term),
                    Asset.ip_address.ilike(asset_term),
                    cast(Asset.id, String).ilike(asset_term),
                )
            )

        if query.date_range != AlertDateRange.ALL:
            hours = {"4h": 4, "12h": 12, "24h": 24}[query.date_range.value]
            since = datetime.now(UTC) - timedelta(hours=hours)
            conditions.append(NormalizedAlert.created_at >= since)

        if conditions:
            statement = statement.where(*conditions)

        severity_rank = case(
            (NormalizedAlert.severity >= 9, 4),
            (NormalizedAlert.severity >= 7, 3),
            (NormalizedAlert.severity >= 4, 2),
            else_=1,
        )
        sort_expression = {
            AlertListSortField.TIMESTAMP: NormalizedAlert.created_at,
            AlertListSortField.SEVERITY: severity_rank,
            AlertListSortField.RISK_SCORE: func.coalesce(RiskScore.score, 0),
        }[query.sort_by]
        direction = (
            sort_expression.asc()
            if query.sort_direction == SortDirection.ASC
            else sort_expression.desc()
        )
        statement = statement.order_by(direction, NormalizedAlert.created_at.desc())

        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0

        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        page = min(query.page, total_pages)
        offset = (page - 1) * query.page_size

        paged_statement = statement.offset(offset).limit(query.page_size)
        return list(self.session.scalars(paged_statement)), total

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
