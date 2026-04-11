"""Add tensorflow_model to scoremethod enum for TensorFlow risk scoring."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_scoremethod_tensorflow"
down_revision = "0009_containment_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL 15+ supports IF NOT EXISTS; older versions may need a one-off manual ALTER.
    op.execute(
        sa.text("ALTER TYPE scoremethod ADD VALUE IF NOT EXISTS 'tensorflow_model'")
    )


def downgrade() -> None:
    # Enum values cannot be dropped safely across PostgreSQL versions; no-op.
    pass
