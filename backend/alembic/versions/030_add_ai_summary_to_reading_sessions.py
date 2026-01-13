"""Add ai_summary column to reading_sessions table.

This column stores AI-generated summaries of reading session content,
enabling quick access to summaries without regenerating them.

Revision ID: 030
Revises: 029
Create Date: 2026-01-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "030"
down_revision: str | None = "029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ai_summary column to reading_sessions."""
    op.add_column(
        "reading_sessions",
        sa.Column("ai_summary", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove ai_summary column from reading_sessions."""
    op.drop_column("reading_sessions", "ai_summary")
