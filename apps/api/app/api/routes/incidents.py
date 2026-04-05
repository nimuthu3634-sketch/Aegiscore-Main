from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.models.enums import DetectionType
from app.schemas.common import IncidentListResponse
from app.schemas.incidents import IncidentDetailResponse
from app.schemas.listing import (
    IncidentListQuery,
    IncidentListSortField,
    IncidentListStateFilter,
    SortDirection,
)
from app.schemas.alerts import AlertSeverityLabel
from app.services.incidents import get_incident, list_incidents

router = APIRouter(prefix="/incidents", tags=["incidents"])


def get_incident_list_query(
    search: Annotated[str | None, Query()] = None,
    priority: Annotated[AlertSeverityLabel | None, Query()] = None,
    state: Annotated[IncidentListStateFilter | None, Query()] = None,
    assignee: Annotated[str | None, Query()] = None,
    detection_type: Annotated[DetectionType | None, Query()] = None,
    sort_by: Annotated[IncidentListSortField, Query()] = IncidentListSortField.UPDATED_AT,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> IncidentListQuery:
    return IncidentListQuery(
        search=search,
        priority=priority,
        state=state,
        assignee=assignee,
        detection_type=detection_type,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=IncidentListResponse)
def read_incidents(
    query: Annotated[IncidentListQuery, Depends(get_incident_list_query)],
    _: CurrentUser,
    db: DbSession,
) -> IncidentListResponse:
    return list_incidents(db, query)


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def read_incident(
    incident_id: UUID,
    _: CurrentUser,
    db: DbSession,
) -> IncidentDetailResponse:
    return get_incident(db, incident_id)
