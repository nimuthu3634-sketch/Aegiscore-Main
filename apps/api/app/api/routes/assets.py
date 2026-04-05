from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import AssetListResponse
from app.services.assets import list_assets

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=AssetListResponse)
def read_assets(_: CurrentUser, db: DbSession) -> AssetListResponse:
    return list_assets(db)

