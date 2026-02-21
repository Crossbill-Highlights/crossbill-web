"""Add chapter_id column to flashcards table.

Revision ID: 042
Revises: 041
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "042"
down_revision: str | Sequence[str] | None = "041"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "flashcards",
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("flashcards", "chapter_id")
