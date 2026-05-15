from sqlalchemy.orm import Session

from app.repositories.assets import AssetsRepository
from app.schemas.common import AssetListResponse
from app.schemas.listing import AssetListQuery, ListMetaResponse
from app.services.serializers import to_asset_summary_response


def list_assets(session: Session, query: AssetListQuery) -> AssetListResponse:
    # Gets asset records from the database using the selected filters and pagination.
    asset_rows, total = AssetsRepository(session).list_assets(query)

    # Calculates pagination details for the frontend asset table.
    total_pages = max(1, (total + query.page_size - 1) // query.page_size)
    page = min(query.page, total_pages)

    return AssetListResponse(
        items=[
            to_asset_summary_response(
                asset,
                recent_alerts_count=recent_alerts_count,
                open_incidents_count=open_incidents_count,
            )
            for asset, recent_alerts_count, open_incidents_count in asset_rows
        ],
        meta=ListMetaResponse(
            page=page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
            sort_by=query.sort_by.value,
            sort_direction=query.sort_direction,
            warnings=[],
        ),
    )