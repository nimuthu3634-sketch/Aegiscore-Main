from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AgentStatus, AssetCriticality, enum_values

if TYPE_CHECKING:
    from app.models.containment_flag import ContainmentFlag
    from app.models.incident import Incident
    from app.models.normalized_alert import NormalizedAlert


# Represents a monitored endpoint or server in the SOC platform.
class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Basic asset identity and network details.
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    operating_system: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Used to show the importance and current agent state of the asset.
    criticality: Mapped[AssetCriticality] = mapped_column(
        Enum(AssetCriticality, name="assetcriticality", values_callable=enum_values),
        nullable=False,
        default=AssetCriticality.MEDIUM,
    )
    agent_status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agentstatus", values_callable=enum_values),
        nullable=False,
        default=AgentStatus.UNKNOWN,
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

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

    # Relationships connect this asset with alerts, incidents, and containment records.
    alerts: Mapped[list["NormalizedAlert"]] = relationship(back_populates="asset")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="asset")
    containment_flags: Mapped[list["ContainmentFlag"]] = relationship(
        back_populates="asset",
        cascade="all, delete-orphan",
    )