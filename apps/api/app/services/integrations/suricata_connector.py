from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog
from app.repositories.audit_logs import AuditLogsRepository
from app.repositories.ingestion_failures import IngestionFailuresRepository
from app.schemas.ingestion import SuricataConnectorStatusResponse
from app.services.ingestion.service import ingest_suricata_event
from app.services.integrations.checkpoints import (
    build_file_checkpoint,
    current_file_inode,
    default_connector_metrics,
    parse_file_checkpoint,
)
from app.services.integrations.state import (
    SURICATA_CONNECTOR_KEY,
    get_connector_state,
    mark_connector_error,
    mark_connector_running,
    mark_connector_success,
)


def _record_malformed_line_failure(
    session: Session,
    *,
    source_path: Path,
    line_number: int,
    offset_before_read: int,
    line_content: str,
    error_message: str,
) -> None:
    external_id = f"suricata-file-{source_path.name}-{line_number}-{offset_before_read}"
    failure = IngestionFailuresRepository(session).upsert_failure(
        source="suricata",
        external_id=external_id,
        detection_hint="malformed_suricata_line",
        error_type="invalid_json_line",
        error_message=error_message,
        raw_payload={
            "source_path": str(source_path),
            "line_number": line_number,
            "offset": offset_before_read,
            "line": line_content[:8000],
        },
    )
    AuditLogsRepository(session).create(
        AuditLog(
            actor=None,
            entity_type="ingestion",
            entity_id=str(failure.id),
            action="ingestion.failed",
            details={
                "source": "suricata",
                "external_id": external_id,
                "error_type": "invalid_json_line",
                "error_message": error_message,
                "summary": "Malformed Suricata eve.json line encountered during connector polling.",
            },
        )
    )
    session.commit()


def _read_new_eve_lines(
    *,
    source_path: Path,
    checkpoint_offset: int,
    checkpoint_inode: int | None,
    max_events_per_cycle: int,
) -> tuple[list[tuple[int, int, str]], int, int | None]:
    if not source_path.exists():
        return [], checkpoint_offset, checkpoint_inode

    current_inode = current_file_inode(source_path)
    start_offset = checkpoint_offset
    if checkpoint_inode is None or current_inode != checkpoint_inode:
        start_offset = 0

    lines: list[tuple[int, int, str]] = []
    final_offset = start_offset
    with source_path.open("r", encoding="utf-8", errors="replace") as handle:
        handle.seek(start_offset)
        while len(lines) < max_events_per_cycle:
            line_offset = handle.tell()
            line = handle.readline()
            if not line:
                break
            final_offset = handle.tell()
            lines.append((len(lines) + 1, line_offset, line.rstrip("\n")))

    return lines, final_offset, current_inode


def run_suricata_poll_cycle(session: Session) -> dict[str, int]:
    settings = get_settings()
    if settings.suricata_connector_mode != "file_tail":
        raise RuntimeError(
            f"Unsupported Suricata connector mode: {settings.suricata_connector_mode}"
        )

    state = mark_connector_running(session, SURICATA_CONNECTOR_KEY)
    checkpoint = state.checkpoint if isinstance(state.checkpoint, dict) else {}
    metrics = default_connector_metrics(state.metrics if isinstance(state.metrics, dict) else None)
    offset, inode = parse_file_checkpoint(checkpoint)
    source_path = Path(settings.suricata_eve_file_path)

    lines: list[tuple[int, int, str]] = []
    final_offset = offset
    current_inode = inode
    for attempt in range(settings.suricata_retry_attempts + 1):
        try:
            lines, final_offset, current_inode = _read_new_eve_lines(
                source_path=source_path,
                checkpoint_offset=offset,
                checkpoint_inode=inode,
                max_events_per_cycle=max(1, settings.suricata_max_events_per_cycle),
            )
            break
        except OSError:
            if attempt >= settings.suricata_retry_attempts:
                raise
            time.sleep(settings.suricata_retry_backoff_seconds * (attempt + 1))

    cycle_ingested = 0
    cycle_duplicates = 0
    cycle_failed = 0

    for line_number, line_offset, line in lines:
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            cycle_failed += 1
            _record_malformed_line_failure(
                session,
                source_path=source_path,
                line_number=line_number,
                offset_before_read=line_offset,
                line_content=line,
                error_message=f"Invalid JSON: {exc.msg}",
            )
            continue

        if not isinstance(payload, dict):
            cycle_failed += 1
            _record_malformed_line_failure(
                session,
                source_path=source_path,
                line_number=line_number,
                offset_before_read=line_offset,
                line_content=line,
                error_message="Suricata line payload is not a JSON object.",
            )
            continue

        try:
            result = ingest_suricata_event(session, payload, actor=None)
            if result.status == "duplicate":
                cycle_duplicates += 1
            else:
                cycle_ingested += 1
        except HTTPException:
            cycle_failed += 1

    metrics["poll_count"] += 1
    metrics["total_fetched"] += len(lines)
    metrics["total_ingested"] += cycle_ingested
    metrics["total_duplicates"] += cycle_duplicates
    metrics["total_failed"] += cycle_failed

    checkpoint_payload = build_file_checkpoint(offset=final_offset, inode=current_inode)
    mark_connector_success(
        session,
        connector=SURICATA_CONNECTOR_KEY,
        checkpoint=checkpoint_payload,
        metrics=metrics,
    )
    return {
        "fetched": len(lines),
        "ingested": cycle_ingested,
        "duplicates": cycle_duplicates,
        "failed": cycle_failed,
    }


async def run_suricata_connector_forever(stop_event: asyncio.Event) -> None:
    settings = get_settings()
    while not stop_event.is_set():
        with SessionLocal() as session:
            try:
                await asyncio.to_thread(run_suricata_poll_cycle, session)
            except Exception as exc:  # pragma: no cover - guarded runtime branch
                mark_connector_error(
                    session,
                    connector=SURICATA_CONNECTOR_KEY,
                    error_message=str(exc),
                )
        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=max(5, settings.suricata_poll_interval_seconds),
            )
        except TimeoutError:
            continue


def get_suricata_connector_status(session: Session) -> SuricataConnectorStatusResponse:
    settings = get_settings()
    state = get_connector_state(session, SURICATA_CONNECTOR_KEY)
    checkpoint = (
        state.checkpoint if state is not None and isinstance(state.checkpoint, dict) else {}
    )
    offset, inode = parse_file_checkpoint(checkpoint)
    metrics = default_connector_metrics(
        state.metrics if state is not None and isinstance(state.metrics, dict) else None
    )
    return SuricataConnectorStatusResponse(
        connector=SURICATA_CONNECTOR_KEY,
        enabled=settings.suricata_connector_enabled,
        mode=settings.suricata_connector_mode,
        source_path=settings.suricata_eve_file_path,
        status=state.status if state is not None else "idle",
        last_success_at=state.last_success_at if state is not None else None,
        last_error_at=state.last_error_at if state is not None else None,
        last_error_message=state.last_error_message if state is not None else None,
        checkpoint_offset=offset,
        checkpoint_inode=inode,
        metrics=metrics,
    )
