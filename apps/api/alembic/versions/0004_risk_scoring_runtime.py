"""Add persisted risk scoring metadata and normalize score range to 0-100"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_risk_scoring_runtime"
down_revision = "0003_incident_alert_refactor"
branch_labels = None
depends_on = None

score_method_enum = postgresql.ENUM(
    "baseline_rules",
    "sklearn_model",
    name="scoremethod",
)

score_method_column_enum = postgresql.ENUM(
    "baseline_rules",
    "sklearn_model",
    name="scoremethod",
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


def upgrade() -> None:
    bind = op.get_bind()
    score_method_enum.create(bind, checkfirst=True)

    op.add_column(
        "risk_scores",
        sa.Column("priority_label", incident_priority_column_enum, nullable=True),
    )
    op.add_column(
        "risk_scores",
        sa.Column("scoring_method", score_method_column_enum, nullable=True),
    )
    op.add_column(
        "risk_scores",
        sa.Column("baseline_version", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "risk_scores",
        sa.Column("model_version", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "risk_scores",
        sa.Column("explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "risk_scores",
        sa.Column("feature_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.execute(
        """
        UPDATE risk_scores
        SET score = CASE
            WHEN score <= 1 THEN ROUND((score * 100.0)::numeric, 2)
            ELSE score
        END
        """
    )

    op.execute(
        """
        UPDATE risk_scores
        SET priority_label = CASE
            WHEN score >= 85 THEN 'critical'::incidentpriority
            WHEN score >= 70 THEN 'high'::incidentpriority
            WHEN score >= 45 THEN 'medium'::incidentpriority
            ELSE 'low'::incidentpriority
        END,
        scoring_method = 'baseline_rules'::scoremethod,
        baseline_version = 'legacy_seed_v0',
        explanation = jsonb_build_object(
            'label', 'Deterministic baseline score',
            'summary', CONCAT('Legacy score backfilled at ', ROUND(score), '/100.'),
            'rationale', reasoning,
            'factors', jsonb_build_array('Backfilled from pre-runtime risk score data.'),
            'score', ROUND(score),
            'priority_label', CASE
                WHEN score >= 85 THEN 'critical'
                WHEN score >= 70 THEN 'high'
                WHEN score >= 45 THEN 'medium'
                ELSE 'low'
            END,
            'scoring_method', 'baseline_rules',
            'baseline_version', 'legacy_seed_v0'
        ),
        feature_snapshot = jsonb_build_object(
            'backfilled', true,
            'migration', '0004_risk_scoring_runtime'
        )
        """
    )

    op.alter_column("risk_scores", "priority_label", nullable=False)
    op.alter_column("risk_scores", "scoring_method", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.execute(
        """
        UPDATE risk_scores
        SET score = CASE
            WHEN score > 1 THEN ROUND((score / 100.0)::numeric, 4)
            ELSE score
        END
        """
    )

    op.drop_column("risk_scores", "feature_snapshot")
    op.drop_column("risk_scores", "explanation")
    op.drop_column("risk_scores", "model_version")
    op.drop_column("risk_scores", "baseline_version")
    op.drop_column("risk_scores", "scoring_method")
    op.drop_column("risk_scores", "priority_label")

    score_method_enum.drop(bind, checkfirst=True)
