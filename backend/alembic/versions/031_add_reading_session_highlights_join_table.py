"""Add reading_session_highlights join table and indexes for efficient matching.

Revision ID: 031
Revises: 030
Create Date: 2026-01-19

This migration creates:
1. reading_session_highlights - Many-to-many join table between reading_sessions and highlights
2. Composite index on highlights(user_id, book_id, page) for efficient page-based matching
3. Composite index on highlights(user_id, book_id) for xpoint-based matching queries
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "031"
down_revision: str | None = "030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create join table and indexes."""
    # Create the many-to-many join table
    op.create_table(
        "reading_session_highlights",
        sa.Column("reading_session_id", sa.Integer(), nullable=False),
        sa.Column("highlight_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["reading_session_id"],
            ["reading_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["highlight_id"],
            ["highlights.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("reading_session_id", "highlight_id"),
    )

    # Index on highlight_id for reverse lookups (highlight -> sessions)
    op.create_index(
        "ix_reading_session_highlights_highlight_id",
        "reading_session_highlights",
        ["highlight_id"],
        unique=False,
    )

    # Composite index on highlights for efficient page-based range queries
    # Used for: WHERE user_id = ? AND book_id = ? AND page BETWEEN ? AND ?
    op.create_index(
        "ix_highlights_user_book_page",
        "highlights",
        ["user_id", "book_id", "page"],
        unique=False,
    )

    # Composite index on highlights for xpoint-based queries
    # Used for: WHERE user_id = ? AND book_id = ? AND start_xpoint IS NOT NULL
    op.create_index(
        "ix_highlights_user_book",
        "highlights",
        ["user_id", "book_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop join table and indexes."""
    op.drop_index("ix_highlights_user_book", table_name="highlights")
    op.drop_index("ix_highlights_user_book_page", table_name="highlights")
    op.drop_index(
        "ix_reading_session_highlights_highlight_id",
        table_name="reading_session_highlights",
    )
    op.drop_table("reading_session_highlights")
