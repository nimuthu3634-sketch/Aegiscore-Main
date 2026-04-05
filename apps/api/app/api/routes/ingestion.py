from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.ingestion import IngestionResultResponse
from app.services.ingestion.service import ingest_suricata_event, ingest_wazuh_event

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/wazuh/events", response_model=IngestionResultResponse)
def ingest_wazuh_event_route(
    payload: dict[str, Any],
    current_user: CurrentUser,
    db: DbSession,
) -> IngestionResultResponse:
    return ingest_wazuh_event(db, payload, actor=current_user)


@router.post("/suricata/events", response_model=IngestionResultResponse)
def ingest_suricata_event_route(
    payload: dict[str, Any],
    current_user: CurrentUser,
    db: DbSession,
) -> IngestionResultResponse:
    return ingest_suricata_event(db, payload, actor=current_user)
