from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.normalized_alert import NormalizedAlert
from app.services.scoring.constants import (
    PRIVILEGED_ACCOUNT_MARKERS,
    SENSITIVE_FILE_PATTERNS,
)
from app.services.scoring.types import AlertRiskFeatures


def _pick_payload_value(
    payloads: list[dict[str, Any] | None],
    *keys: str,
) -> Any | None:
    for payload in payloads:
        if not payload:
            continue
        for key in keys:
            value = payload.get(key)
            if value not in (None, ""):
                return value
    return None


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.isdigit():
            return int(cleaned)
    return None


def extract_source_ip(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "source_ip",
        "src_ip",
        "srcip",
        "scanner_ip",
    )


def extract_destination_ip(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "destination_ip",
        "dest_ip",
        "dst_ip",
        "dstip",
        "target_ip",
    )


def extract_destination_port(alert: NormalizedAlert) -> int | None:
    return _coerce_int(
        _pick_payload_value(
            [alert.normalized_payload, alert.raw_alert.raw_payload],
            "destination_port",
            "dest_port",
            "dst_port",
            "destinationPort",
        )
    )


def extract_username(alert: NormalizedAlert) -> str | None:
    return _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "username",
        "new_user",
        "user",
    )


def extract_rule_level(alert: NormalizedAlert) -> int:
    value = _coerce_int(
        _pick_payload_value(
            [alert.raw_alert.raw_payload, alert.normalized_payload],
            "rule_level",
            "level",
            "severity",
        )
    )
    return value if value is not None else alert.severity


def extract_failed_login_count(alert: NormalizedAlert) -> int:
    value = _coerce_int(
        _pick_payload_value(
            [alert.normalized_payload, alert.raw_alert.raw_payload],
            "failed_attempts",
            "failed_logins",
            "attempt_count",
            "failed_count",
        )
    )
    return value or 0


def extract_sensitive_file_flag(alert: NormalizedAlert) -> bool:
    file_path = _pick_payload_value(
        [alert.normalized_payload, alert.raw_alert.raw_payload],
        "file_path",
        "path",
        "target_path",
    )
    if not isinstance(file_path, str):
        return False

    lowered = file_path.lower()
    return any(pattern in lowered for pattern in SENSITIVE_FILE_PATTERNS)


def extract_privileged_account_flag(alert: NormalizedAlert) -> bool:
    username = extract_username(alert)
    if not username:
        return False

    lowered = username.lower()
    return any(marker in lowered for marker in PRIVILEGED_ACCOUNT_MARKERS)


def extract_alert_features(
    session: Session,
    alert: NormalizedAlert,
) -> AlertRiskFeatures:
    observed_at = alert.created_at or alert.raw_alert.received_at or datetime.now(UTC)
    source_ip = extract_source_ip(alert)
    destination_ip = extract_destination_ip(alert)
    destination_port = extract_destination_port(alert)
    username = extract_username(alert)
    failed_login_count = extract_failed_login_count(alert)

    recent_statement = (
        select(NormalizedAlert)
        .options(selectinload(NormalizedAlert.raw_alert))
        .where(NormalizedAlert.created_at >= observed_at - timedelta(days=30))
    )
    recent_alerts = list(session.scalars(recent_statement))

    recent_day_alerts = [
        other
        for other in recent_alerts
        if other.created_at >= observed_at - timedelta(hours=24)
    ]
    recent_hour_alerts = [
        other
        for other in recent_alerts
        if other.created_at >= observed_at - timedelta(hours=1)
    ]
    historical_alerts = [
        other
        for other in recent_alerts
        if other.created_at < observed_at - timedelta(hours=24)
    ]

    repeated_event_count = sum(
        1
        for other in recent_day_alerts
        if other.detection_type == alert.detection_type
        and (
            alert.asset_id is None
            or other.asset_id == alert.asset_id
            or extract_source_ip(other) == source_ip
        )
    )
    time_window_density = sum(
        1
        for other in recent_hour_alerts
        if alert.asset_id is None or other.asset_id == alert.asset_id
    )
    repeated_source_ip = (
        sum(
            1
            for other in recent_day_alerts
            if source_ip is not None and extract_source_ip(other) == source_ip
        )
        if source_ip is not None
        else 0
    )
    recurrence_history = sum(
        1
        for other in historical_alerts
        if other.detection_type == alert.detection_type
        and (
            (alert.asset_id is not None and other.asset_id == alert.asset_id)
            or (source_ip is not None and extract_source_ip(other) == source_ip)
        )
    )

    if alert.detection_type.value == "brute_force" and source_ip is not None:
        same_source_brute_force = sum(
            1
            for other in recent_day_alerts
            if other.detection_type.value == "brute_force"
            and extract_source_ip(other) == source_ip
        )
        failed_login_count = max(
            failed_login_count,
            same_source_brute_force * max(1, failed_login_count or 5),
        )

    return AlertRiskFeatures(
        observed_at=observed_at,
        source_type=alert.source.lower(),
        detection_type=alert.detection_type.value,
        source_severity=alert.severity,
        source_rule_level=extract_rule_level(alert),
        repeated_event_count=max(1, repeated_event_count),
        time_window_density=max(1, time_window_density),
        asset_criticality=alert.asset.criticality.value if alert.asset else "unknown",
        privileged_account_flag=extract_privileged_account_flag(alert),
        sensitive_file_flag=extract_sensitive_file_flag(alert),
        repeated_source_ip=max(1, repeated_source_ip) if source_ip else 0,
        repeated_failed_logins=failed_login_count,
        recurrence_history=max(0, recurrence_history),
        destination_port=destination_port or 0,
        has_destination_port=destination_port is not None,
        source_ip=source_ip,
        destination_ip=destination_ip,
        username=username,
        asset_hostname=alert.asset.hostname if alert.asset else None,
        asset_id=str(alert.asset_id) if alert.asset_id else None,
        alert_id=str(alert.id) if alert.id else None,
        external_id=alert.raw_alert.external_id,
    )
