from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import AssetCriticality, enum_values

if TYPE_CHECKING:
    from app.models.normalized_alert import NormalizedAlert
    from app.models.raw_alert import RawAlert


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    hostname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    operating_system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[AssetCriticality] = mapped_column(
        Enum(AssetCriticality, name="assetcriticality", values_callable=enum_values),
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

    raw_alerts: Mapped[list["RawAlert"]] = relationship(back_populates="asset")
    normalized_alerts: Mapped[list["NormalizedAlert"]] = relationship(back_populates="asset")
