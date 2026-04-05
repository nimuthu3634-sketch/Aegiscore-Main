from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import UTC, date, datetime, time, timedelta
from io import StringIO
from typing import Any, Iterable

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.enums import IncidentStatus, ResponseStatus
from app.models.normalized_alert import NormalizedAlert
from app.models.response_action import ResponseAction
from app.models.user import User
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.reports import ReportsRepository
from app.schemas.listing import AlertSeverityLabel, ResponseExecutionStatusLabel
from app.schemas.reports import (
    AlertExportItemResponse,
    AlertExportResponse,
    AlertReportExportQuery,
    IncidentExportItemResponse,
    IncidentExportResponse,
    IncidentReportExportQuery,
    ReportBreakdownItemResponse,
    ReportExportFormat,
    ReportSummaryQuery,
    ReportSummaryResponse,
    ReportTimeBucketResponse,
    ReportTopAssetResponse,
    ResponseExportItemResponse,
    ResponseExportResponse,
    ResponseReportExportQuery,
)
from app.services.serializers import (
    to_alert_summary_response,
    to_incident_summary_response,
    to_response_action_summary_response,
)

HIGH_RISK_THRESHOLD = 70
TERMINAL_INCIDENT_STATES = {
    IncidentStatus.RESOLVED,
    IncidentStatus.FALSE_POSITIVE,
}


def _normalize_window(
    *,
    date_from: date | None,
    date_to: date | None,
    default_days: int,
) -> tuple[datetime, datetime]:
    now = datetime.now(UTC)

    if date_from is None and date_to is None:
        return now - timedelta(days=default_days), now

    if date_from is not None:
        start = datetime.combine(date_from, time.min, tzinfo=UTC)
    else:
        if date_to is None:
            raise ValueError("A report end date is required when the start date is omitted.")
        end_anchor = datetime.combine(date_to, time.max, tzinfo=UTC)
        start = end_anchor - timedelta(days=default_days)

    if date_to is not None:
        end = datetime.combine(date_to, time.max, tzinfo=UTC)
    else:
        end = min(now, start + timedelta(days=default_days, hours=1))

    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be later than date_to.",
        )

    return start, min(end, now)


def _severity_label(severity_score: int) -> AlertSeverityLabel:
    if severity_score >= 9:
        return AlertSeverityLabel.CRITICAL
    if severity_score >= 7:
        return AlertSeverityLabel.HIGH
    if severity_score >= 4:
        return AlertSeverityLabel.MEDIUM
    return AlertSeverityLabel.LOW


def _response_execution_label(
    response_action: ResponseAction,
) -> ResponseExecutionStatusLabel:
    if response_action.status == ResponseStatus.COMPLETED:
        return ResponseExecutionStatusLabel.SUCCEEDED
    if response_action.status == ResponseStatus.WARNING:
        return ResponseExecutionStatusLabel.WARNING
    if response_action.status == ResponseStatus.FAILED:
        return ResponseExecutionStatusLabel.FAILED
    return ResponseExecutionStatusLabel.PENDING


def _execution_timestamp(response_action: ResponseAction) -> datetime:
    return response_action.executed_at or response_action.created_at


def _alert_related_responses(
    alerts: Iterable[NormalizedAlert],
    *,
    window_start: datetime,
    window_end: datetime,
) -> list[ResponseAction]:
    by_id: dict[str, ResponseAction] = {}

    for alert in alerts:
        for response_action in alert.response_actions:
            executed_at = _execution_timestamp(response_action)
            if window_start <= executed_at <= window_end:
                by_id[str(response_action.id)] = response_action
        if alert.incident is not None:
            for response_action in alert.incident.response_actions:
                executed_at = _execution_timestamp(response_action)
                if window_start <= executed_at <= window_end:
                    by_id[str(response_action.id)] = response_action

    return sorted(by_id.values(), key=_execution_timestamp, reverse=True)


def _unique_incidents(alerts: Iterable[NormalizedAlert]):
    incidents: dict[str, Any] = {}
    for alert in alerts:
        if alert.incident is not None:
            incidents[str(alert.incident.id)] = alert.incident
    return list(incidents.values())


