"""Create book_reflections and book_reflection_notes tables.

Revision ID: 059
Revises: 058
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "059"
down_revision: str | Sequence[str] | None = "058"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "book_reflections",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("what_is_it_about", sa.Text(), nullable=False, server_default=""),
        sa.Column("what_does_it_say", sa.Text(), nullable=False, server_default=""),
        sa.Column("do_i_agree", sa.Text(), nullable=False, server_default=""),
        sa.Column("so_what", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("book_id", name="uq_book_reflections_book_id"),
    )
    op.create_table(
        "book_reflection_notes",
        sa.Column(
            "book_reflection_id",
            sa.Integer(),
            sa.ForeignKey("book_reflections.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("book_reflection_notes")
    op.drop_table("book_reflections")
