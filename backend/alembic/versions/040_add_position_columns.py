"""Add position columns to highlights, reading_sessions, and chapters.

Revision ID: 040
Revises: 249c9ffd1b90
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "040"
down_revision: str | Sequence[str] | None = "038"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("highlights", sa.Column("position", sa.JSON(), nullable=True))
    op.add_column("reading_sessions", sa.Column("start_position", sa.JSON(), nullable=True))
    op.add_column("reading_sessions", sa.Column("end_position", sa.JSON(), nullable=True))
    op.add_column("chapters", sa.Column("start_position", sa.JSON(), nullable=True))
    op.add_column("chapters", sa.Column("end_position", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("chapters", "end_position")
    op.drop_column("chapters", "start_position")
    op.drop_column("reading_sessions", "end_position")
    op.drop_column("reading_sessions", "start_position")
    op.drop_column("highlights", "position")
