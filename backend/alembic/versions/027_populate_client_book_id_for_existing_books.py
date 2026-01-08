"""Populate client_book_id for existing books using MD5 hash.

This generates the same hash that KOReader would generate:
    md5(title || "|" || author)

Where NULL values are treated as empty strings.

Revision ID: 027
Revises: 026
Create Date: 2026-01-08

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "027"
down_revision: str | None = "026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Populate client_book_id for existing books without one.

    Uses the same hash algorithm as KOReader:
        local input = (title or "") .. "|" .. (author or "")
        return md5(input)
    """
    op.execute(
        """
        UPDATE books
        SET client_book_id = md5(COALESCE(title, '') || '|' || COALESCE(author, ''))
        WHERE client_book_id IS NULL
        """
    )


def downgrade() -> None:
    """Clear client_book_id values that were auto-generated.

    Note: This cannot distinguish between auto-generated and manually-set values,
    so we simply set all to NULL. This is acceptable since the column was nullable
    before this migration.
    """
    op.execute(
        """
        UPDATE books
        SET client_book_id = NULL
        """
    )
