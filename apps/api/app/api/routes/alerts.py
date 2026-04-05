from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import AlertListResponse, AlertSummaryResponse
from app.services.alerts import get_alert, list_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
def read_alerts(_: CurrentUser, db: DbSession) -> AlertListResponse:
    return list_alerts(db)


@router.get("/{alert_id}", response_model=AlertSummaryResponse)
def read_alert(alert_id: UUID, _: CurrentUser, db: DbSession) -> AlertSummaryResponse:
    return get_alert(db, alert_id)

