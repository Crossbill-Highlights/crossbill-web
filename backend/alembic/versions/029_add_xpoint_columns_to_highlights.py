"""Add start_xpoint and end_xpoint columns to highlights table.

These columns store the XML position of highlights in EPUB documents,
allowing precise location of highlighted text.

Revision ID: 029
Revises: 028
Create Date: 2026-01-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "029"
down_revision: str | None = "028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add start_xpoint and end_xpoint columns to highlights."""
    op.add_column(
        "highlights",
        sa.Column("start_xpoint", sa.Text(), nullable=True),
    )
    op.add_column(
        "highlights",
        sa.Column("end_xpoint", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove start_xpoint and end_xpoint columns from highlights."""
    op.drop_column("highlights", "end_xpoint")
    op.drop_column("highlights", "start_xpoint")
