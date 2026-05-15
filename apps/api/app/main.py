# FastAPI application entry point for the AegisCore backend.

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.integrations.suricata_connector import run_suricata_connector_forever
from app.services.integrations.state import (
    SURICATA_CONNECTOR_KEY,
    WAZUH_CONNECTOR_KEY,
    get_or_create_connector_state,
)
from app.services.integrations.wazuh_connector import run_wazuh_connector_forever

# Loads application settings once so the API can use environment configuration.
settings = get_settings()


# Starts connector background tasks when the API starts and stops them during shutdown.
@asynccontextmanager
async def lifespan(_: FastAPI):
    # This event is used to gracefully stop background connector loops.
    stop_event = asyncio.Event()
    tasks: list[asyncio.Task[None]] = []
    try:
        with SessionLocal() as session:
            if settings.wazuh_connector_enabled:
                get_or_create_connector_state(session, WAZUH_CONNECTOR_KEY)
            if settings.suricata_connector_enabled:
                get_or_create_connector_state(session, SURICATA_CONNECTOR_KEY)
            session.commit()
    except Exception:
        # Connector loops update state once polling starts; startup should not fail on temporary DB issues.
        pass
    # Starts the Wazuh connector only when it is enabled in environment settings.
    if settings.wazuh_connector_enabled:
        tasks.append(asyncio.create_task(run_wazuh_connector_forever(stop_event)))
    # Starts the Suricata connector only when it is enabled in environment settings.
    if settings.suricata_connector_enabled:
        tasks.append(asyncio.create_task(run_suricata_connector_forever(stop_event)))
    try:
        yield
    finally:
        # Signals the background connector tasks to stop during shutdown.
        stop_event.set()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Creates the FastAPI app and attaches the application lifespan handler.
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
# Registers all API route groups in the application.
app.include_router(api_router)

