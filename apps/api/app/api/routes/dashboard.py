from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_dashboard_summary

# Routes used to load dashboard overview data.
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def read_dashboard_summary(_: CurrentUser, db: DbSession) -> DashboardSummaryResponse:
    # Returns the main summary values shown on the dashboard.
    return get_dashboard_summary(db)