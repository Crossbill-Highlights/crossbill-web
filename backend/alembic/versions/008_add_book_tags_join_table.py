"""Add book_tags join table for many-to-many relationship.

Revision ID: 008
Revises: 007
Create Date: 2025-11-13 00:01:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create book_tags join table."""
    op.create_table(
        "book_tags",
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("book_id", "tag_id"),
    )
    op.create_index(op.f("ix_book_tags_book_id"), "book_tags", ["book_id"], unique=False)
    op.create_index(op.f("ix_book_tags_tag_id"), "book_tags", ["tag_id"], unique=False)


def downgrade() -> None:
    """Drop book_tags join table."""
    op.drop_index(op.f("ix_book_tags_tag_id"), table_name="book_tags")
    op.drop_index(op.f("ix_book_tags_book_id"), table_name="book_tags")
    op.drop_table("book_tags")
