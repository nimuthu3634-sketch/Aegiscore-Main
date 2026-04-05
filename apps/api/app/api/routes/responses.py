from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ResponseActionListResponse
from app.schemas.listing import (
    ResponseExecutionStatusLabel,
    ResponseListQuery,
    ResponseListSortField,
    ResponseModeLabel,
    SortDirection,
)
from app.services.responses import list_response_actions

router = APIRouter(prefix="/responses", tags=["responses"])


def get_response_list_query(
    search: Annotated[str | None, Query()] = None,
    mode: Annotated[ResponseModeLabel | None, Query()] = None,
    execution_status: Annotated[ResponseExecutionStatusLabel | None, Query()] = None,
    action_type: Annotated[str | None, Query()] = None,
    sort_by: Annotated[ResponseListSortField, Query()] = ResponseListSortField.EXECUTED_AT,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.DESC,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> ResponseListQuery:
    return ResponseListQuery(
        search=search,
        mode=mode,
        execution_status=execution_status,
        action_type=action_type,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=ResponseActionListResponse)
def read_responses(
    query: Annotated[ResponseListQuery, Depends(get_response_list_query)],
    _: CurrentUser,
    db: DbSession,
) -> ResponseActionListResponse:
    return list_response_actions(db, query)
