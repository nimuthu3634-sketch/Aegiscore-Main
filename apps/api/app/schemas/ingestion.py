from __future__ import annotations

from datetime import datetime

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


class WazuhConnectorStatusResponse(APIModel):
    connector: str
    enabled: bool
    status: str
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None
    last_checkpoint_timestamp: str | None
    checkpoint_external_ids: list[str]
    metrics: dict[str, int]


class SuricataConnectorStatusResponse(APIModel):
    connector: str
    enabled: bool
    mode: str
    source_path: str
    status: str
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error_message: str | None
    checkpoint_offset: int
    checkpoint_inode: int | None
    metrics: dict[str, int]
