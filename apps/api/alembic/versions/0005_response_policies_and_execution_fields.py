"""Add automated response policies and first-class execution outcome fields"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_response_policies"
down_revision = "0004_risk_scoring_runtime"
branch_labels = None
depends_on = None

response_policy_target_enum = postgresql.ENUM(
    "alert",
    "incident",
    name="responsepolicytarget",
)

response_action_type_enum = postgresql.ENUM(
    "block_ip",
    "disable_user",
    "quarantine_host_flag",
    "create_manual_review",
    "notify_admin",
    name="responseactiontype",
)

response_policy_target_column_enum = postgresql.ENUM(
    "alert",
    "incident",
    name="responsepolicytarget",
    create_type=False,
)

response_action_type_column_enum = postgresql.ENUM(
    "block_ip",
    "disable_user",
    "quarantine_host_flag",
    "create_manual_review",
    "notify_admin",
    name="responseactiontype",
    create_type=False,
)

detection_type_column_enum = postgresql.ENUM(
    "brute_force",
    "file_integrity_violation",
    "port_scan",
    "unauthorized_user_creation",
    name="detectiontype",
    create_type=False,
)

response_mode_column_enum = postgresql.ENUM(
    "dry-run",
    "live",
    name="responsemode",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    op.execute("ALTER TYPE responsestatus ADD VALUE IF NOT EXISTS 'warning'")
    response_policy_target_enum.create(bind, checkfirst=True)
    response_action_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "response_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("target", response_policy_target_column_enum, nullable=False),
        sa.Column("detection_type", detection_type_column_enum, nullable=False),
        sa.Column("min_risk_score", sa.Integer(), nullable=False),
        sa.Column("action_type", response_action_type_column_enum, nullable=False),
        sa.Column("mode", response_mode_column_enum, nullable=False, server_default="dry-run"),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_response_policies_enabled_lookup",
        "response_policies",
        ["enabled", "target", "detection_type", "min_risk_score"],
    )

    op.add_column(
        "response_actions",
        sa.Column("normalized_alert_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "response_actions",
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "response_actions",
        sa.Column("target_value", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "response_actions",
        sa.Column("result_summary", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "response_actions",
        sa.Column("result_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "response_actions",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "response_actions",
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_response_actions_normalized_alert_id_normalized_alerts",
        "response_actions",
        "normalized_alerts",
        ["normalized_alert_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_response_actions_policy_id_response_policies",
        "response_actions",
        "response_policies",
        ["policy_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_response_actions_policy_lookup",
        "response_actions",
        ["policy_id", "normalized_alert_id", "incident_id"],
    )

    op.execute(
        """
        UPDATE response_actions
        SET target_value = COALESCE(
            details ->> 'target',
            details ->> 'username',
            details ->> 'path',
            details ->> 'ip_address',
            details ->> 'hostname',
            details ->> 'asset_hostname'
        ),
        result_summary = COALESCE(
            details ->> 'summary',
            details ->> 'result',
            details ->> 'message',
            details ->> 'reason'
        ),
        result_message = COALESCE(
            details ->> 'message',
            details ->> 'reason',
            details ->> 'result'
        ),
        attempt_count = CASE
            WHEN status IN ('completed', 'failed') THEN 1
            ELSE 0
        END,
        last_attempted_at = COALESCE(executed_at, created_at)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_response_actions_policy_lookup", table_name="response_actions")
    op.drop_constraint(
        "fk_response_actions_policy_id_response_policies",
        "response_actions",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_response_actions_normalized_alert_id_normalized_alerts",
        "response_actions",
        type_="foreignkey",
    )
    op.drop_column("response_actions", "last_attempted_at")
    op.drop_column("response_actions", "attempt_count")
    op.drop_column("response_actions", "result_message")
    op.drop_column("response_actions", "result_summary")
    op.drop_column("response_actions", "target_value")
    op.drop_column("response_actions", "policy_id")
    op.drop_column("response_actions", "normalized_alert_id")

    op.drop_index("ix_response_policies_enabled_lookup", table_name="response_policies")
    op.drop_table("response_policies")

    op.execute("UPDATE response_actions SET status = 'failed' WHERE status = 'warning'")
    op.execute("ALTER TYPE responsestatus RENAME TO responsestatus_old")
    legacy_response_status_enum = postgresql.ENUM(
        "queued",
        "in_progress",
        "completed",
        "failed",
        name="responsestatus",
    )
    legacy_response_status_enum.create(bind, checkfirst=False)
    op.execute(
        """
        ALTER TABLE response_actions
        ALTER COLUMN status TYPE responsestatus
        USING status::text::responsestatus
        """
    )
    op.execute("DROP TYPE responsestatus_old")

    response_action_type_enum.drop(bind, checkfirst=True)
    response_policy_target_enum.drop(bind, checkfirst=True)
