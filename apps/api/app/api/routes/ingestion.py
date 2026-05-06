from typing import Any

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.schemas.ingestion import (
    IngestionResultResponse,
    SuricataConnectorStatusResponse,
    WazuhConnectorStatusResponse,
)
from app.services.ingestion.service import ingest_suricata_event, ingest_wazuh_event
from app.services.integrations.suricata_connector import get_suricata_connector_status
from app.services.integrations.wazuh_connector import get_wazuh_connector_status
from app.services.integrations.wazuh_indexer_connector import fetch_latest_wazuh_indexer_alerts

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/wazuh/events", response_model=IngestionResultResponse)
def ingest_wazuh_event_route(
    payload: dict[str, Any],
    current_user: AdminUser,
    db: DbSession,
) -> IngestionResultResponse:
    return ingest_wazuh_event(db, payload, actor=current_user)


@router.post("/suricata/events", response_model=IngestionResultResponse)
def ingest_suricata_event_route(
    payload: dict[str, Any],
    current_user: AdminUser,
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

@router.get("/wazuh/indexer/test")
def wazuh_indexer_test_route(
    current_user: CurrentUser,
) -> dict[str, Any]:
    alerts = fetch_latest_wazuh_indexer_alerts(limit=5)
    return {
        "count": len(alerts),
        "alerts": alerts,
    }


@router.post("/wazuh/indexer/sync")
def wazuh_indexer_sync_route(
    current_user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    alerts = fetch_latest_wazuh_indexer_alerts(limit=50)

    ingested = 0
    failed = 0
    errors = []

    for alert in alerts:
        try:
            ingest_wazuh_event(db, alert, actor=current_user)
            ingested += 1
        except Exception as exc:
            failed += 1
            errors.append(str(exc))

    return {
        "fetched": len(alerts),
        "ingested": ingested,
        "failed": failed,
        "errors": errors[:5],
    }

# --- Wazuh live agent status sync imports ---
from datetime import UTC as _UTC, datetime as _datetime
import requests as _requests
import urllib3 as _urllib3
from sqlalchemy import func as _func, select as _select

from app.core.config import get_settings as _get_settings
from app.models.asset import Asset as _Asset

_urllib3.disable_warnings(_urllib3.exceptions.InsecureRequestWarning)


@router.post("/wazuh/agents/sync")
def wazuh_agents_sync_route(
    current_user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    settings = _get_settings()
    base_url = settings.wazuh_base_url.rstrip("/")
    auth_response = _requests.get(
        f"{base_url}/security/user/authenticate?raw=true",
        auth=(settings.wazuh_username, settings.wazuh_password),
        verify=settings.wazuh_verify_tls,
        timeout=10,
    )
    auth_response.raise_for_status()
    token = auth_response.text.strip()

    agents_response = _requests.get(
        f"{base_url}/agents?pretty=true",
        headers={"Authorization": f"Bearer {token}"},
        verify=settings.wazuh_verify_tls,
        timeout=10,
    )
    agents_response.raise_for_status()

    data = agents_response.json()
    agents = data.get("data", {}).get("affected_items", [])

    checked = 0
    updated_online = 0
    unmatched = []

    for agent in agents:
        checked += 1

        agent_id = str(agent.get("id", ""))
        agent_name = agent.get("name")
        agent_ip = agent.get("ip")
        agent_status = str(agent.get("status", "")).lower()
        agent_os = agent.get("os") or {}
        os_name = agent_os.get("name")
        os_version = agent_os.get("version")

        if agent_id == "000":
            continue

        asset = None

        if agent_name:
            asset = db.scalar(
                _select(_Asset).where(
                    _func.lower(_Asset.hostname) == str(agent_name).lower()
                )
            )

        if asset is None and agent_ip and agent_ip not in {"any", "127.0.0.1"}:
            asset = db.scalar(
                _select(_Asset).where(_Asset.ip_address == str(agent_ip))
            )

        if asset is None:
            unmatched.append(
                {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "agent_ip": agent_ip,
                    "agent_status": agent_status,
                }
            )
            continue

        if agent_status == "active":
            asset.updated_at = _datetime.now(_UTC)
            
            if os_name:
               asset.operating_system = (
                   f"{os_name} {os_version}".strip()
                   if os_version 
                   else str(os_name)
               )

            updated_online += 1

    db.commit()

    return {
        "checked_agents": checked,
        "updated_online_assets": updated_online,
        "unmatched_agents": unmatched[:10],
    }
