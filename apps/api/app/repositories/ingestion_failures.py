from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ingestion_failure import IngestionFailure


class IngestionFailuresRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_source_external_id(
        self,
        *,
        source: str,
        external_id: str,
    ) -> IngestionFailure | None:
        statement = select(IngestionFailure).where(
            IngestionFailure.source == source,
            IngestionFailure.external_id == external_id,
        )
        return self.session.scalar(statement)

    def upsert_failure(
        self,
        *,
        source: str,
        external_id: str,
        detection_hint: str | None,
        error_type: str,
        error_message: str,
        raw_payload: dict,
    ) -> IngestionFailure:
        failure = self.get_by_source_external_id(
            source=source,
            external_id=external_id,
        )
        if failure is None:
            failure = IngestionFailure(
                source=source,
                external_id=external_id,
                detection_hint=detection_hint,
                error_type=error_type,
                error_message=error_message,
                raw_payload=raw_payload,
                retry_count=1,
                last_attempted_at=datetime.now(UTC),
            )
            self.session.add(failure)
            return failure

        failure.detection_hint = detection_hint
        failure.error_type = error_type
        failure.error_message = error_message
        failure.raw_payload = raw_payload
        failure.retry_count += 1
        failure.last_attempted_at = datetime.now(UTC)
        failure.resolved_at = None
        return failure

    def resolve_failure(
        self,
        *,
        source: str,
        external_id: str,
    ) -> IngestionFailure | None:
        failure = self.get_by_source_external_id(
            source=source,
            external_id=external_id,
        )
        if failure is None:
            return None

        failure.resolved_at = datetime.now(UTC)
        return failure
