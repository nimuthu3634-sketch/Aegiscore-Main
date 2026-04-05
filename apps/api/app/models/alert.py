from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DetectionType

if TYPE_CHECKING:
    from app.models.incident import Incident


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    detection_type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType, name="detectiontype"),
        nullable=False,
    )
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship(back_populates="alert")
