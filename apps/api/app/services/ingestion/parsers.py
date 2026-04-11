"""Normalize upstream events; reject detections outside the academic MVP four-category scope."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Iterable

from app.models.enums import AssetCriticality, DetectionType
from app.services.ingestion.types import IngestionParseError, ParsedSecurityEvent

SUPPORTED_DETECTION_VALUES = {
    detection.value: detection for detection in DetectionType
}


def _dig(payload: dict[str, Any], *path: str) -> Any | None:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _pick_first(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any | None:
    for path in paths:
        value = _dig(payload, *path)
        if value not in (None, ""):
            return value
    return None


def _flatten_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for nested in value.values():
            yield from _flatten_strings(nested)
        return
    if isinstance(value, list):
        for item in value:
            yield from _flatten_strings(item)


def _payload_fingerprint(source: str, payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{source}-{digest}"


def _normalize_detection_hint(value: Any) -> DetectionType | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return SUPPORTED_DETECTION_VALUES.get(normalized)


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


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, UTC)
    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    if len(cleaned) >= 5 and cleaned[-5] in {"+", "-"} and cleaned[-3] != ":":
        cleaned = f"{cleaned[:-2]}:{cleaned[-2:]}"

    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _clamp_severity(value: Any, *, default: int) -> int:
    normalized = _coerce_int(value)
    if normalized is None:
        normalized = default
    return max(1, min(10, normalized))


def _suricata_severity_to_internal(value: Any) -> int:
    severity = _coerce_int(value)
    mapping = {
        1: 9,
        2: 7,
        3: 5,
        4: 3,
    }
    if severity is None:
        return 5
    return mapping.get(severity, _clamp_severity(severity, default=5))


def _infer_detection_from_text(*values: Any) -> DetectionType | None:
    combined = " ".join(
        text.lower()
        for value in values
        for text in _flatten_strings(value)
    )
    if not combined:
        return None

    if any(
        marker in combined
        for marker in (
            "unauthorized_user_creation",
            "user account created",
            "account created",
            "new user created",
            "local user created",
            "4720",
            "domain admins",
        )
    ):
        return DetectionType.UNAUTHORIZED_USER_CREATION

    if any(
        marker in combined
        for marker in (
            "file_integrity_violation",
            "file integrity",
            "syscheck",
            "fim",
            "checksum changed",
            "file modified",
            "critical file change",
        )
    ):
        return DetectionType.FILE_INTEGRITY_VIOLATION

    if any(
        marker in combined
        for marker in (
            "brute_force",
            "brute force",
            "failed login",
            "authentication failure",
            "multiple failed",
            "auth burst",
            "credential stuffing",
        )
    ):
        return DetectionType.BRUTE_FORCE

    if any(
        marker in combined
        for marker in (
            "port_scan",
            "port scan",
            "portscan",
            "sweep",
            "recon",
            "potential rdp scan",
            "potential ssh scan",
            "nmap",
        )
    ):
        return DetectionType.PORT_SCAN

    return None


def _extract_external_id(source: str, payload: dict[str, Any]) -> tuple[str, bool]:
    external_id = _pick_first(
        payload,
        ("id",),
        ("_id",),
        ("event_id",),
        ("data", "event_id"),
        ("flow_id",),
        ("tx_id",),
    )
    if external_id is None:
        return _payload_fingerprint(source, payload), True
    return str(external_id), False


def _title_for_detection(detection_type: DetectionType) -> str:
    return {
        DetectionType.BRUTE_FORCE: "Brute-force activity detected",
        DetectionType.FILE_INTEGRITY_VIOLATION: "File integrity violation detected",
        DetectionType.PORT_SCAN: "Port scan activity detected",
        DetectionType.UNAUTHORIZED_USER_CREATION: "Unauthorized user creation detected",
    }[detection_type]


def _description_for_detection(
    detection_type: DetectionType,
    *,
    source_ip: str | None,
    destination_ip: str | None,
    username: str | None,
    file_path: str | None,
    asset_hostname: str | None,
    source_rule_name: str | None,
) -> str:
    if detection_type == DetectionType.BRUTE_FORCE:
        destination_label = asset_hostname or destination_ip or "a monitored asset"
        source_label = source_ip or "an observed source"
        return (
            f"Repeated authentication failures were observed from {source_label} "
            f"against {destination_label}."
        )
    if detection_type == DetectionType.FILE_INTEGRITY_VIOLATION:
        return (
            f"A monitored file integrity change affected {file_path or 'a protected path'} "
            f"on {asset_hostname or 'a monitored asset'}."
        )
    if detection_type == DetectionType.UNAUTHORIZED_USER_CREATION:
        return (
            f"An unexpected account creation event created {username or 'a new user'} "
            f"on {asset_hostname or 'a monitored asset'}."
        )
    return (
        f"Network telemetry observed reconnaissance from {source_ip or 'an observed source'} "
        f"against {asset_hostname or destination_ip or 'a monitored target'}"
        f"{f' via {source_rule_name}' if source_rule_name else ''}."
    )


def _asset_criticality_from_payload(payload: dict[str, Any]) -> AssetCriticality | None:
    value = _pick_first(
        payload,
        ("asset_criticality",),
        ("asset", "criticality"),
        ("agent", "criticality"),
    )
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower().replace("mission_critical", "critical")
    try:
        return AssetCriticality(normalized)
    except ValueError:
        return None


def parse_wazuh_event(payload: dict[str, Any]) -> ParsedSecurityEvent:
    if not isinstance(payload, dict):
        raise IngestionParseError(
            error_type="invalid_payload",
            message="Wazuh payload must be a JSON object.",
            external_id="wazuh-invalid-payload",
        )

    external_id, used_fingerprint = _extract_external_id("wazuh", payload)
    rule_payload = _dig(payload, "rule") if isinstance(_dig(payload, "rule"), dict) else {}
    data_payload = _dig(payload, "data") if isinstance(_dig(payload, "data"), dict) else {}
    syscheck_payload = (
        _dig(payload, "syscheck") if isinstance(_dig(payload, "syscheck"), dict) else {}
    )

    detection_type = _normalize_detection_hint(
        _pick_first(payload, ("detection_type",), ("normalized", "detection_type"))
    ) or _infer_detection_from_text(
        rule_payload,
        data_payload,
        syscheck_payload,
        _pick_first(payload, ("decoder", "name")),
    )
    if detection_type is None:
        raise IngestionParseError(
            error_type="unsupported_detection",
            message="Wazuh payload did not match the supported AegisCore detection scope.",
            external_id=external_id,
            detection_hint=str(_pick_first(payload, ("event_type",), ("rule", "description")) or "unknown"),
        )

    source_ip = _pick_first(
        payload,
        ("data", "srcip"),
        ("data", "src_ip"),
        ("src_ip",),
    )
    destination_ip = _pick_first(
        payload,
        ("data", "dstip"),
        ("data", "dst_ip"),
        ("data", "destination_ip"),
        ("agent", "ip"),
    )
    destination_port = _coerce_int(
        _pick_first(
            payload,
            ("data", "dstport"),
            ("data", "dst_port"),
            ("data", "destination_port"),
        )
    )
    username = _pick_first(
        payload,
        ("data", "username"),
        ("data", "user"),
        ("data", "new_user"),
        ("data", "srcuser"),
        ("data", "win", "eventdata", "TargetUserName"),
    )
    failed_attempts = _coerce_int(
        _pick_first(
            payload,
            ("data", "failed_attempts"),
            ("data", "failed_logins"),
            ("rule", "firedtimes"),
        )
    )
    file_path = _pick_first(
        payload,
        ("syscheck", "path"),
        ("file", "path"),
        ("data", "path"),
    )
    source_rule_id = _pick_first(payload, ("rule", "id"), ("rule_id",))
    source_rule_name = _pick_first(payload, ("rule", "description"), ("rule_name",))
    service = _pick_first(payload, ("data", "service"), ("service",))
    asset_hostname = _pick_first(
        payload,
        ("agent", "name"),
        ("data", "hostname"),
        ("data", "system_name"),
    )
    asset_ip = _pick_first(payload, ("agent", "ip"), ("data", "dstip"), ("data", "dst_ip"))
    asset_os = _pick_first(payload, ("agent", "os", "name"), ("data", "os"))
    observed_at = _coerce_datetime(
        _pick_first(payload, ("timestamp",), ("data", "timestamp"))
    ) or datetime.now(UTC)
    severity = _clamp_severity(
        _pick_first(payload, ("rule", "level"), ("severity",)),
        default=5,
    )

    warnings: list[str] = []
    if used_fingerprint:
        warnings.append("No source event ID was present; external_id was generated from a payload fingerprint.")
    if not asset_hostname and not asset_ip:
        warnings.append("No asset hostname or IP was provided; alert will be stored without asset linkage.")

    normalized_payload = {
        "source_type": "wazuh",
        "asset_hostname": asset_hostname,
        "asset_ip": asset_ip,
        "source_ip": str(source_ip) if source_ip is not None else None,
        "destination_ip": str(destination_ip) if destination_ip is not None else None,
        "destination_port": destination_port,
        "username": str(username) if username is not None else None,
        "failed_attempts": failed_attempts,
        "file_path": str(file_path) if file_path is not None else None,
        "service": str(service) if service is not None else None,
        "event_ref": external_id,
        "source_rule_id": str(source_rule_id) if source_rule_id is not None else None,
        "source_rule_name": str(source_rule_name) if source_rule_name is not None else None,
        "rule_level": _coerce_int(_pick_first(payload, ("rule", "level"), ("level",))),
        "file_hash_after": _pick_first(payload, ("syscheck", "sha256_after"), ("syscheck", "md5_after")),
        "group_name": _pick_first(payload, ("data", "win", "eventdata", "GroupName")),
        "raw_groups": _pick_first(payload, ("rule", "groups")),
    }

    return ParsedSecurityEvent(
        source="wazuh",
        external_id=external_id,
        detection_type=detection_type,
        severity=severity,
        title=_title_for_detection(detection_type),
        description=_description_for_detection(
            detection_type,
            source_ip=str(source_ip) if source_ip is not None else None,
            destination_ip=str(destination_ip) if destination_ip is not None else None,
            username=str(username) if username is not None else None,
            file_path=str(file_path) if file_path is not None else None,
            asset_hostname=str(asset_hostname) if asset_hostname is not None else None,
            source_rule_name=str(source_rule_name) if source_rule_name is not None else None,
        ),
        observed_at=observed_at,
        normalized_payload={key: value for key, value in normalized_payload.items() if value is not None},
        raw_payload=payload,
        asset_hostname=str(asset_hostname) if asset_hostname is not None else None,
        asset_ip=str(asset_ip) if asset_ip is not None else None,
        asset_operating_system=str(asset_os) if asset_os is not None else None,
        asset_criticality=_asset_criticality_from_payload(payload),
        warnings=warnings,
    )


def parse_suricata_event(payload: dict[str, Any]) -> ParsedSecurityEvent:
    if not isinstance(payload, dict):
        raise IngestionParseError(
            error_type="invalid_payload",
            message="Suricata payload must be a JSON object.",
            external_id="suricata-invalid-payload",
        )

    external_id, used_fingerprint = _extract_external_id("suricata", payload)
    alert_payload = _dig(payload, "alert") if isinstance(_dig(payload, "alert"), dict) else {}
    detection_type = _normalize_detection_hint(
        _pick_first(payload, ("detection_type",), ("normalized", "detection_type"))
    ) or _infer_detection_from_text(alert_payload, payload)
    if detection_type is None:
        raise IngestionParseError(
            error_type="unsupported_detection",
            message="Suricata payload did not match the supported AegisCore detection scope.",
            external_id=external_id,
            detection_hint=str(_pick_first(payload, ("event_type",), ("alert", "signature")) or "unknown"),
        )

    source_ip = _pick_first(payload, ("src_ip",), ("source_ip",))
    destination_ip = _pick_first(payload, ("dest_ip",), ("destination_ip",))
    destination_port = _coerce_int(
        _pick_first(payload, ("dest_port",), ("dst_port",), ("destination_port",))
    )
    username = _pick_first(payload, ("username",), ("http", "hostname_user"))
    source_rule_id = _pick_first(payload, ("alert", "signature_id"), ("signature_id",))
    source_rule_name = _pick_first(payload, ("alert", "signature"), ("signature",))
    observed_at = _coerce_datetime(_pick_first(payload, ("timestamp",))) or datetime.now(UTC)
    severity = _suricata_severity_to_internal(
        _pick_first(payload, ("alert", "severity"), ("severity",))
    )

    warnings: list[str] = []
    if used_fingerprint:
        warnings.append("No Suricata flow or event ID was present; external_id was generated from a payload fingerprint.")
    if destination_ip is None:
        warnings.append("No destination IP was provided; alert will be stored without asset linkage.")

    normalized_payload = {
        "source_type": "suricata",
        "source_ip": str(source_ip) if source_ip is not None else None,
        "destination_ip": str(destination_ip) if destination_ip is not None else None,
        "destination_port": destination_port,
        "username": str(username) if username is not None else None,
        "event_ref": external_id,
        "source_rule_id": str(source_rule_id) if source_rule_id is not None else None,
        "source_rule_name": str(source_rule_name) if source_rule_name is not None else None,
        "category": _pick_first(payload, ("alert", "category")),
        "signature": _pick_first(payload, ("alert", "signature")),
        "signature_id": _pick_first(payload, ("alert", "signature_id")),
        "flow_id": _pick_first(payload, ("flow_id",)),
        "rule_level": severity,
    }

    return ParsedSecurityEvent(
        source="suricata",
        external_id=external_id,
        detection_type=detection_type,
        severity=severity,
        title=_title_for_detection(detection_type),
        description=_description_for_detection(
            detection_type,
            source_ip=str(source_ip) if source_ip is not None else None,
            destination_ip=str(destination_ip) if destination_ip is not None else None,
            username=str(username) if username is not None else None,
            file_path=None,
            asset_hostname=str(destination_ip) if destination_ip is not None else None,
            source_rule_name=str(source_rule_name) if source_rule_name is not None else None,
        ),
        observed_at=observed_at,
        normalized_payload={key: value for key, value in normalized_payload.items() if value is not None},
        raw_payload=payload,
        asset_hostname=None,
        asset_ip=str(destination_ip) if destination_ip is not None else None,
        asset_operating_system=None,
        asset_criticality=_asset_criticality_from_payload(payload),
        warnings=warnings,
    )
