from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ResponseMode, ResponseStatus, enum_values

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.notification_event import NotificationEvent
    from app.models.normalized_alert import NormalizedAlert
    from app.models.response_policy import ResponsePolicy
    from app.models.user import User


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    normalized_alert_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="SET NULL"),
        nullable=True,
    )
    policy_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("response_policies.id", ondelete="SET NULL"),
        nullable=True,
    )
    requested_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ResponseStatus] = mapped_column(
        Enum(ResponseStatus, name="responsestatus", values_callable=enum_values),
        default=ResponseStatus.QUEUED,
        nullable=False,
    )
    mode: Mapped[ResponseMode] = mapped_column(
        Enum(ResponseMode, name="responsemode", values_callable=enum_values),
        default=ResponseMode.LIVE,
        nullable=False,
    )
    target_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    details: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    incident: Mapped["Incident"] = relationship(back_populates="response_actions")
    normalized_alert: Mapped["NormalizedAlert | None"] = relationship(
        back_populates="response_actions"
    )
    policy: Mapped["ResponsePolicy | None"] = relationship(back_populates="response_actions")
    requested_by: Mapped["User | None"] = relationship(back_populates="requested_response_actions")
    notification_events: Mapped[list["NotificationEvent"]] = relationship(
        back_populates="response_action"
    )
