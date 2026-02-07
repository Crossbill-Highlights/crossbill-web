"""Fix users table ID sequence.

This migration fixes the users_id_seq sequence to be in sync with the
maximum user ID in the database. This is necessary because migration 013
created the admin user with an explicit ID (id=1), which doesn't advance
the PostgreSQL sequence. Without this fix, attempting to create new users
results in primary key conflicts.

Revision ID: 249c9ffd1b90
Revises: 036
Create Date: 2026-02-01 21:47:13.455366

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "249c9ffd1b90"
down_revision: str | Sequence[str] | None = "036"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Fix the users_id_seq sequence to match the maximum user ID."""
    # Set the sequence to max(id) + 1
    # The 'false' parameter means the sequence will return this value on the NEXT nextval() call
    # This ensures that when a new user is created, it gets an ID that doesn't conflict
    op.execute(
        sa.text(
            "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 0) + 1, false)"
        )
    )


def downgrade() -> None:
    """Downgrade not applicable for sequence fixes.

    Sequences are auto-incrementing, so there's no meaningful downgrade.
    The sequence will remain at its current value.
    """
