from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DetectionType, enum_values

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.normalized_alert import NormalizedAlert


# Stores the original alert/event data received from tools like Wazuh or Suricata.
class RawAlert(Base):
    __tablename__ = "raw_alerts"
    __table_args__ = (
        # Prevents saving the same external alert more than once.
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_raw_alerts_source_external_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Links the raw alert to the affected asset when it is known.
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detection_type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType, name="detectiontype", values_callable=enum_values),
        nullable=False,
    )
    severity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Keeps the full original payload for evidence and debugging.
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships connect the raw alert to the asset and its normalized version.
    asset: Mapped["Asset | None"] = relationship(back_populates="raw_alerts")
    normalized_alert: Mapped["NormalizedAlert | None"] = relationship(
        back_populates="raw_alert",
        uselist=False,
    )