from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.ingestion import (
    IngestionResultResponse,
    SuricataConnectorStatusResponse,
    WazuhConnectorStatusResponse,
)
from app.services.ingestion.service import ingest_suricata_event, ingest_wazuh_event
from app.services.integrations.suricata_connector import get_suricata_connector_status
from app.services.integrations.wazuh_connector import get_wazuh_connector_status

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


@router.get("/wazuh/connector/status", response_model=WazuhConnectorStatusResponse)
def wazuh_connector_status_route(
    current_user: CurrentUser,
    db: DbSession,
) -> WazuhConnectorStatusResponse:
    return get_wazuh_connector_status(db)


@router.get("/suricata/connector/status", response_model=SuricataConnectorStatusResponse)
def suricata_connector_status_route(
    current_user: CurrentUser,
    db: DbSession,
) -> SuricataConnectorStatusResponse:
    return get_suricata_connector_status(db)
