from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.models.enums import AssetCriticality, DetectionType


# Represents one security event after it has been parsed and normalized.
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

    # Asset details are optional because some logs may not include host information.
    asset_hostname: str | None = None
    asset_ip: str | None = None
    asset_operating_system: str | None = None
    asset_criticality: AssetCriticality | None = None

    # Warnings are used when the event is accepted but some information is missing.
    warnings: list[str] = field(default_factory=list)


# Custom error used when a Wazuh or Suricata event cannot be parsed correctly.
@dataclass(slots=True, frozen=True)
class IngestionParseError(Exception):
    error_type: str
    message: str
    external_id: str
    detection_hint: str | None = None

    def __str__(self) -> str:
        return self.message
