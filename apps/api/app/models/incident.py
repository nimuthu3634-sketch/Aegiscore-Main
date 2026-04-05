from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import IncidentPriority, IncidentStatus, enum_values

if TYPE_CHECKING:
    from app.models.normalized_alert import NormalizedAlert
    from app.models.response_action import ResponseAction
    from app.models.user import User


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    normalized_alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incidentstatus", values_callable=enum_values),
        default=IncidentStatus.NEW,
        nullable=False,
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        Enum(IncidentPriority, name="incidentpriority", values_callable=enum_values),
        default=IncidentPriority.MEDIUM,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    normalized_alert: Mapped["NormalizedAlert"] = relationship(back_populates="incident")
    assigned_user: Mapped["User | None"] = relationship(back_populates="assigned_incidents")
    response_actions: Mapped[list["ResponseAction"]] = relationship(back_populates="incident")
