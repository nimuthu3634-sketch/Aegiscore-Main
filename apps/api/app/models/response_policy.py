from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    DetectionType,
    ResponseActionType,
    ResponseMode,
    ResponsePolicyTarget,
    enum_values,
)

if TYPE_CHECKING:
    from app.models.response_action import ResponseAction


class ResponsePolicy(Base):
    __tablename__ = "response_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    target: Mapped[ResponsePolicyTarget] = mapped_column(
        Enum(ResponsePolicyTarget, name="responsepolicytarget", values_callable=enum_values),
        nullable=False,
    )
    detection_type: Mapped[DetectionType] = mapped_column(
        Enum(DetectionType, name="detectiontype", values_callable=enum_values),
        nullable=False,
    )
    min_risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[ResponseActionType] = mapped_column(
        Enum(ResponseActionType, name="responseactiontype", values_callable=enum_values),
        nullable=False,
    )
    mode: Mapped[ResponseMode] = mapped_column(
        Enum(ResponseMode, name="responsemode", values_callable=enum_values),
        nullable=False,
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
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

    response_actions: Mapped[list["ResponseAction"]] = relationship(back_populates="policy")
