from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import engine
from app.db.session import SessionLocal
from app.services.integrations.state import (
    SURICATA_CONNECTOR_KEY,
    WAZUH_CONNECTOR_KEY,
    get_connector_state,
)
from app.schemas.health import (
    DependencyStatusResponse,
    HealthResponse,
    ReadinessResponse,
)


def get_database_status() -> str:
    # Checks whether the API can connect to the database.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "up"
    except SQLAlchemyError:
        return "down"


def get_health_payload() -> HealthResponse:
    # Builds the basic health response for the API.
    database_status = get_database_status()
    application_status = "ok" if database_status == "up" else "degraded"

    return HealthResponse(
        status=application_status,
        service="aegiscore-api",
        database=database_status,
    )


def _integration_dependency_status(connector: str, enabled: bool) -> DependencyStatusResponse:
    # Returns the current status of an external connector like Wazuh or Suricata.
    if not enabled:
        return DependencyStatusResponse(
            enabled=False,
            status="disabled",
            detail="Connector disabled in environment configuration.",
        )

    with SessionLocal() as session:
        state = get_connector_state(session, connector)

    if state is None:
        return DependencyStatusResponse(
            enabled=True,
            status="starting",
            detail="Connector is enabled but has not recorded status yet.",
        )

    # Adds useful detail about the last connector success or error.
    detail = None
    if state.last_error_message:
        detail = state.last_error_message
    elif state.last_success_at:
        detail = f"Last success at {state.last_success_at.isoformat()}"

    return DependencyStatusResponse(
        enabled=True,
        status=state.status,
        detail=detail,
    )


def get_readiness_payload() -> ReadinessResponse:
    # Readiness checks database access and external connector states.
    settings = get_settings()
    database_status = get_database_status()

    dependencies = {
        "wazuh_connector": _integration_dependency_status(
            WAZUH_CONNECTOR_KEY,
            settings.wazuh_connector_enabled,
        ),
        "suricata_connector": _integration_dependency_status(
            SURICATA_CONNECTOR_KEY,
            settings.suricata_connector_enabled,
        ),
    }

    overall_status = "ready" if database_status == "up" else "not_ready"

    return ReadinessResponse(
        status=overall_status,
        service="aegiscore-api",
        database=database_status,
        dependencies=dependencies,
    )