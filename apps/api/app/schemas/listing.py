import enum
from typing import Literal

from pydantic import Field

from app.models.enums import DetectionType
from app.schemas.base import APIModel


# Severity labels used for alert filtering and display.
class AlertSeverityLabel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Common sorting direction used by list pages.
class SortDirection(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


# Asset status labels shown in the asset table.
class AssetAgentStatusLabel(str, enum.Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class AssetEnvironmentLabel(str, enum.Enum):
    PRODUCTION = "production"
    OFFICE = "office"
    REMOTE = "remote"


# Status labels used when filtering response action results.
class ResponseExecutionStatusLabel(str, enum.Enum):
    SUCCEEDED = "succeeded"
    WARNING = "warning"
    FAILED = "failed"
    PENDING = "pending"


class ResponseModeLabel(str, enum.Enum):
    DRY_RUN = "dry-run"
    LIVE = "live"


# Alert status filters used by the Alerts page.
class AlertListStatusFilter(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    PENDING_RESPONSE = "pending_response"


class AlertListSortField(str, enum.Enum):
    TIMESTAMP = "timestamp"
    SEVERITY = "severity"
    RISK_SCORE = "risk_score"


class AlertDateRange(str, enum.Enum):
    FOUR_HOURS = "4h"
    TWELVE_HOURS = "12h"
    TWENTY_FOUR_HOURS = "24h"
    ALL = "all"


class SourceTypeFilter(str, enum.Enum):
    WAZUH = "wazuh"
    SURICATA = "suricata"


# Incident workflow filters used by the Incidents page.
class IncidentListStateFilter(str, enum.Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"


class IncidentListSortField(str, enum.Enum):
    UPDATED_AT = "updated_at"
    CREATED_AT = "created_at"
    PRIORITY = "priority"


class AssetListSortField(str, enum.Enum):
    HOSTNAME = "hostname"
    LAST_SEEN = "last_seen"
    RECENT_ALERTS = "recent_alerts"


class ResponseListSortField(str, enum.Enum):
    EXECUTED_AT = "executed_at"
    STATUS = "status"


# Common pagination fields reused by all list query schemas.
class PaginationQuery(APIModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)


# Metadata returned with paginated API responses.
class ListMetaResponse(APIModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    sort_by: str
    sort_direction: SortDirection
    warnings: list[str] = Field(default_factory=list)


# Query parameters supported by the alert listing API.
class AlertListQuery(PaginationQuery):
    search: str | None = None
    severity: AlertSeverityLabel | None = None
    status: AlertListStatusFilter | None = None
    detection_type: DetectionType | None = None
    source_type: SourceTypeFilter | None = None
    asset: str | None = None
    date_range: AlertDateRange = AlertDateRange.TWENTY_FOUR_HOURS
    sort_by: AlertListSortField = AlertListSortField.TIMESTAMP
    sort_direction: SortDirection = SortDirection.DESC


# Query parameters supported by the incident listing API.
class IncidentListQuery(PaginationQuery):
    search: str | None = None
    priority: AlertSeverityLabel | None = None
    state: IncidentListStateFilter | None = None
    assignee: str | None = None
    detection_type: DetectionType | None = None
    sort_by: IncidentListSortField = IncidentListSortField.UPDATED_AT
    sort_direction: SortDirection = SortDirection.DESC


# Query parameters supported by the asset listing API.
class AssetListQuery(PaginationQuery):
    search: str | None = None
    status: AssetAgentStatusLabel | None = None
    criticality: Literal["mission_critical", "high", "standard", "low"] | None = None
    operating_system: str | None = None
    environment: AssetEnvironmentLabel | None = None
    sort_by: AssetListSortField = AssetListSortField.HOSTNAME
    sort_direction: SortDirection = SortDirection.ASC


# Query parameters supported by the response action listing API.
class ResponseListQuery(PaginationQuery):
    search: str | None = None
    mode: ResponseModeLabel | None = None
    execution_status: ResponseExecutionStatusLabel | None = None
    action_type: str | None = None
    sort_by: ResponseListSortField = ResponseListSortField.EXECUTED_AT
    sort_direction: SortDirection = SortDirection.DESC