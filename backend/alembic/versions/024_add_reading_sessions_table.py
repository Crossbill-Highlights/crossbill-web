"""Add reading_sessions table for tracking reading sessions from KOReader.

Revision ID: 024
Revises: 023
Create Date: 2026-01-05

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "024"
down_revision: str | None = "023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create reading_sessions table."""
    op.create_table(
        "reading_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("start_xpoint", sa.Text(), nullable=True),
        sa.Column("end_xpoint", sa.Text(), nullable=True),
        sa.Column("start_page", sa.Integer(), nullable=True),
        sa.Column("end_page", sa.Integer(), nullable=True),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "content_hash", name="uq_reading_session_content_hash"),
    )
    op.create_index(op.f("ix_reading_sessions_id"), "reading_sessions", ["id"], unique=False)
    op.create_index(
        op.f("ix_reading_sessions_user_id"), "reading_sessions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_reading_sessions_book_id"), "reading_sessions", ["book_id"], unique=False
    )
    op.create_index(
        op.f("ix_reading_sessions_content_hash"), "reading_sessions", ["content_hash"], unique=False
    )
    op.create_index(
        op.f("ix_reading_sessions_start_time"), "reading_sessions", ["start_time"], unique=False
    )


def downgrade() -> None:
    """Drop reading_sessions table."""
    op.drop_index(op.f("ix_reading_sessions_start_time"), table_name="reading_sessions")
    op.drop_index(op.f("ix_reading_sessions_content_hash"), table_name="reading_sessions")
    op.drop_index(op.f("ix_reading_sessions_book_id"), table_name="reading_sessions")
    op.drop_index(op.f("ix_reading_sessions_user_id"), table_name="reading_sessions")
    op.drop_index(op.f("ix_reading_sessions_id"), table_name="reading_sessions")
    op.drop_table("reading_sessions")
