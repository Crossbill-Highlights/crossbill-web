"""Drop cover column from books table.

The cover URL was deterministic (/api/v1/books/{id}/cover) and derived from the
book ID at runtime. It is no longer stored in the database.

Revision ID: 046
Revises: 045
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "046"
down_revision: str | Sequence[str] | None = "045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("books", "cover")


def downgrade() -> None:
    op.add_column("books", sa.Column("cover", sa.String(500), nullable=True))
