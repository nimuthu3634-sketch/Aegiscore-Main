from __future__ import annotations

from app.schemas.base import APIModel
from app.schemas.common import AlertSummaryResponse, IncidentReferenceResponse


class IngestionResultResponse(APIModel):
    source: str
    external_id: str
    status: str
    alert: AlertSummaryResponse
    linked_incident: IncidentReferenceResponse | None
    responses_created: int
    warnings: list[str]
