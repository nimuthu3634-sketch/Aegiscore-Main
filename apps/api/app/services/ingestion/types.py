from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.enums import AssetCriticality, DetectionType


@dataclass(slots=True, frozen=True)
class ParsedSecurityEvent:
    source: str
    external_id: str
    detection_type: DetectionType
    severity: int
    title: str
    description: str | None
    observed_at: datetime
    normalized_payload: dict[str, Any]
    raw_payload: dict[str, Any]
    asset_hostname: str | None = None
    asset_ip: str | None = None
    asset_operating_system: str | None = None
    asset_criticality: AssetCriticality | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class IngestionParseError(Exception):
    error_type: str
    message: str
    external_id: str
    detection_hint: str | None = None

    def __str__(self) -> str:
        return self.message
