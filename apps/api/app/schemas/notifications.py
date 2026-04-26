from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel


class RecentNotificationItem(APIModel):
    id: UUID
    incident_id: UUID
    incident_title: str
    trigger_type: str
    trigger_value: str
    subject: str
    status: str
    created_at: datetime
    read: bool


class RecentNotificationsResponse(APIModel):
    items: list[RecentNotificationItem]
    unread_count: int = Field(ge=0)
    total: int = Field(ge=0)
