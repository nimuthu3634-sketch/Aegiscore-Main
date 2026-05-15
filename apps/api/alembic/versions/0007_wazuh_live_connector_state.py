# AegisCore student note: Alembic migration for storing Wazuh live connector checkpoint state.

"""Add connector state table for live Wazuh polling"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_wazuh_connector_state"
down_revision = "0006_ingestion_pipeline"
branch_labels = None
depends_on = None


# Applies this migration when moving the database forward.
def upgrade() -> None:
    # Creates a database table needed by the application.
    op.create_table(
        "integration_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("connector", sa.String(length=64), nullable=False, unique=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="idle"),
        sa.Column(
            "checkpoint",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_message", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


# Reverts this migration if the database needs to roll back.
def downgrade() -> None:
    # Drops the table when rolling this migration back.
    op.drop_table("integration_states")
