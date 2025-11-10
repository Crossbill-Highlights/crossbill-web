"""Add deleted_at column to highlights table for soft deletes.

Revision ID: 004
Revises: 003
Create Date: 2025-11-10 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add deleted_at column to highlights table."""
    op.add_column(
        "highlights",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Add index for querying non-deleted highlights efficiently
    op.create_index(
        "ix_highlights_deleted_at",
        "highlights",
        ["deleted_at"],
    )


def downgrade() -> None:
    """Remove deleted_at column from highlights table."""
    op.drop_index("ix_highlights_deleted_at", table_name="highlights")
    op.drop_column("highlights", "deleted_at")
