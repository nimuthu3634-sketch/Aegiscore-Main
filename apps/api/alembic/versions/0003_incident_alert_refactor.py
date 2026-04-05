"""Refactor incidents to own many alerts via normalized_alerts.incident_id"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_incident_alert_refactor"
down_revision = "0002_workflow_actions_and_notes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("primary_alert_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "normalized_alerts",
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_foreign_key(
        "fk_incidents_primary_alert_id_normalized_alerts",
        "incidents",
        "normalized_alerts",
        ["primary_alert_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_normalized_alerts_incident_id_incidents",
        "normalized_alerts",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute(
        """
        UPDATE incidents
        SET primary_alert_id = normalized_alert_id
        WHERE primary_alert_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE normalized_alerts AS alerts
        SET incident_id = incidents.id
        FROM incidents
        WHERE incidents.normalized_alert_id = alerts.id
          AND alerts.incident_id IS NULL
        """
    )

    op.create_unique_constraint(
        "uq_incidents_primary_alert_id",
        "incidents",
        ["primary_alert_id"],
    )
    op.create_index(
        "ix_normalized_alerts_incident_id",
        "normalized_alerts",
        ["incident_id"],
    )

    op.drop_column("incidents", "normalized_alert_id")


def downgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("normalized_alert_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_incidents_normalized_alert_id_normalized_alerts",
        "incidents",
        "normalized_alerts",
        ["normalized_alert_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        UPDATE incidents AS incident
        SET normalized_alert_id = COALESCE(
            incident.primary_alert_id,
            (
                SELECT alert.id
                FROM normalized_alerts AS alert
                WHERE alert.incident_id = incident.id
                ORDER BY alert.created_at ASC, alert.id ASC
                LIMIT 1
            )
        )
        """
    )

    op.create_unique_constraint(
        "uq_incidents_normalized_alert_id",
        "incidents",
        ["normalized_alert_id"],
    )
    op.alter_column("incidents", "normalized_alert_id", nullable=False)

    op.drop_index("ix_normalized_alerts_incident_id", table_name="normalized_alerts")
    op.drop_constraint(
        "uq_incidents_primary_alert_id",
        "incidents",
        type_="unique",
    )
    op.drop_constraint(
        "fk_normalized_alerts_incident_id_incidents",
        "normalized_alerts",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_incidents_primary_alert_id_normalized_alerts",
        "incidents",
        type_="foreignkey",
    )
    op.drop_column("normalized_alerts", "incident_id")
    op.drop_column("incidents", "primary_alert_id")
