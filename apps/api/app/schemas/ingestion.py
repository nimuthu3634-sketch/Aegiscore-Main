from datetime import datetime
from typing import Any

from app.models.enums import DetectionType
from app.schemas.base import APIModel


# Request body used when raw alerts are sent into the ingestion API.
class RawAlertIngestRequest(APIModel):
    source: str
    external_id: str | None = None
    detection_type: DetectionType
    severity: int
    payload: dict[str, Any]
    received_at: datetime | None = None


# Response returned after one alert is ingested successfully.
class IngestedAlertResponse(APIModel):
    raw_alert_id: str
    normalized_alert_id: str
    risk_score: int | None = None


# Request body used for sending multiple alerts at once.
class BulkIngestRequest(APIModel):
    alerts: list[RawAlertIngestRequest]


# Response returned after bulk ingestion is completed.
class BulkIngestResponse(APIModel):
    ingested: list[IngestedAlertResponse]
    failed: list[dict[str, Any]]