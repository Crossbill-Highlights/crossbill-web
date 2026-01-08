"""Add client_book_id column to books table.

Revision ID: 026
Revises: 025
Create Date: 2026-01-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "026"
down_revision: str | None = "025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add client_book_id column with partial unique constraint."""
    # Add nullable column (existing books won't have it)
    op.add_column(
        "books",
        sa.Column("client_book_id", sa.String(length=255), nullable=True),
    )

    # Add index for efficient lookups
    op.create_index("ix_books_client_book_id", "books", ["client_book_id"])

    # Add partial unique constraint (only when client_book_id is not null)
    # This allows multiple NULL values while enforcing uniqueness for non-null values
    op.execute("""
        CREATE UNIQUE INDEX uq_book_client_book_id
        ON books (user_id, client_book_id)
        WHERE client_book_id IS NOT NULL
    """)


def downgrade() -> None:
    """Remove client_book_id column and constraints."""
    op.execute("DROP INDEX IF EXISTS uq_book_client_book_id")
    op.drop_index("ix_books_client_book_id", table_name="books")
    op.drop_column("books", "client_book_id")
