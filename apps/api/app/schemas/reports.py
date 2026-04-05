import enum
from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from app.models.enums import DetectionType, IncidentPriority, IncidentStatus
from app.schemas.base import APIModel
from app.schemas.listing import (
    AlertListStatusFilter,
    AlertSeverityLabel,
    IncidentListStateFilter,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
    SourceTypeFilter,
)


class ReportExportFormat(str, enum.Enum):
    CSV = "csv"
    JSON = "json"


class ReportSummaryQuery(APIModel):
    date_from: date | None = None
    date_to: date | None = None
    detection_type: DetectionType | None = None
    source_type: SourceTypeFilter | None = None


class AlertReportExportQuery(APIModel):
    date_from: date | None = None
    date_to: date | None = None
    detection_type: DetectionType | None = None
    source_type: SourceTypeFilter | None = None
    severity: AlertSeverityLabel | None = None
    status: AlertListStatusFilter | None = None
    asset: str | None = None
    format: ReportExportFormat = ReportExportFormat.CSV


class IncidentReportExportQuery(APIModel):
    date_from: date | None = None
    date_to: date | None = None
    priority: AlertSeverityLabel | None = None
    state: IncidentListStateFilter | None = None
    assignee: str | None = None
    detection_type: DetectionType | None = None
    format: ReportExportFormat = ReportExportFormat.CSV


class ResponseReportExportQuery(APIModel):
    date_from: date | None = None
    date_to: date | None = None
    mode: ResponseModeLabel | None = None
    execution_status: ResponseExecutionStatusLabel | None = None
    action_type: str | None = None
    format: ReportExportFormat = ReportExportFormat.CSV


class ReportBreakdownItemResponse(APIModel):
    label: str
    total: int


class ReportTimeBucketResponse(APIModel):
    label: str
    start: datetime
    end: datetime
    total: int


class ReportTopAssetResponse(APIModel):
    asset_id: UUID
    hostname: str
    ip_address: str
    alert_count: int
    incident_count: int


class ReportSummaryResponse(APIModel):
    report_type: Literal["daily", "weekly"]
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    total_alerts: int
    high_risk_alerts: int
    open_incidents: int
    response_actions: int
    active_assets: int
    average_risk_score: float
    alert_volume: list[ReportTimeBucketResponse]
    alerts_by_detection: list[ReportBreakdownItemResponse]
    severity_distribution: list[ReportBreakdownItemResponse]
    incident_state_distribution: list[ReportBreakdownItemResponse]
    response_status_distribution: list[ReportBreakdownItemResponse]
    top_assets: list[ReportTopAssetResponse]


class AlertExportItemResponse(APIModel):
    id: UUID
    event_id: str | None = None
    created_at: datetime
    detection_type: DetectionType
    source_type: str
    severity_label: AlertSeverityLabel
    status_label: str
    risk_score: int | None = None
    priority_label: IncidentPriority | None = None
    asset_hostname: str | None = None
    asset_ip_address: str | None = None
    source_ip: str | None = None
    destination_ip: str | None = None
    destination_port: int | None = None
    username: str | None = None
    linked_incident_id: UUID | None = None
    linked_incident_title: str | None = None


class IncidentExportItemResponse(APIModel):
    id: UUID
    title: str
    priority: IncidentPriority
    state: IncidentStatus
    assignee: str | None = None
    created_at: datetime
    updated_at: datetime
    linked_alerts_count: int
    primary_asset: str | None = None
    detection_types: list[str]
    asset_hostnames: list[str]
    response_actions_count: int


class ResponseExportItemResponse(APIModel):
    id: UUID
    action_type: str
    execution_status: ResponseExecutionStatusLabel
    mode: ResponseModeLabel | None = None
    policy_name: str | None = None
    target: str | None = None
    linked_incident_id: UUID | None = None
    linked_incident_title: str | None = None
    result_summary: str | None = None
    result_message: str | None = None
    attempt_count: int = 0
    created_at: datetime
    executed_at: datetime | None = None


class AlertExportResponse(APIModel):
    report_name: str
    generated_at: datetime
    format: ReportExportFormat
    filters: dict[str, Any]
    total: int
    items: list[AlertExportItemResponse]


class IncidentExportResponse(APIModel):
    report_name: str
    generated_at: datetime
    format: ReportExportFormat
    filters: dict[str, Any]
    total: int
    items: list[IncidentExportItemResponse]


class ResponseExportResponse(APIModel):
    report_name: str
    generated_at: datetime
    format: ReportExportFormat
    filters: dict[str, Any]
    total: int
    items: list[ResponseExportItemResponse]
