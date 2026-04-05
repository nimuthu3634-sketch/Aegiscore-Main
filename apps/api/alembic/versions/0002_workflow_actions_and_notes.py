"""Add workflow actions, richer incident states, response mode, and analyst notes"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_workflow_actions_and_notes"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

response_mode_enum = postgresql.ENUM(
    "dry-run",
    "live",
    name="responsemode",
)

note_target_type_enum = postgresql.ENUM(
    "alert",
    "incident",
    name="notetargettype",
)

response_mode_column_enum = postgresql.ENUM(
    "dry-run",
    "live",
    name="responsemode",
    create_type=False,
)

note_target_type_column_enum = postgresql.ENUM(
    "alert",
    "incident",
    name="notetargettype",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_enum
                WHERE enumlabel = 'open'
                AND enumtypid = 'incidentstatus'::regtype
            ) THEN
                ALTER TYPE incidentstatus RENAME VALUE 'open' TO 'new';
            END IF;
        END
        $$;
        """
    )
    op.execute("ALTER TYPE incidentstatus ADD VALUE IF NOT EXISTS 'triaged'")
    op.execute("ALTER TYPE incidentstatus ADD VALUE IF NOT EXISTS 'contained'")
    op.execute("ALTER TYPE incidentstatus ADD VALUE IF NOT EXISTS 'false_positive'")
    op.alter_column("incidents", "status", server_default="new")

    response_mode_enum.create(bind, checkfirst=True)
    note_target_type_enum.create(bind, checkfirst=True)

    op.add_column(
        "response_actions",
        sa.Column("mode", response_mode_column_enum, nullable=True),
    )
    op.execute(
        """
        UPDATE response_actions
        SET mode = CASE
            WHEN details ->> 'mode' IN ('dry-run', 'dry_run') THEN 'dry-run'
            ELSE 'live'
        END::responsemode
        """
    )
    op.alter_column(
        "response_actions",
        "mode",
        nullable=False,
        server_default="live",
    )

    op.create_table(
        "analyst_notes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("target_type", note_target_type_column_enum, nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "author_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
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
        "ix_analyst_notes_target_lookup",
        "analyst_notes",
        ["target_type", "target_id", "created_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_analyst_notes_target_lookup", table_name="analyst_notes")
    op.drop_table("analyst_notes")

    op.drop_column("response_actions", "mode")
    response_mode_enum.drop(bind, checkfirst=True)
    note_target_type_enum.drop(bind, checkfirst=True)

    op.execute(
        """
        UPDATE incidents
        SET status = 'investigating'
        WHERE status IN ('triaged', 'contained')
        """
    )
    op.execute(
        """
        UPDATE incidents
        SET status = 'resolved'
        WHERE status = 'false_positive'
        """
    )
    op.alter_column("incidents", "status", server_default=None)
    op.execute("ALTER TYPE incidentstatus RENAME TO incidentstatus_new")
    op.execute(
        """
        CREATE TYPE incidentstatus AS ENUM ('open', 'investigating', 'resolved')
        """
    )
    op.execute(
        """
        ALTER TABLE incidents
        ALTER COLUMN status TYPE incidentstatus
        USING (
            CASE
                WHEN status::text = 'new' THEN 'open'
                ELSE status::text
            END
        )::incidentstatus
        """
    )
    op.alter_column("incidents", "status", server_default="open")
    op.execute("DROP TYPE incidentstatus_new")
