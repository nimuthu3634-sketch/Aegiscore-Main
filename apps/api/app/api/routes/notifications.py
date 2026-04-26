from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, DbSession
from app.repositories.notification_events import NotificationEventsRepository
from app.schemas.notifications import RecentNotificationItem, RecentNotificationsResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/recent", response_model=RecentNotificationsResponse)
def list_recent_notifications(
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    unread_only: Annotated[bool, Query()] = False,
) -> RecentNotificationsResponse:
    repo = NotificationEventsRepository(db)
    rows = repo.list_recent(limit=limit, unread_only=unread_only)
    unread_count = repo.count_unread()
    total = repo.count_matching(unread_only=unread_only)
    items = [
        RecentNotificationItem(
            id=r.id,
            incident_id=r.incident_id,
            incident_title=r.incident_title,
            trigger_type=r.trigger_type,
            trigger_value=r.trigger_value,
            subject=r.subject,
            status=r.status,
            created_at=r.created_at,
            read=r.read,
        )
        for r in rows
    ]
    return RecentNotificationsResponse(
        items=items,
        unread_count=unread_count,
        total=total,
    )


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    repo = NotificationEventsRepository(db)
    repo.mark_all_read(current_user.id)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    repo = NotificationEventsRepository(db)
    updated = repo.mark_read(notification_id, current_user.id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
