"""Add highlight_style JSON column to highlights table.

Revision ID: 041
Revises: 040
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "041"
down_revision: str | Sequence[str] | None = "040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_STYLE = '{"color": "gray", "style": "lighten"}'


def upgrade() -> None:
    # Add column as nullable first
    op.add_column("highlights", sa.Column("highlight_style", sa.JSON(), nullable=True))

    # Backfill existing rows with default values
    highlights = sa.table("highlights", sa.column("highlight_style", sa.JSON))
    op.execute(
        highlights.update()
        .where(highlights.c.highlight_style.is_(None))
        .values(highlight_style={"color": "gray", "style": "lighten"})
    )

    # Make non-nullable with server default
    op.alter_column(
        "highlights",
        "highlight_style",
        nullable=False,
        server_default=sa.text("'" + DEFAULT_STYLE + "'"),
    )


def downgrade() -> None:
    op.drop_column("highlights", "highlight_style")
