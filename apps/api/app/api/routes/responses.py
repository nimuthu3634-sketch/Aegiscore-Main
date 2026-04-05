from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ResponseActionListResponse
from app.services.responses import list_response_actions

router = APIRouter(prefix="/responses", tags=["responses"])


@router.get("", response_model=ResponseActionListResponse)
def read_responses(_: CurrentUser, db: DbSession) -> ResponseActionListResponse:
    return list_response_actions(db)

