from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.api.deps import CurrentUser, DbSession
from app.models.enums import DetectionType
from app.schemas.listing import (
    AlertListStatusFilter,
    AlertSeverityLabel,
    IncidentListStateFilter,
    ResponseExecutionStatusLabel,
    ResponseModeLabel,
    SourceTypeFilter,
)
from app.schemas.reports import (
    AlertReportExportQuery,
    IncidentReportExportQuery,
    ReportExportFormat,
    ReportSummaryQuery,
    ReportSummaryResponse,
    ResponseReportExportQuery,
)
from app.services.reports import (
    export_alert_report,
    export_incident_report,
    export_response_report,
    get_daily_summary,
    get_weekly_summary,
)

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_summary_query(
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    detection_type: Annotated[DetectionType | None, Query()] = None,
    source_type: Annotated[SourceTypeFilter | None, Query()] = None,
) -> ReportSummaryQuery:
    return ReportSummaryQuery(
        date_from=date_from,
        date_to=date_to,
        detection_type=detection_type,
        source_type=source_type,
    )


def get_alert_report_export_query(
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    detection_type: Annotated[DetectionType | None, Query()] = None,
    source_type: Annotated[SourceTypeFilter | None, Query()] = None,
    severity: Annotated[AlertSeverityLabel | None, Query()] = None,
    status: Annotated[AlertListStatusFilter | None, Query()] = None,
    asset: Annotated[str | None, Query()] = None,
    format: Annotated[ReportExportFormat, Query()] = ReportExportFormat.CSV,
) -> AlertReportExportQuery:
    return AlertReportExportQuery(
        date_from=date_from,
        date_to=date_to,
        detection_type=detection_type,
        source_type=source_type,
        severity=severity,
        status=status,
        asset=asset,
        format=format,
    )


def get_incident_report_export_query(
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    priority: Annotated[AlertSeverityLabel | None, Query()] = None,
    state: Annotated[IncidentListStateFilter | None, Query()] = None,
    assignee: Annotated[str | None, Query()] = None,
    detection_type: Annotated[DetectionType | None, Query()] = None,
    format: Annotated[ReportExportFormat, Query()] = ReportExportFormat.CSV,
) -> IncidentReportExportQuery:
    return IncidentReportExportQuery(
        date_from=date_from,
        date_to=date_to,
        priority=priority,
        state=state,
        assignee=assignee,
        detection_type=detection_type,
        format=format,
    )


def get_response_report_export_query(
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    mode: Annotated[ResponseModeLabel | None, Query()] = None,
    execution_status: Annotated[ResponseExecutionStatusLabel | None, Query()] = None,
    action_type: Annotated[str | None, Query()] = None,
    format: Annotated[ReportExportFormat, Query()] = ReportExportFormat.CSV,
) -> ResponseReportExportQuery:
    return ResponseReportExportQuery(
        date_from=date_from,
        date_to=date_to,
        mode=mode,
        execution_status=execution_status,
        action_type=action_type,
        format=format,
    )


@router.get("/daily-summary", response_model=ReportSummaryResponse)
def read_daily_summary(
    query: Annotated[ReportSummaryQuery, Depends(get_report_summary_query)],
    _: CurrentUser,
    db: DbSession,
) -> ReportSummaryResponse:
    return get_daily_summary(db, query)


@router.get("/weekly-summary", response_model=ReportSummaryResponse)
def read_weekly_summary(
    query: Annotated[ReportSummaryQuery, Depends(get_report_summary_query)],
    _: CurrentUser,
    db: DbSession,
) -> ReportSummaryResponse:
    return get_weekly_summary(db, query)


@router.get("/alerts/export")
def export_alerts_route(
    query: Annotated[AlertReportExportQuery, Depends(get_alert_report_export_query)],
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    return export_alert_report(db, query, current_user)


@router.get("/incidents/export")
def export_incidents_route(
    query: Annotated[IncidentReportExportQuery, Depends(get_incident_report_export_query)],
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    return export_incident_report(db, query, current_user)


@router.get("/responses/export")
def export_responses_route(
    query: Annotated[ResponseReportExportQuery, Depends(get_response_report_export_query)],
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    return export_response_report(db, query, current_user)
