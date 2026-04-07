from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.integration_state import IntegrationState

WAZUH_CONNECTOR_KEY = "wazuh_live_connector"
SURICATA_CONNECTOR_KEY = "suricata_live_connector"


def _utcnow() -> datetime:
    return datetime.now(UTC)


def get_connector_state(session: Session, connector: str) -> IntegrationState | None:
    return session.scalar(
        select(IntegrationState).where(IntegrationState.connector == connector)
    )


def get_or_create_connector_state(session: Session, connector: str) -> IntegrationState:
    state = get_connector_state(session, connector)
    if state is not None:
        return state

    state = IntegrationState(
        connector=connector,
        status="idle",
        checkpoint={},
        metrics={},
    )
    session.add(state)
    session.flush()
    return state


def mark_connector_running(session: Session, connector: str) -> IntegrationState:
    state = get_or_create_connector_state(session, connector)
    state.status = "running"
    state.updated_at = _utcnow()
    session.commit()
    return state


def mark_connector_success(
    session: Session,
    *,
    connector: str,
    checkpoint: dict[str, Any],
    metrics: dict[str, int],
) -> IntegrationState:
    state = get_or_create_connector_state(session, connector)
    state.status = "healthy"
    state.checkpoint = checkpoint
    state.metrics = metrics
    state.last_success_at = _utcnow()
    state.last_error_message = None
    state.updated_at = _utcnow()
    session.commit()
    return state


def mark_connector_error(
    session: Session,
    *,
    connector: str,
    error_message: str,
) -> IntegrationState:
    state = get_or_create_connector_state(session, connector)
    state.status = "error"
    state.last_error_at = _utcnow()
    state.last_error_message = error_message
    state.updated_at = _utcnow()
    session.commit()
    return state
