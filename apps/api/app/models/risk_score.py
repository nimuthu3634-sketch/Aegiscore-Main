from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import IncidentPriority, ScoreMethod, enum_values

if TYPE_CHECKING:
    from app.models.normalized_alert import NormalizedAlert


class RiskScore(Base):
    __tablename__ = "risk_scores"

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
    score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority_label: Mapped[IncidentPriority] = mapped_column(
        Enum(IncidentPriority, name="incidentpriority", values_callable=enum_values),
        default=IncidentPriority.MEDIUM,
        nullable=False,
    )
    scoring_method: Mapped[ScoreMethod] = mapped_column(
        Enum(ScoreMethod, name="scoremethod", values_callable=enum_values),
        default=ScoreMethod.BASELINE_RULES,
        nullable=False,
    )
    baseline_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    feature_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    normalized_alert: Mapped["NormalizedAlert"] = relationship(back_populates="risk_score")
