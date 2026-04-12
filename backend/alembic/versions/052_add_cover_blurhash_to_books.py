"""add_cover_blurhash_to_books

Revision ID: 052
Revises: 051
Create Date: 2026-04-12 20:23:33.953700

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "052"
down_revision: str | Sequence[str] | None = "051"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("books", sa.Column("cover_blurhash", sa.String(40), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("books", "cover_blurhash")
