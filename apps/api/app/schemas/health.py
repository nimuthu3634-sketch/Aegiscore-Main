from app.schemas.base import APIModel


# Basic API health response used by health check endpoints.
class HealthResponse(APIModel):
    status: str
    service: str
    database: str


# Readiness response shows whether the API can fully serve requests.
class ReadinessResponse(APIModel):
    status: str
    database: str
    checks: dict[str, str]