"""Initial AegisCore schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

detection_type_enum = postgresql.ENUM(
    "brute_force",
    "file_integrity_violation",
    "port_scan",
    "unauthorized_user_creation",
    name="detectiontype",
)

incident_status_enum = postgresql.ENUM(
    "open",
    "investigating",
    "resolved",
    name="incidentstatus",
)

response_status_enum = postgresql.ENUM(
    "queued",
    "completed",
    "failed",
    name="responsestatus",
)

detection_type_column_enum = postgresql.ENUM(
    "brute_force",
    "file_integrity_violation",
    "port_scan",
    "unauthorized_user_creation",
    name="detectiontype",
    create_type=False,
)

incident_status_column_enum = postgresql.ENUM(
    "open",
    "investigating",
    "resolved",
    name="incidentstatus",
    create_type=False,
)

response_status_column_enum = postgresql.ENUM(
    "queued",
    "completed",
    "failed",
    name="responsestatus",
    create_type=False,
)


def upgrade() -> None:
    detection_type_enum.create(op.get_bind(), checkfirst=True)
    incident_status_enum.create(op.get_bind(), checkfirst=True)
    response_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("detection_type", detection_type_column_enum, nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column(
            "normalized_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "raw_payload",
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
        "incidents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alerts.id", ondelete="CASCADE"),
            nullable=False,
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
            sa.ForeignKey("incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_name", sa.String(length=255), nullable=False),
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
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("actor", sa.String(length=255), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("subject_type", sa.String(length=255), nullable=False),
        sa.Column("subject_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_metadata",
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


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("response_actions")
    op.drop_table("incidents")
    op.drop_table("alerts")

    response_status_enum.drop(op.get_bind(), checkfirst=True)
    incident_status_enum.drop(op.get_bind(), checkfirst=True)
    detection_type_enum.drop(op.get_bind(), checkfirst=True)
