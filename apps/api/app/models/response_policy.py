from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ResponsePolicyTarget, enum_values

if TYPE_CHECKING:
    from app.models.response_action import ResponseAction


# Stores rules that decide when automated response actions should be triggered.
class ResponsePolicy(Base):
    __tablename__ = "response_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Defines whether this policy applies to alerts or incidents.
    target_type: Mapped[ResponsePolicyTarget] = mapped_column(
        Enum(ResponsePolicyTarget, name="responsepolicytarget", values_callable=enum_values),
        nullable=False,
    )

    # Conditions and actions are stored as JSON so the policy can stay flexible.
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actions: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

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

    # Shows which response actions were created from this policy.
    response_actions: Mapped[list["ResponseAction"]] = relationship(back_populates="policy")