from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import DetectionType
from app.models.normalized_alert import NormalizedAlert
from app.services.scoring.constants import (
    INTEGRITY_CRITICAL_PATH_MARKERS,
    PRIVILEGED_ACCOUNT_MARKERS,
    SCORING_BLACKLISTED_IP_REPEAT_THRESHOLD,
    SCORING_BUSINESS_HOUR_END_UTC,
    SCORING_BUSINESS_HOUR_START_UTC,
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


def _alerts_in_window(
    recent_alerts: list[NormalizedAlert],
    *,
    anchor: datetime,
    window: timedelta,
) -> list[NormalizedAlert]:
    start = anchor - window
    return [a for a in recent_alerts if start <= a.created_at <= anchor]


def _same_ip_brute_force_count(
    candidates: list[NormalizedAlert],
    *,
    source_ip: str | None,
) -> int:
    if not source_ip:
        return 0
    return sum(
        1
        for other in candidates
        if other.detection_type == DetectionType.BRUTE_FORCE
        and extract_source_ip(other) == source_ip
    )


def extract_integrity_change_tier(alert: NormalizedAlert) -> str:
    payloads = [alert.normalized_payload, alert.raw_alert.raw_payload]
    raw = _pick_payload_value(payloads, "integrity_change", "syscheck_event_type", "fim_event_type")
    if isinstance(raw, str):
        tier = raw.strip().lower()
        if tier in ("none", "minor", "important", "critical"):
            return tier
    file_path = _pick_payload_value(payloads, "file_path", "path", "target_path")
    if isinstance(file_path, str):
        lowered = file_path.lower()
        if any(marker in lowered for marker in INTEGRITY_CRITICAL_PATH_MARKERS):
            return "critical"
        if extract_sensitive_file_flag(alert):
            return "important"
        return "minor"
    if extract_sensitive_file_flag(alert):
        return "important"
    return "none"


def extract_failed_logins_5m(
    alert: NormalizedAlert,
    *,
    recent_alerts: list[NormalizedAlert],
    observed_at: datetime,
) -> int:
    payloads = [alert.normalized_payload, alert.raw_alert.raw_payload]
    explicit = _coerce_int(
        _pick_payload_value(
            payloads,
            "failed_logins_5m",
            "failed_logins_5min",
            "failed_attempts_5m",
            "failed_attempts_last_5m",
        )
    )
    base = extract_failed_login_count(alert)
    window_alerts = _alerts_in_window(recent_alerts, anchor=observed_at, window=timedelta(minutes=5))
    source_ip = extract_source_ip(alert)
    brute_peers = _same_ip_brute_force_count(window_alerts, source_ip=source_ip)
    if alert.detection_type == DetectionType.BRUTE_FORCE:
        return max(explicit or 0, base, brute_peers)
    return max(explicit or 0, base)


def extract_failed_logins_1m(
    alert: NormalizedAlert,
    *,
    recent_alerts: list[NormalizedAlert],
    observed_at: datetime,
    failed_logins_5m: int,
) -> int:
    payloads = [alert.normalized_payload, alert.raw_alert.raw_payload]
    explicit = _coerce_int(
        _pick_payload_value(
            payloads,
            "failed_logins_1m",
            "failed_logins_1min",
            "failed_attempts_1m",
        )
    )
    base = extract_failed_login_count(alert)
    window_alerts = _alerts_in_window(recent_alerts, anchor=observed_at, window=timedelta(minutes=1))
    source_ip = extract_source_ip(alert)
    brute_peers = _same_ip_brute_force_count(window_alerts, source_ip=source_ip)
    if alert.detection_type == DetectionType.BRUTE_FORCE:
        merged = max(explicit or 0, brute_peers, min(base, failed_logins_5m))
        return merged
    return max(explicit or 0, min(base, failed_logins_5m))


def extract_unique_ports_1m(
    alert: NormalizedAlert,
    *,
    recent_alerts: list[NormalizedAlert],
    observed_at: datetime,
    destination_port: int | None,
) -> int:
    payloads = [alert.normalized_payload, alert.raw_alert.raw_payload]
    explicit = _coerce_int(
        _pick_payload_value(
            payloads,
            "unique_ports_1m",
            "unique_dest_ports_1m",
            "unique_ports",
        )
    )
    if explicit is not None and explicit > 0:
        return explicit
    if alert.detection_type != DetectionType.PORT_SCAN:
        return max(destination_port or 0, 0)
    source_ip = extract_source_ip(alert)
    if not source_ip:
        return max(destination_port or 0, 1)
    window_alerts = _alerts_in_window(recent_alerts, anchor=observed_at, window=timedelta(minutes=60))
    ports: set[int] = set()
    if destination_port:
        ports.add(int(destination_port))
    for other in window_alerts:
        if other.detection_type != DetectionType.PORT_SCAN:
            continue
        if extract_source_ip(other) != source_ip:
            continue
        dp = extract_destination_port(other)
        if dp is not None:
            ports.add(int(dp))
    return max(len(ports), 1)


def extract_off_hours_flag(observed_at: datetime) -> int:
    dt = observed_at if observed_at.tzinfo else observed_at.replace(tzinfo=UTC)
    hour = dt.astimezone(UTC).hour
    if SCORING_BUSINESS_HOUR_START_UTC <= hour < SCORING_BUSINESS_HOUR_END_UTC:
        return 0
    return 1


def extract_blacklisted_ip_flag(alert: NormalizedAlert, *, repeated_source_ip: int) -> int:
    payloads = [alert.normalized_payload, alert.raw_alert.raw_payload]
    marker = _pick_payload_value(
        payloads,
        "blacklisted_ip",
        "blocked_ip",
        "denylist_match",
        "reputation_block",
    )
    if marker is True or (isinstance(marker, (int, float)) and int(marker) == 1):
        return 1
    if isinstance(marker, str) and marker.strip().lower() in ("1", "true", "yes"):
        return 1
    return 1 if repeated_source_ip >= SCORING_BLACKLISTED_IP_REPEAT_THRESHOLD else 0


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

    failed_logins_5m = extract_failed_logins_5m(
        alert, recent_alerts=recent_alerts, observed_at=observed_at
    )
    failed_logins_1m = extract_failed_logins_1m(
        alert,
        recent_alerts=recent_alerts,
        observed_at=observed_at,
        failed_logins_5m=failed_logins_5m,
    )
    unique_ports_1m = extract_unique_ports_1m(
        alert,
        recent_alerts=recent_alerts,
        observed_at=observed_at,
        destination_port=destination_port,
    )
    integrity_change = extract_integrity_change_tier(alert)
    new_user_created = 1 if alert.detection_type == DetectionType.UNAUTHORIZED_USER_CREATION else 0
    off_hours = extract_off_hours_flag(observed_at)
    blacklisted_ip = extract_blacklisted_ip_flag(
        alert, repeated_source_ip=repeated_source_ip if source_ip else 0
    )
    suricata_severity = alert.severity if alert.source.lower() == "suricata" else 0

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
        failed_logins_1m=failed_logins_1m,
        failed_logins_5m=failed_logins_5m,
        unique_ports_1m=unique_ports_1m,
        integrity_change=integrity_change,
        new_user_created=new_user_created,
        off_hours=off_hours,
        blacklisted_ip=blacklisted_ip,
        suricata_severity=suricata_severity,
    )
