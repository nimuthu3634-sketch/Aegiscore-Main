from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.asset import Asset
from app.models.audit_log import AuditLog
from app.models.enums import AlertStatus, AssetCriticality
from app.models.normalized_alert import NormalizedAlert
from app.models.raw_alert import RawAlert
from app.models.user import User
from app.repositories.alerts import AlertsRepository
from app.repositories.assets import AssetsRepository
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.ingestion_failures import IngestionFailuresRepository
from app.schemas.ingestion import IngestionResultResponse
from app.services.ingestion.parsers import parse_suricata_event, parse_wazuh_event
from app.services.ingestion.types import IngestionParseError, ParsedSecurityEvent
from app.services.serializers import (
    to_alert_summary_response,
    to_incident_reference_response,
)


def _default_asset_criticality() -> AssetCriticality:
    settings = get_settings()
    try:
        return AssetCriticality(settings.ingestion_default_asset_criticality.lower())
    except ValueError:
        return AssetCriticality.MEDIUM


def _fallback_hostname(ip_address: str) -> str:
    normalized = ip_address.replace(".", "-").replace(":", "-").lower()
    return f"detected-{normalized}"


def _log_audit(
    session: Session,
    *,
    actor: User | None,
    entity_type: str,
    entity_id: str,
    action: str,
    details: dict[str, Any],
) -> None:
    AuditLogsRepository(session).create(
        AuditLog(
            actor=actor,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            details=details,
        )
    )


def _resolve_or_create_asset(
    session: Session,
    parsed_event: ParsedSecurityEvent,
) -> tuple[Asset | None, list[str]]:
    warnings: list[str] = []
    repository = AssetsRepository(session)
    existing_asset = repository.get_by_hostname_or_ip(
        hostname=parsed_event.asset_hostname,
        ip_address=parsed_event.asset_ip,
    )
    if existing_asset is not None:
        return existing_asset, warnings

    settings = get_settings()
    if not settings.ingestion_allow_asset_autocreate:
        if parsed_event.asset_hostname or parsed_event.asset_ip:
            warnings.append(
                "Asset auto-creation is disabled, so the alert was stored without an asset record."
            )
        return None, warnings

    if parsed_event.asset_ip is None:
        if parsed_event.asset_hostname:
            warnings.append(
                "Asset hostname was present without an IP address, so the alert was stored without asset linkage."
            )
        return None, warnings

    hostname = parsed_event.asset_hostname or _fallback_hostname(parsed_event.asset_ip)
    asset = repository.create(
        Asset(
            hostname=hostname,
            ip_address=parsed_event.asset_ip,
            operating_system=parsed_event.asset_operating_system,
            criticality=parsed_event.asset_criticality or _default_asset_criticality(),
        )
    )
    warnings.append(
        "A new asset record was created automatically from the ingested event context."
    )
    return asset, warnings


def _related_response_count(alert: NormalizedAlert) -> int:
    response_ids = {str(action.id) for action in alert.response_actions}
    if alert.incident is not None:
        response_ids.update(str(action.id) for action in alert.incident.response_actions)
    return len(response_ids)


def _to_result_response(
    *,
    alert: NormalizedAlert,
    source: str,
    external_id: str,
    status_label: str,
    warnings: list[str],
) -> IngestionResultResponse:
    return IngestionResultResponse(
        source=source,
        external_id=external_id,
        status=status_label,
        alert=to_alert_summary_response(alert),
        linked_incident=to_incident_reference_response(alert.incident)
        if alert.incident
        else None,
        responses_created=_related_response_count(alert),
        warnings=warnings,
    )


def _handle_parse_failure(
    session: Session,
    *,
    source: str,
    payload: dict[str, Any],
    error: IngestionParseError,
    actor: User | None,
) -> None:
    failure = IngestionFailuresRepository(session).upsert_failure(
        source=source,
        external_id=error.external_id,
        detection_hint=error.detection_hint,
        error_type=error.error_type,
        error_message=error.message,
        raw_payload=payload,
    )
    _log_audit(
        session,
        actor=actor,
        entity_type="ingestion",
        entity_id=str(failure.id),
        action="ingestion.failed",
        details={
            "source": source,
            "external_id": error.external_id,
            "error_type": error.error_type,
            "error_message": error.message,
            "retry_count": failure.retry_count,
            "detection_hint": error.detection_hint,
        },
    )
    session.commit()


