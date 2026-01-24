"""Allow duplicate chapter names at different hierarchy levels.

Revision ID: 033
Revises: 032
Create Date: 2026-01-24

Changes the unique constraint from (book_id, name) to (book_id, parent_id, name)
to allow chapters with the same name under different parent chapters.

Example: Both "Harjoitukset" under Part I and "Harjoitukset" under Part II
can now coexist in the database.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "033"
down_revision: str | None = "032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace chapter unique constraint to allow duplicate names at different hierarchy levels."""
    # Drop the old constraint: (book_id, name)
    op.drop_constraint("uq_chapter_per_book", "chapters", type_="unique")

    # Create new constraint: (book_id, parent_id, name)
    # This allows duplicate names under different parents
    op.create_unique_constraint("uq_chapter_per_book", "chapters", ["book_id", "parent_id", "name"])


def downgrade() -> None:
    """Revert to original constraint (book_id, name)."""
    # Drop the new constraint
    op.drop_constraint("uq_chapter_per_book", "chapters", type_="unique")

    # Recreate the original constraint
    # WARNING: This will fail if duplicate (book_id, name) pairs exist
    op.create_unique_constraint("uq_chapter_per_book", "chapters", ["book_id", "name"])
