from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


# Stores sync/checkpoint details for external integrations like Wazuh or Suricata.
class IntegrationState(Base):
    __tablename__ = "integration_states"

    # Integration name is used as the unique key, for example "wazuh" or "suricata".
    integration_name: Mapped[str] = mapped_column(String(64), primary_key=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="unknown")
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Checkpoint keeps the last processed position/time so duplicate ingestion can be avoided.
    checkpoint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

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