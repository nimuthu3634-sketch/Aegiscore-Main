# AegisCore student note: Alembic migration for user TOTP MFA fields.

"""Add TOTP MFA columns to users."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_user_totp_mfa"
down_revision = "0010_scoremethod_tensorflow"
branch_labels = None
depends_on = None


# Applies this migration when moving the database forward.
def upgrade() -> None:
    # Adds a new column required by the updated schema.
    op.add_column(
        "users",
        sa.Column("mfa_secret", sa.String(length=128), nullable=True),
    )
    # Adds a new column required by the updated schema.
    op.add_column(
        "users",
        sa.Column(
            "mfa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.alter_column("users", "mfa_enabled", server_default=None)


# Reverts this migration if the database needs to roll back.
def downgrade() -> None:
    # Removes the column during rollback.
    op.drop_column("users", "mfa_enabled")
    # Removes the column during rollback.
    op.drop_column("users", "mfa_secret")
