from fastapi import APIRouter

from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health import get_health_payload, get_readiness_payload

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    return get_health_payload()


@router.get("/health/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="aegiscore-api",
        database="unknown",
    )


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    return get_readiness_payload()

