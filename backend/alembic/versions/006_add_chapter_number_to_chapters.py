"""Add chapter_number column to chapters table.

Revision ID: 006
Revises: 005
Create Date: 2025-11-11 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add chapter_number column to chapters table."""
    op.add_column(
        "chapters",
        sa.Column("chapter_number", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_chapters_chapter_number"), "chapters", ["chapter_number"], unique=False
    )


def downgrade() -> None:
    """Remove chapter_number column from chapters table."""
    op.drop_index(op.f("ix_chapters_chapter_number"), table_name="chapters")
    op.drop_column("chapters", "chapter_number")
