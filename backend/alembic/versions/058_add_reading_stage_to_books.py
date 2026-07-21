"""add_reading_stage_to_books

Revision ID: 058
Revises: 057
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "058"
down_revision: str | Sequence[str] | None = "057"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("books", sa.Column("reading_stage", sa.String(20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("books", "reading_stage")
