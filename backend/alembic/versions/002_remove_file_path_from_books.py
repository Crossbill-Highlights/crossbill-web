"""Remove file_path from books table.

Revision ID: 002
Revises: 001
Create Date: 2025-11-09 10:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Remove file_path column from books table."""
    # Drop the unique index first
    op.drop_index("ix_books_file_path", table_name="books")

    # Drop the file_path column
    op.drop_column("books", "file_path")


def downgrade() -> None:
    """Add file_path column back to books table."""
    # Add the file_path column back
    op.add_column(
        "books",
        sa.Column("file_path", sa.String(length=1000), nullable=True),
    )

    # Create the index
    op.create_index("ix_books_file_path", "books", ["file_path"], unique=True)

    # Note: In a real scenario, you'd need to populate file_path values here
    # This downgrade migration assumes data loss is acceptable
