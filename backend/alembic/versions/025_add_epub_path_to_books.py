"""Add epub_path column to books table.

Revision ID: 025
Revises: 024
Create Date: 2026-01-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "025"
down_revision: str | None = "024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add epub_path column to books table."""
    op.add_column(
        "books",
        sa.Column("epub_path", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    """Remove epub_path column from books table."""
    op.drop_column("books", "epub_path")