def _breakdown(counter: Counter[str]) -> list[ReportBreakdownItemResponse]:
    return [
        ReportBreakdownItemResponse(label=label, total=total)
        for label, total in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def _bucket_floor(timestamp: datetime, *, granularity: str) -> datetime:
    normalized = timestamp.astimezone(UTC)
    if granularity == "day":
        return normalized.replace(hour=0, minute=0, second=0, microsecond=0)
    return normalized.replace(minute=0, second=0, microsecond=0)


def _bucket_step(*, granularity: str) -> timedelta:
    if granularity == "day":
        return timedelta(days=1)
    return timedelta(hours=1)


def _bucket_label(bucket_start: datetime, *, granularity: str) -> str:
    if granularity == "day":
        return bucket_start.strftime("%m-%d")
    return bucket_start.strftime("%m-%d %H:00")


def _build_alert_volume(
    alerts: Iterable[NormalizedAlert],
    *,
    window_start: datetime,
    window_end: datetime,
    granularity: str,
) -> list[ReportTimeBucketResponse]:
    counts: Counter[datetime] = Counter()
    for alert in alerts:
        counts[_bucket_floor(alert.created_at, granularity=granularity)] += 1

    cursor = _bucket_floor(window_start, granularity=granularity)
    final_bucket = _bucket_floor(window_end, granularity=granularity)
    step = _bucket_step(granularity=granularity)
    buckets: list[ReportTimeBucketResponse] = []
    while cursor <= final_bucket:
        bucket_end = min(cursor + step - timedelta(seconds=1), window_end)
        buckets.append(
            ReportTimeBucketResponse(
                label=_bucket_label(cursor, granularity=granularity),
                start=cursor,
                end=bucket_end,
                total=counts.get(cursor, 0),
            )
        )
        cursor += step

    return buckets


def _build_top_assets(alerts: Iterable[NormalizedAlert]) -> list[ReportTopAssetResponse]:
    grouped: dict[str, dict[str, Any]] = {}

    for alert in alerts:
        if alert.asset is None:
            continue
        asset_key = str(alert.asset.id)
        bucket = grouped.setdefault(
            asset_key,
            {
                "asset": alert.asset,
                "alert_count": 0,
                "incident_ids": set(),
            },
        )
        bucket["alert_count"] += 1
        if alert.incident is not None:
            bucket["incident_ids"].add(str(alert.incident.id))

    ranked = sorted(
        grouped.values(),
        key=lambda item: (
            -item["alert_count"],
            -len(item["incident_ids"]),
            item["asset"].hostname,
        ),
    )

    return [
        ReportTopAssetResponse(
            asset_id=item["asset"].id,
            hostname=item["asset"].hostname,
            ip_address=item["asset"].ip_address,
            alert_count=item["alert_count"],
            incident_count=len(item["incident_ids"]),
        )
        for item in ranked[:5]
    ]


def _serialize_filter_value(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "value"):
        return getattr(value, "value")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_filters(query: Any, fields: Iterable[str]) -> dict[str, Any]:
    return {
        field_name: _serialize_filter_value(getattr(query, field_name))
        for field_name in fields
    }


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(_csv_value(item) for item in value)
    return str(value)


def _build_csv_content(items: Iterable[dict[str, Any]], fieldnames: list[str]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        writer.writerow({key: _csv_value(item.get(key)) for key in fieldnames})
    return buffer.getvalue()


def _build_download_filename(prefix: str, export_format: ReportExportFormat) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"aegiscore-{prefix}-{stamp}.{export_format.value}"


def _record_export_audit(
    session: Session,
    *,
    actor: User,
    report_name: str,
    export_format: ReportExportFormat,
    filters: dict[str, Any],
    record_count: int,
) -> None:
    AuditLogsRepository(session).create(
        AuditLog(
            actor=actor,
            entity_type="report",
            entity_id=report_name,
            action=f"report.export.{report_name}",
            details={
                "format": export_format.value,
                "filters": filters,
                "record_count": record_count,
                "summary": f"{report_name} exported in {export_format.value} format.",
            },
        )
    )


def _alert_export_item(alert: NormalizedAlert) -> AlertExportItemResponse:
    summary = to_alert_summary_response(alert)
    return AlertExportItemResponse(
        id=summary.id,
        event_id=summary.event_id,
        created_at=summary.created_at,
        detection_type=summary.detection_type,
        source_type=summary.source_type,
        severity_label=AlertSeverityLabel(summary.severity_label),
        status_label=summary.status_label,
        risk_score=summary.risk_score_value,
        priority_label=summary.risk_score.priority_label if summary.risk_score else None,
        asset_hostname=summary.asset.hostname if summary.asset else None,
        asset_ip_address=summary.asset.ip_address if summary.asset else None,
        source_ip=summary.source_ip,
        destination_ip=summary.destination_ip,
        destination_port=summary.destination_port,
        username=summary.username,
        linked_incident_id=summary.incident.id if summary.incident else None,
        linked_incident_title=summary.incident.title if summary.incident else None,
    )


def _incident_export_item(incident) -> IncidentExportItemResponse:
    summary = to_incident_summary_response(incident)
    detection_types = sorted({alert.detection_type.value for alert in incident.alerts})
    asset_hostnames = sorted(
        {
            alert.asset.hostname
            for alert in incident.alerts
            if alert.asset is not None
        }
    )
    return IncidentExportItemResponse(
        id=summary.id,
        title=summary.title,
        priority=summary.priority,
        state=summary.status,
        assignee=summary.assignee_name,
        created_at=summary.created_at,
        updated_at=summary.updated_at,
        linked_alerts_count=summary.linked_alerts_count,
        primary_asset=summary.primary_asset_name,
        detection_types=detection_types,
        asset_hostnames=asset_hostnames,
        response_actions_count=len(incident.response_actions),
    )


def _response_export_item(response_action: ResponseAction) -> ResponseExportItemResponse:
    summary = to_response_action_summary_response(response_action)
    return ResponseExportItemResponse(
        id=summary.id,
        action_type=summary.action_type,
        execution_status=summary.execution_status_label,
        mode=summary.mode,
        policy_name=summary.policy_name,
        target=summary.target,
        linked_incident_id=summary.incident.id if summary.incident else None,
        linked_incident_title=summary.incident.title if summary.incident else None,
        result_summary=summary.result_summary,
        result_message=summary.result_message,
        attempt_count=summary.attempt_count,
        created_at=summary.created_at,
        executed_at=summary.executed_at,
    )


def _alert_export_rows(items: list[AlertExportItemResponse]) -> list[dict[str, Any]]:
    return [
        {
            "alert_id": item.id,
            "event_id": item.event_id,
            "created_at": item.created_at,
            "detection_type": item.detection_type,
            "source_type": item.source_type,
            "severity_label": item.severity_label,
            "status_label": item.status_label,
            "risk_score": item.risk_score,
            "priority_label": item.priority_label,
            "asset_hostname": item.asset_hostname,
            "asset_ip_address": item.asset_ip_address,
            "source_ip": item.source_ip,
            "destination_ip": item.destination_ip,
            "destination_port": item.destination_port,
            "username": item.username,
            "linked_incident_id": item.linked_incident_id,
            "linked_incident_title": item.linked_incident_title,
        }
        for item in items
    ]


def _incident_export_rows(items: list[IncidentExportItemResponse]) -> list[dict[str, Any]]:
    return [
        {
            "incident_id": item.id,
            "title": item.title,
            "priority": item.priority,
            "state": item.state,
            "assignee": item.assignee,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "linked_alerts_count": item.linked_alerts_count,
            "primary_asset": item.primary_asset,
            "detection_types": item.detection_types,
            "asset_hostnames": item.asset_hostnames,
            "response_actions_count": item.response_actions_count,
        }
        for item in items
    ]


def _response_export_rows(items: list[ResponseExportItemResponse]) -> list[dict[str, Any]]:
    return [
        {
            "response_id": item.id,
            "action_type": item.action_type,
            "execution_status": item.execution_status,
            "mode": item.mode,
            "policy_name": item.policy_name,
            "target": item.target,
            "linked_incident_id": item.linked_incident_id,
            "linked_incident_title": item.linked_incident_title,
            "result_summary": item.result_summary,
            "result_message": item.result_message,
            "attempt_count": item.attempt_count,
            "created_at": item.created_at,
            "executed_at": item.executed_at,
        }
        for item in items
    ]


def _download_response(
    *,
    filename: str,
    export_format: ReportExportFormat,
    content: str,
) -> Response:
    media_type = (
        "text/csv"
        if export_format == ReportExportFormat.CSV
        else "application/json"
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _json_download_response(
    *,
    filename: str,
    payload: AlertExportResponse | IncidentExportResponse | ResponseExportResponse,
) -> JSONResponse:
    return JSONResponse(
        content=payload.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _build_report_summary(
    *,
    report_type: str,
    alerts: list[NormalizedAlert],
    window_start: datetime,
    window_end: datetime,
    granularity: str,
) -> ReportSummaryResponse:
    incidents = _unique_incidents(alerts)
    responses = _alert_related_responses(
        alerts,
        window_start=window_start,
        window_end=window_end,
    )
    risk_scores = [
        alert.risk_score.score
        for alert in alerts
        if alert.risk_score is not None
    ]
    severity_counter = Counter(_severity_label(alert.severity).value for alert in alerts)
    detection_counter = Counter(alert.detection_type.value for alert in alerts)
    incident_state_counter = Counter(incident.status.value for incident in incidents)
    response_status_counter = Counter(
        _response_execution_label(response_action).value
        for response_action in responses
    )
    active_assets = {
        str(alert.asset.id)
        for alert in alerts
        if alert.asset is not None
    }

    return ReportSummaryResponse(
        report_type=report_type,
        generated_at=datetime.now(UTC),
        window_start=window_start,
        window_end=window_end,
        total_alerts=len(alerts),
        high_risk_alerts=sum(
            1
            for alert in alerts
            if alert.risk_score is not None and alert.risk_score.score >= HIGH_RISK_THRESHOLD
        ),
        open_incidents=sum(
            1
            for incident in incidents
            if incident.status not in TERMINAL_INCIDENT_STATES
        ),
        response_actions=len(responses),
        active_assets=len(active_assets),
        average_risk_score=round(sum(risk_scores) / len(risk_scores), 2)
        if risk_scores
        else 0.0,
        alert_volume=_build_alert_volume(
            alerts,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        ),
        alerts_by_detection=_breakdown(detection_counter),
        severity_distribution=_breakdown(severity_counter),
        incident_state_distribution=_breakdown(incident_state_counter),
        response_status_distribution=_breakdown(response_status_counter),
        top_assets=_build_top_assets(alerts),
    )


def get_daily_summary(session: Session, query: ReportSummaryQuery) -> ReportSummaryResponse:
    window_start, window_end = _normalize_window(
        date_from=query.date_from,
        date_to=query.date_to,
        default_days=1,
    )
    alerts = ReportsRepository(session).list_alerts_for_summary(
        query,
        window_start=window_start,
        window_end=window_end,
    )
    return _build_report_summary(
        report_type="daily",
        alerts=alerts,
        window_start=window_start,
        window_end=window_end,
        granularity="hour",
    )


def get_weekly_summary(session: Session, query: ReportSummaryQuery) -> ReportSummaryResponse:
    window_start, window_end = _normalize_window(
        date_from=query.date_from,
        date_to=query.date_to,
        default_days=7,
    )
    alerts = ReportsRepository(session).list_alerts_for_summary(
        query,
        window_start=window_start,
        window_end=window_end,
    )
    return _build_report_summary(
        report_type="weekly",
        alerts=alerts,
        window_start=window_start,
        window_end=window_end,
        granularity="day",
    )


def export_alert_report(
    session: Session,
    query: AlertReportExportQuery,
    actor: User,
) -> Response:
    window_start, window_end = _normalize_window(
        date_from=query.date_from,
        date_to=query.date_to,
        default_days=7,
    )
    alerts = ReportsRepository(session).list_alerts_for_export(
        query,
        window_start=window_start,
        window_end=window_end,
    )
    items = [_alert_export_item(alert) for alert in alerts]
    filters = _serialize_filters(
        query,
        [
            "date_from",
            "date_to",
            "detection_type",
            "source_type",
            "severity",
            "status",
            "asset",
        ],
    )
    _record_export_audit(
        session,
        actor=actor,
        report_name="alerts_export",
        export_format=query.format,
        filters=filters,
        record_count=len(items),
    )
    session.commit()

    if query.format == ReportExportFormat.CSV:
        filename = _build_download_filename("alerts-export", query.format)
        rows = _alert_export_rows(items)
        fieldnames = list(rows[0].keys()) if rows else [
            "alert_id",
            "event_id",
            "created_at",
            "detection_type",
            "source_type",
            "severity_label",
            "status_label",
            "risk_score",
            "priority_label",
            "asset_hostname",
            "asset_ip_address",
            "source_ip",
            "destination_ip",
            "destination_port",
            "username",
            "linked_incident_id",
            "linked_incident_title",
        ]
        return _download_response(
            filename=filename,
            export_format=query.format,
            content=_build_csv_content(rows, fieldnames),
        )

    payload = AlertExportResponse(
        report_name="alerts_export",
        generated_at=datetime.now(UTC),
        format=query.format,
        filters=filters,
        total=len(items),
        items=items,
    )
    return _json_download_response(
        filename=_build_download_filename("alerts-export", query.format),
        payload=payload,
    )


def export_incident_report(
    session: Session,
    query: IncidentReportExportQuery,
    actor: User,
) -> Response:
    window_start, window_end = _normalize_window(
        date_from=query.date_from,
        date_to=query.date_to,
        default_days=7,
    )
    incidents = ReportsRepository(session).list_incidents_for_export(
        query,
        window_start=window_start,
        window_end=window_end,
    )
    items = [_incident_export_item(incident) for incident in incidents]
    filters = _serialize_filters(
        query,
        ["date_from", "date_to", "priority", "state", "assignee", "detection_type"],
    )
    _record_export_audit(
        session,
        actor=actor,
        report_name="incidents_export",
        export_format=query.format,
        filters=filters,
        record_count=len(items),
    )
    session.commit()

    if query.format == ReportExportFormat.CSV:
        filename = _build_download_filename("incidents-export", query.format)
        rows = _incident_export_rows(items)
        fieldnames = list(rows[0].keys()) if rows else [
            "incident_id",
            "title",
            "priority",
            "state",
            "assignee",
            "created_at",
            "updated_at",
            "linked_alerts_count",
            "primary_asset",
            "detection_types",
            "asset_hostnames",
            "response_actions_count",
        ]
        return _download_response(
            filename=filename,
            export_format=query.format,
            content=_build_csv_content(rows, fieldnames),
        )

    payload = IncidentExportResponse(
        report_name="incidents_export",
        generated_at=datetime.now(UTC),
        format=query.format,
        filters=filters,
        total=len(items),
        items=items,
    )
    return _json_download_response(
        filename=_build_download_filename("incidents-export", query.format),
        payload=payload,
    )


def export_response_report(
    session: Session,
    query: ResponseReportExportQuery,
    actor: User,
) -> Response:
    window_start, window_end = _normalize_window(
        date_from=query.date_from,
        date_to=query.date_to,
        default_days=7,
    )
    responses = ReportsRepository(session).list_responses_for_export(
        query,
        window_start=window_start,
        window_end=window_end,
    )
    items = [_response_export_item(response_action) for response_action in responses]
    filters = _serialize_filters(
        query,
        ["date_from", "date_to", "mode", "execution_status", "action_type"],
    )
    _record_export_audit(
        session,
        actor=actor,
        report_name="responses_export",
        export_format=query.format,
        filters=filters,
        record_count=len(items),
    )
    session.commit()

    if query.format == ReportExportFormat.CSV:
        filename = _build_download_filename("responses-export", query.format)
        rows = _response_export_rows(items)
        fieldnames = list(rows[0].keys()) if rows else [
            "response_id",
            "action_type",
            "execution_status",
            "mode",
            "policy_name",
            "target",
            "linked_incident_id",
            "linked_incident_title",
            "result_summary",
            "result_message",
            "attempt_count",
            "created_at",
            "executed_at",
        ]
        return _download_response(
            filename=filename,
            export_format=query.format,
            content=_build_csv_content(rows, fieldnames),
        )

    payload = ResponseExportResponse(
        report_name="responses_export",
        generated_at=datetime.now(UTC),
        format=query.format,
        filters=filters,
        total=len(items),
        items=items,
    )
    return _json_download_response(
        filename=_build_download_filename("responses-export", query.format),
        payload=payload,
    )
