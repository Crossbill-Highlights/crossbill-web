"""Add note_id column to flashcards table.

Revision ID: 056
Revises: 055
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "056"
down_revision: str | Sequence[str] | None = "055"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # SET NULL (not CASCADE): notes are hard-deleted, and deleting a note
    # should not destroy study material — the flashcard survives as a
    # book-level card.
    op.add_column(
        "flashcards",
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("flashcards", "note_id")
