"""Add ingestion failure logging and raw alert dedupe support"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_ingestion_pipeline"
down_revision = "0005_response_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_failures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("detection_hint", sa.String(length=64), nullable=True),
        sa.Column("error_type", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_attempted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "source",
            "external_id",
            name="uq_ingestion_failures_source_external_id",
        ),
    )
    op.create_index(
        "ix_ingestion_failures_retry_lookup",
        "ingestion_failures",
        ["source", "last_attempted_at"],
    )

    op.create_unique_constraint(
        "uq_raw_alerts_source_external_id",
        "raw_alerts",
        ["source", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_raw_alerts_source_external_id",
        "raw_alerts",
        type_="unique",
    )
    op.drop_index("ix_ingestion_failures_retry_lookup", table_name="ingestion_failures")
    op.drop_table("ingestion_failures")
