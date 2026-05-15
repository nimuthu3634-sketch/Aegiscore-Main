from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ScoreMethod, enum_values

if TYPE_CHECKING:
    from app.models.normalized_alert import NormalizedAlert


# Stores the calculated risk score for a normalized alert.
class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Each risk score belongs to one normalized alert.
    normalized_alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Shows whether the score came from rules or the AI model.
    method: Mapped[ScoreMethod] = mapped_column(
        Enum(ScoreMethod, name="scoremethod", values_callable=enum_values),
        nullable=False,
    )

    model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    feature_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Links the score back to the alert it belongs to.
    normalized_alert: Mapped["NormalizedAlert"] = relationship(back_populates="risk_score")