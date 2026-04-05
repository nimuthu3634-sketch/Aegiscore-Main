"""Initial AegisCore backend foundation"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

role_name_enum = postgresql.ENUM(
    "admin",
    "analyst",
    name="rolename",
)

detection_type_enum = postgresql.ENUM(
    "brute_force",
    "file_integrity_violation",
    "port_scan",
    "unauthorized_user_creation",
    name="detectiontype",
)

asset_criticality_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="assetcriticality",
)

alert_status_enum = postgresql.ENUM(
    "new",
    "investigating",
    "resolved",
    name="alertstatus",
)

incident_status_enum = postgresql.ENUM(
    "open",
    "investigating",
    "resolved",
    name="incidentstatus",
)

incident_priority_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="incidentpriority",
)

response_status_enum = postgresql.ENUM(
    "queued",
    "in_progress",
    "completed",
    "failed",
    name="responsestatus",
)

role_name_column_enum = postgresql.ENUM(
    "admin",
    "analyst",
    name="rolename",
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

asset_criticality_column_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="assetcriticality",
    create_type=False,
)

alert_status_column_enum = postgresql.ENUM(
    "new",
    "investigating",
    "resolved",
    name="alertstatus",
    create_type=False,
)

incident_status_column_enum = postgresql.ENUM(
    "open",
    "investigating",
    "resolved",
    name="incidentstatus",
    create_type=False,
)

incident_priority_column_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="incidentpriority",
    create_type=False,
)

response_status_column_enum = postgresql.ENUM(
    "queued",
    "in_progress",
    "completed",
    "failed",
    name="responsestatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    role_name_enum.create(bind, checkfirst=True)
    detection_type_enum.create(bind, checkfirst=True)
    asset_criticality_enum.create(bind, checkfirst=True)
    alert_status_enum.create(bind, checkfirst=True)
    incident_status_enum.create(bind, checkfirst=True)
    incident_priority_enum.create(bind, checkfirst=True)
    response_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "roles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", role_name_column_enum, nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("hostname", sa.String(length=255), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(length=45), nullable=False, unique=True),
        sa.Column("operating_system", sa.String(length=255), nullable=True),
        sa.Column("criticality", asset_criticality_column_enum, nullable=False),
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

    op.create_table(
        "raw_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("detection_type", detection_type_column_enum, nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "normalized_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "raw_alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("raw_alerts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "asset_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("detection_type", detection_type_column_enum, nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            alert_status_column_enum,
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "normalized_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "risk_scores",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "normalized_alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "incidents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "normalized_alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("normalized_alerts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "assigned_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "status",
            incident_status_column_enum,
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "priority",
            incident_priority_column_enum,
            nullable=False,
            server_default="medium",
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

    op.create_table(
        "response_actions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "requested_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            response_status_column_enum,
            nullable=False,
            server_default="queued",
        ),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index("ix_raw_alerts_received_at", "raw_alerts", ["received_at"])
    op.create_index("ix_normalized_alerts_created_at", "normalized_alerts", ["created_at"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])
    op.create_index("ix_response_actions_created_at", "response_actions", ["created_at"])
    op.create_index("ix_audit_logs_entity_lookup", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_audit_logs_entity_lookup", table_name="audit_logs")
    op.drop_index("ix_response_actions_created_at", table_name="response_actions")
    op.drop_index("ix_incidents_created_at", table_name="incidents")
    op.drop_index("ix_normalized_alerts_created_at", table_name="normalized_alerts")
    op.drop_index("ix_raw_alerts_received_at", table_name="raw_alerts")

    op.drop_table("audit_logs")
    op.drop_table("response_actions")
    op.drop_table("incidents")
    op.drop_table("risk_scores")
    op.drop_table("normalized_alerts")
    op.drop_table("raw_alerts")
    op.drop_table("assets")
    op.drop_table("users")
    op.drop_table("roles")

    response_status_enum.drop(bind, checkfirst=True)
    incident_priority_enum.drop(bind, checkfirst=True)
    incident_status_enum.drop(bind, checkfirst=True)
    alert_status_enum.drop(bind, checkfirst=True)
    asset_criticality_enum.drop(bind, checkfirst=True)
    detection_type_enum.drop(bind, checkfirst=True)
    role_name_enum.drop(bind, checkfirst=True)
