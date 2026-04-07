from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str


class DependencyStatusResponse(BaseModel):
    enabled: bool
    status: str
    detail: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    service: str
    database: str
    dependencies: dict[str, DependencyStatusResponse]

