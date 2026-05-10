from __future__ import annotations

# This file uses FastAPI dependency aliases such as CurrentUser, AdminUser, and DbSession.
# They work correctly at runtime. This line prevents Pylance from incorrectly flagging them.
# pyright: reportInvalidTypeForm=false

from datetime import UTC, datetime
from typing import Any

import requests
import urllib3
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.config import get_settings
from app.models.asset import Asset
from app.services.ingestion.service import ingest_suricata_event, ingest_wazuh_event
from app.services.integrations.suricata_connector import get_suricata_connector_status
from app.services.integrations.wazuh_connector import get_wazuh_connector_status
from app.services.integrations.wazuh_indexer_connector import (
    fetch_latest_wazuh_indexer_alerts,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@router.get("/status")
def get_integration_status(
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    return {
        "wazuh": get_wazuh_connector_status(db),
        "suricata": get_suricata_connector_status(db),
    }


@router.post("/wazuh")
def ingest_wazuh_event_route(
    payload: dict[str, Any],
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    alert = ingest_wazuh_event(db, payload, actor=current_user)

    return {
        "status": "accepted",
        "alert_id": str(alert.id),
        "detection_type": alert.detection_type.value,
    }


@router.post("/suricata")
def ingest_suricata_event_route(
    payload: dict[str, Any],
    current_user: CurrentUser,
    db: DbSession,
) -> dict[str, Any]:
    alert = ingest_suricata_event(db, payload, actor=current_user)

    return {
        "status": "accepted",
        "alert_id": str(alert.id),
        "detection_type": alert.detection_type.value,
    }


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
    errors: list[str] = []

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


@router.post("/wazuh/agents/sync")
def wazuh_agents_sync_route(
    current_user: AdminUser,
    db: DbSession,
) -> dict[str, Any]:
    settings = get_settings()

    base_url = settings.wazuh_base_url.rstrip("/")
    username = settings.wazuh_username
    password = settings.wazuh_password

    if not username or not password:
        raise HTTPException(
            status_code=500,
            detail="Wazuh Manager API username or password is not configured.",
        )

    auth_response = requests.get(
        f"{base_url}/security/user/authenticate?raw=true",
        auth=(username, password),
        verify=settings.wazuh_verify_tls,
        timeout=10,
    )
    auth_response.raise_for_status()

    token = auth_response.text.strip()

    if not token:
        raise HTTPException(
            status_code=500,
            detail="Wazuh Manager API authentication did not return a token.",
        )

    agents_response = requests.get(
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
    unmatched: list[dict[str, Any]] = []

    for agent in agents:
        checked += 1

        agent_id = str(agent.get("id", ""))
        agent_name = agent.get("name")
        agent_ip = agent.get("ip")
        agent_status = str(agent.get("status", "")).lower()

        agent_os = agent.get("os") or {}
        os_name = agent_os.get("name")
        os_version = agent_os.get("version")

        # Skip the Wazuh Manager local agent.
        if agent_id == "000":
            continue

        asset = None

        if agent_name:
            asset = db.scalar(
                select(Asset).where(
                    func.lower(Asset.hostname) == str(agent_name).lower()
                )
            )

        if asset is None and agent_ip and agent_ip not in {"any", "127.0.0.1"}:
            asset = db.scalar(
                select(Asset).where(Asset.ip_address == str(agent_ip))
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
            asset.updated_at = datetime.now(UTC)

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