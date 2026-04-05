from datetime import UTC, datetime, timedelta

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.enums import IncidentStatus
from app.models.incident import Incident
from app.models.normalized_alert import NormalizedAlert
from app.schemas.listing import (
    AssetAgentStatusLabel,
    AssetListQuery,
    AssetListSortField,
    SortDirection,
)


class AssetsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_assets(
        self, query: AssetListQuery
    ) -> tuple[list[tuple[Asset, int, int]], int]:
        recent_alerts_subquery = (
            select(
                NormalizedAlert.asset_id.label("asset_id"),
                func.count(NormalizedAlert.id).label("recent_alerts_count"),
            )
            .group_by(NormalizedAlert.asset_id)
            .subquery()
        )
        open_incidents_subquery = (
            select(
                NormalizedAlert.asset_id.label("asset_id"),
                func.count(Incident.id).label("open_incidents_count"),
            )
            .join(Incident, Incident.id == NormalizedAlert.incident_id)
            .where(
                Incident.status.notin_(
                    [IncidentStatus.RESOLVED, IncidentStatus.FALSE_POSITIVE]
                )
            )
            .group_by(NormalizedAlert.asset_id)
            .subquery()
        )

        recent_alerts_count = func.coalesce(
            recent_alerts_subquery.c.recent_alerts_count, 0
        )
        open_incidents_count = func.coalesce(
            open_incidents_subquery.c.open_incidents_count, 0
        )

        statement = (
            select(Asset, recent_alerts_count, open_incidents_count)
            .outerjoin(recent_alerts_subquery, recent_alerts_subquery.c.asset_id == Asset.id)
            .outerjoin(
                open_incidents_subquery, open_incidents_subquery.c.asset_id == Asset.id
            )
        )

        conditions = []
        if query.search:
            search_term = f"%{query.search.strip()}%"
            conditions.append(
                or_(
                    cast(Asset.id, String).ilike(search_term),
                    Asset.hostname.ilike(search_term),
                    Asset.ip_address.ilike(search_term),
                    Asset.operating_system.ilike(search_term),
                )
            )

        if query.status is not None:
            online_threshold = datetime.now(UTC) - timedelta(minutes=30)
            degraded_threshold = datetime.now(UTC) - timedelta(hours=2)
            if query.status == AssetAgentStatusLabel.ONLINE:
                conditions.append(Asset.updated_at >= online_threshold)
            elif query.status == AssetAgentStatusLabel.DEGRADED:
                conditions.extend(
                    [Asset.updated_at < online_threshold, Asset.updated_at >= degraded_threshold]
                )
            else:
                conditions.append(Asset.updated_at < degraded_threshold)

        if query.criticality is not None:
            criticality_map = {
                "mission_critical": "critical",
                "high": "high",
                "standard": "medium",
                "low": "low",
            }
            conditions.append(Asset.criticality == criticality_map[query.criticality])

        if query.operating_system:
            conditions.append(Asset.operating_system.ilike(f"%{query.operating_system.strip()}%"))

        if query.environment is not None:
            if query.environment.value == "office":
                conditions.append(
                    or_(Asset.hostname.ilike("%branch%"), Asset.hostname.ilike("%office%"))
                )
            elif query.environment.value == "remote":
                conditions.append(
                    or_(
                        Asset.hostname.ilike("%edge%"),
                        Asset.hostname.ilike("%warehouse%"),
                        Asset.hostname.ilike("%vpn%"),
                        Asset.hostname.ilike("%remote%"),
                    )
                )
            else:
                conditions.append(
                    ~or_(
                        Asset.hostname.ilike("%branch%"),
                        Asset.hostname.ilike("%office%"),
                        Asset.hostname.ilike("%edge%"),
                        Asset.hostname.ilike("%warehouse%"),
                        Asset.hostname.ilike("%vpn%"),
                        Asset.hostname.ilike("%remote%"),
                    )
                )

        if conditions:
            statement = statement.where(*conditions)

        sort_expression = {
            AssetListSortField.HOSTNAME: Asset.hostname,
            AssetListSortField.LAST_SEEN: Asset.updated_at,
            AssetListSortField.RECENT_ALERTS: recent_alerts_count,
        }[query.sort_by]
        direction = (
            sort_expression.asc()
            if query.sort_direction == SortDirection.ASC
            else sort_expression.desc()
        )
        statement = statement.order_by(direction, Asset.hostname.asc())

        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0

        total_pages = max(1, (total + query.page_size - 1) // query.page_size)
        page = min(query.page, total_pages)
        offset = (page - 1) * query.page_size
        paged_statement = statement.offset(offset).limit(query.page_size)
        return list(self.session.execute(paged_statement).all()), total

    def create(self, asset: Asset) -> Asset:
        self.session.add(asset)
        return asset
