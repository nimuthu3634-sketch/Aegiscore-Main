from sqlalchemy.orm import Session

from app.repositories.assets import AssetsRepository
from app.schemas.common import AssetListResponse
from app.services.serializers import to_asset_summary_response


def list_assets(session: Session) -> AssetListResponse:
    assets = AssetsRepository(session).list_assets()
    return AssetListResponse(items=[to_asset_summary_response(asset) for asset in assets])

