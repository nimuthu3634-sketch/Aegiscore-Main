from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import IncidentListResponse
from app.schemas.incidents import IncidentDetailResponse
from app.services.incidents import get_incident, list_incidents

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
def read_incidents(_: CurrentUser, db: DbSession) -> IncidentListResponse:
    return list_incidents(db)


@router.get("/{incident_id}", response_model=IncidentDetailResponse)
def read_incident(
    incident_id: UUID,
    _: CurrentUser,
    db: DbSession,
) -> IncidentDetailResponse:
    return get_incident(db, incident_id)
