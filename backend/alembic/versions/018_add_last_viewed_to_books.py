"""Add last_viewed column to books for tracking recently viewed books.

This migration adds a nullable last_viewed timestamp column to the books table.
The column is updated whenever a user views a book's details.

Revision ID: 018
Revises: 017
Create Date: 2025-12-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: str | None = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add last_viewed column to books table."""
    op.add_column(
        "books",
        sa.Column("last_viewed", sa.DateTime(timezone=True), nullable=True),
    )
    # Add index for efficient sorting by last_viewed
    op.create_index("ix_books_last_viewed", "books", ["last_viewed"])


def downgrade() -> None:
    """Remove last_viewed column from books table."""
    op.drop_index("ix_books_last_viewed", table_name="books")
    op.drop_column("books", "last_viewed")
