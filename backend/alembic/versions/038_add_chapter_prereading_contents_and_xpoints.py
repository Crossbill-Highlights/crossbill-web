"""add chapter prereading contents and xpoints

Revision ID: 038
Revises: 037
Create Date: 2026-02-07

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "038"
down_revision: str | Sequence[str] | None = "037"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add XPoint columns to chapters table
    op.add_column("chapters", sa.Column("start_xpoint", sa.Text(), nullable=True))
    op.add_column("chapters", sa.Column("end_xpoint", sa.Text(), nullable=True))

    # Create chapter_prereading_contents table
    op.create_table(
        "chapter_prereading_contents",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("keypoints", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ai_model", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_id"),
    )
    op.create_index(
        "ix_chapter_prereading_contents_chapter_id",
        "chapter_prereading_contents",
        ["chapter_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chapter_prereading_contents_chapter_id",
        table_name="chapter_prereading_contents",
    )
    op.drop_table("chapter_prereading_contents")
    op.drop_column("chapters", "end_xpoint")
    op.drop_column("chapters", "start_xpoint")
