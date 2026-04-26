"""Add read state columns to notification_events."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_notification_read_state"
down_revision = "0011_user_totp_mfa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notification_events",
        sa.Column(
            "read",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "notification_events",
        sa.Column(
            "read_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_notification_events_read_created",
        "notification_events",
        ["read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_events_read_created", table_name="notification_events")
    op.drop_column("notification_events", "read_by_user_id")
    op.drop_column("notification_events", "read")
