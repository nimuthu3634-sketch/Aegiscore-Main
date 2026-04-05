from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health import get_health_payload

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return get_health_payload()

