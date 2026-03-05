"""Add end_position column to books table.

Revision ID: 043
Revises: 042
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "043"
down_revision: str | Sequence[str] | None = "042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column("end_position", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("books", "end_position")
