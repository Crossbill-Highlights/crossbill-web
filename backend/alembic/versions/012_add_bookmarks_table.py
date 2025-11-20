"""Add bookmarks table for tracking reading progress.

Revision ID: 012
Revises: 011
Create Date: 2025-11-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: str | None = "011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create bookmarks table."""
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("highlight_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["highlight_id"], ["highlights.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookmarks_id"), "bookmarks", ["id"], unique=False)
    op.create_index(op.f("ix_bookmarks_book_id"), "bookmarks", ["book_id"], unique=False)
    op.create_index(op.f("ix_bookmarks_highlight_id"), "bookmarks", ["highlight_id"], unique=False)


def downgrade() -> None:
    """Drop bookmarks table."""
    op.drop_index(op.f("ix_bookmarks_highlight_id"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_book_id"), table_name="bookmarks")
    op.drop_index(op.f("ix_bookmarks_id"), table_name="bookmarks")
    op.drop_table("bookmarks")
