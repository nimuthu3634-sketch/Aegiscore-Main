"""${message}"""

# Template used by Alembic when a new migration revision is generated.
# The values below are filled automatically for each migration file.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

# Alembic operation helpers are used inside generated upgrade/downgrade functions.
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}


def upgrade() -> None:
    # Place schema changes that should be applied to the database here.
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    # Place reverse schema changes here so the migration can be rolled back.
    ${downgrades if downgrades else "pass"}

