from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import AssetListResponse
from app.schemas.listing import (
    AssetAgentStatusLabel,
    AssetEnvironmentLabel,
    AssetListQuery,
    AssetListSortField,
    SortDirection,
)
from app.services.assets import list_assets

router = APIRouter(prefix="/assets", tags=["assets"])


def get_asset_list_query(
    search: Annotated[str | None, Query()] = None,
    status: Annotated[AssetAgentStatusLabel | None, Query()] = None,
    criticality: Annotated[
        str | None,
        Query(pattern="^(mission_critical|high|standard|low)$"),
    ] = None,
    operating_system: Annotated[str | None, Query()] = None,
    environment: Annotated[AssetEnvironmentLabel | None, Query()] = None,
    sort_by: Annotated[AssetListSortField, Query()] = AssetListSortField.HOSTNAME,
    sort_direction: Annotated[SortDirection, Query()] = SortDirection.ASC,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> AssetListQuery:
    return AssetListQuery(
        search=search,
        status=status,
        criticality=criticality,
        operating_system=operating_system,
        environment=environment,
        sort_by=sort_by,
        sort_direction=sort_direction,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=AssetListResponse)
def read_assets(
    query: Annotated[AssetListQuery, Depends(get_asset_list_query)],
    _: CurrentUser,
    db: DbSession,
) -> AssetListResponse:
    return list_assets(db, query)
