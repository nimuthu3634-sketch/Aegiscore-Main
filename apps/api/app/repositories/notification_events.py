from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.notification_event import NotificationEvent


@dataclass(frozen=True)
class NotificationBellRow:
    id: uuid.UUID
    incident_id: uuid.UUID
    incident_title: str
    trigger_type: str
    trigger_value: str
    subject: str
    status: str
    created_at: datetime
    read: bool


class NotificationEventsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def count_unread(self) -> int:
        stmt = select(func.count()).select_from(NotificationEvent).where(
            NotificationEvent.read.is_(False)
        )
        return int(self.session.scalar(stmt) or 0)

    def count_matching(self, *, unread_only: bool) -> int:
        stmt = select(func.count()).select_from(NotificationEvent)
        if unread_only:
            stmt = stmt.where(NotificationEvent.read.is_(False))
        return int(self.session.scalar(stmt) or 0)

    def list_recent(
        self,
        *,
        limit: int,
        unread_only: bool,
    ) -> list[NotificationBellRow]:
        stmt = (
            select(
                NotificationEvent.id,
                NotificationEvent.incident_id,
                Incident.title,
                NotificationEvent.trigger_type,
                NotificationEvent.trigger_value,
                NotificationEvent.subject,
                NotificationEvent.status,
                NotificationEvent.created_at,
                NotificationEvent.read,
            )
            .join(Incident, Incident.id == NotificationEvent.incident_id)
            .order_by(NotificationEvent.created_at.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(NotificationEvent.read.is_(False))
        rows = self.session.execute(stmt).all()
        return [
            NotificationBellRow(
                id=r.id,
                incident_id=r.incident_id,
                incident_title=r.title,
                trigger_type=r.trigger_type,
                trigger_value=r.trigger_value,
                subject=r.subject,
                status=r.status,
                created_at=r.created_at,
                read=bool(r.read),
            )
            for r in rows
        ]

    def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = (
            update(NotificationEvent)
            .where(NotificationEvent.id == notification_id)
            .values(read=True, read_by_user_id=user_id)
        )
        result = self.session.execute(stmt)
        return result.rowcount > 0

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        stmt = (
            update(NotificationEvent)
            .where(NotificationEvent.read.is_(False))
            .values(read=True, read_by_user_id=user_id)
        )
        result = self.session.execute(stmt)
        return int(result.rowcount or 0)
