from fastapi import APIRouter

from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health import get_health_payload, get_readiness_payload

# Health routes are used to check whether the API is running properly.
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    # Returns full health information about the API and database.
    return get_health_payload()


@router.get("/health/live", response_model=HealthResponse)
def liveness() -> HealthResponse:
    # Simple endpoint to confirm that the API container is alive.
    return HealthResponse(
        status="ok",
        service="aegiscore-api",
        database="unknown",
    )


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness() -> ReadinessResponse:
    # Checks whether the API is ready to handle requests.
    return get_readiness_payload()