import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.services.integrations.suricata_connector import run_suricata_connector_forever
from app.services.integrations.wazuh_connector import run_wazuh_connector_forever

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop_event = asyncio.Event()
    tasks: list[asyncio.Task[None]] = []
    if settings.wazuh_connector_enabled:
        tasks.append(asyncio.create_task(run_wazuh_connector_forever(stop_event)))
    if settings.suricata_connector_enabled:
        tasks.append(asyncio.create_task(run_suricata_connector_forever(stop_event)))
    try:
        yield
    finally:
        stop_event.set()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.include_router(api_router)

