from datetime import datetime
from uuid import UUID

from app.schemas.base import APIModel


# One notification item shown in the frontend notification dropdown.
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


# Response returned when loading recent notifications.
class RecentNotificationsResponse(APIModel):
    items: list[RecentNotificationItem]
    unread_count: int
    total: int