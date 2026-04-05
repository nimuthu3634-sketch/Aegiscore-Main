from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.alerts import AlertDetailResponse
from app.schemas.common import AlertListResponse
from app.schemas.listing import (
    AlertDateRange,
    AlertListQuery,
    AlertListSortField,
    AlertListStatusFilter,
    SortDirection,
    SourceTypeFilter,
)
from app.schemas.alerts import AlertSeverityLabel
from app.models.enums import DetectionType
from app.schemas.workflows import (
    AlertLifecycleResponse,
    AlertLinkIncidentRequest,
    AlertLinkIncidentResponse,
    AnalystNoteCreateRequest,
    AnalystNoteCreateResponse,
)
from app.services.alerts import (
    acknowledge_alert,
    close_alert,
    create_alert_note,
    get_alert_detail,
    link_alert_incident,
    list_alerts,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_list_query(
    search: Annotated[str | None, Query()] = None,
    severity: Annotated[AlertSeverityLabel | None, Query()] = None,
    status: Annotated[AlertListStatusFilter | None, Query()] = None,
    detection_type: Annotated[DetectionType | None, Query()] = None,
    source_type: Annotated[SourceTypeFilter | None, Query()] = None,
    asset: Annotated[str | None, Query()] = None,
    date_range: Annotated[AlertDateRange, Query()] = AlertDateRange.TWENTY_FOUR_HOURS,
    sort_by: Annotated[AlertListSortField, Query()] = AlertListSortField.TIMESTAMP,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AlertListQuery:
    return AlertListQuery(
        search=search,
        severity=severity,
        status=status,
        detection_type=detection_type,
        source_type=source_type,
        asset=asset,
        date_range=date_range,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=AlertListResponse)
def read_alerts(
    query: Annotated[AlertListQuery, Depends(get_alert_list_query)],
    _: CurrentUser,
    db: DbSession,
) -> AlertListResponse:
    return list_alerts(db, query)


@router.get("/{alert_id}", response_model=AlertDetailResponse)
def read_alert(alert_id: UUID, _: CurrentUser, db: DbSession) -> AlertDetailResponse:
    return get_alert_detail(db, alert_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertLifecycleResponse)
def acknowledge_alert_route(
    alert_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AlertLifecycleResponse:
    return acknowledge_alert(db, alert_id, current_user)


@router.post("/{alert_id}/close", response_model=AlertLifecycleResponse)
def close_alert_route(
    alert_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AlertLifecycleResponse:
    return close_alert(db, alert_id, current_user)


@router.post("/{alert_id}/link-incident", response_model=AlertLinkIncidentResponse)
def link_alert_incident_route(
    alert_id: UUID,
    payload: AlertLinkIncidentRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AlertLinkIncidentResponse:
    return link_alert_incident(db, alert_id, payload, current_user)


@router.post("/{alert_id}/notes", response_model=AnalystNoteCreateResponse)
def create_alert_note_route(
    alert_id: UUID,
    payload: AnalystNoteCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> AnalystNoteCreateResponse:
    return create_alert_note(db, alert_id, payload.content, current_user)
