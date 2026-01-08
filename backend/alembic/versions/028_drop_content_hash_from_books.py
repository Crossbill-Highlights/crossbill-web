"""Drop content_hash column from books table.

The content_hash column is no longer needed as book deduplication
is now handled using client_book_id.

Revision ID: 028
Revises: 027
Create Date: 2026-01-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "028"
down_revision: str | None = "027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop content_hash column from books."""
    # Drop the unique constraint first
    op.drop_constraint("uq_book_content_hash", "books", type_="unique")

    # Drop the index
    op.drop_index("ix_books_content_hash", table_name="books")

    # Drop the column
    op.drop_column("books", "content_hash")


def downgrade() -> None:
    """Re-add content_hash column to books."""
    # Add the column back (nullable initially)
    op.add_column(
        "books",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # Populate content_hash using MD5 of title|author (matching the original logic)
    op.execute(
        """
        UPDATE books
        SET content_hash = encode(sha256((COALESCE(title, '') || '|' || COALESCE(author, ''))::bytea), 'hex')
        """
    )

    # Make it non-nullable
    op.alter_column("books", "content_hash", nullable=False)

    # Recreate the index
    op.create_index("ix_books_content_hash", "books", ["content_hash"])

    # Recreate the unique constraint
    op.create_unique_constraint("uq_book_content_hash", "books", ["user_id", "content_hash"])
