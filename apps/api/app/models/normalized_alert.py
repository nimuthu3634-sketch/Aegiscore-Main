from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AlertStatus, DetectionType, enum_values

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.incident import Incident
    from app.models.raw_alert import RawAlert
    from app.models.risk_score import RiskScore


class NormalizedAlert(Base):
    __tablename__ = "normalized_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    raw_alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_alerts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detection_type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType, name="detectiontype", values_callable=enum_values),
        nullable=False,
    )
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alertstatus", values_callable=enum_values),
        default=AlertStatus.NEW,
        nullable=False,
    )
    normalized_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    raw_alert: Mapped["RawAlert"] = relationship(back_populates="normalized_alert")
    asset: Mapped["Asset | None"] = relationship(back_populates="normalized_alerts")
    risk_score: Mapped["RiskScore | None"] = relationship(
        back_populates="normalized_alert",
        uselist=False,
    )
    incident: Mapped["Incident | None"] = relationship(
        back_populates="normalized_alert",
        uselist=False,
    )
