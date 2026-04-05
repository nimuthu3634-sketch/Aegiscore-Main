from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def read_dashboard_summary(_: CurrentUser, db: DbSession) -> DashboardSummaryResponse:
    return get_dashboard_summary(db)