def _ingest_event(
    session: Session,
    *,
    payload: dict[str, Any],
    parser,
    source: str,
    actor: User | None = None,
) -> IngestionResultResponse:
    try:
        parsed_event = parser(payload)
    except IngestionParseError as exc:
        _handle_parse_failure(
            session,
            source=source,
            payload=payload if isinstance(payload, dict) else {"payload": payload},
            error=exc,
            actor=actor,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=exc.message,
        ) from exc

    alerts_repository = AlertsRepository(session)
    existing_raw_alert = alerts_repository.get_raw_alert_by_source_external_id(
        source=parsed_event.source,
        external_id=parsed_event.external_id,
    )
    if existing_raw_alert is not None and existing_raw_alert.normalized_alert is not None:
        _log_audit(
            session,
            actor=actor,
            entity_type="alert",
            entity_id=str(existing_raw_alert.normalized_alert.id),
            action="alert.ingestion_duplicate",
            details={
                "source": parsed_event.source,
                "external_id": parsed_event.external_id,
                "summary": "Duplicate source event received; existing alert was returned.",
            },
        )
        session.commit()
        return _to_result_response(
            alert=existing_raw_alert.normalized_alert,
            source=parsed_event.source,
            external_id=parsed_event.external_id,
            status_label="duplicate",
            warnings=["Duplicate source event ignored; existing alert was returned."],
        )

    asset, asset_warnings = _resolve_or_create_asset(session, parsed_event)
    raw_alert = RawAlert(
        asset=asset,
        source=parsed_event.source,
        external_id=parsed_event.external_id,
        detection_type=parsed_event.detection_type,
        severity=parsed_event.severity,
        raw_payload=parsed_event.raw_payload,
        received_at=parsed_event.observed_at,
    )
    normalized_alert = NormalizedAlert(
        asset=asset,
        source=parsed_event.source,
        title=parsed_event.title,
        description=parsed_event.description,
        detection_type=parsed_event.detection_type,
        severity=parsed_event.severity,
        status=AlertStatus.NEW,
        normalized_payload=parsed_event.normalized_payload,
        created_at=parsed_event.observed_at,
    )
    alerts_repository.create_raw_and_normalized(raw_alert, normalized_alert)
    session.flush()
    IngestionFailuresRepository(session).resolve_failure(
        source=parsed_event.source,
        external_id=parsed_event.external_id,
    )

    combined_warnings = [*parsed_event.warnings, *asset_warnings]
    _log_audit(
        session,
        actor=actor,
        entity_type="alert",
        entity_id=str(normalized_alert.id),
        action="alert.ingested_partial" if combined_warnings else "alert.ingested",
        details={
            "source": parsed_event.source,
            "external_id": parsed_event.external_id,
            "detection_type": parsed_event.detection_type.value,
            "warnings": combined_warnings,
            "summary": "Alert ingested and normalized into the AegisCore alert pipeline.",
        },
    )
    session.commit()

    return _to_result_response(
        alert=normalized_alert,
        source=parsed_event.source,
        external_id=parsed_event.external_id,
        status_label="ingested",
        warnings=combined_warnings,
    )


def ingest_wazuh_event(
    session: Session,
    payload: dict[str, Any],
    *,
    actor: User | None = None,
) -> IngestionResultResponse:
    return _ingest_event(
        session,
        payload=payload,
        parser=parse_wazuh_event,
        source="wazuh",
        actor=actor,
    )


def ingest_suricata_event(
    session: Session,
    payload: dict[str, Any],
    *,
    actor: User | None = None,
) -> IngestionResultResponse:
    return _ingest_event(
        session,
        payload=payload,
        parser=parse_suricata_event,
        source="suricata",
        actor=actor,
    )
