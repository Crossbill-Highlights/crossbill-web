"""Remove completion tracking columns from quiz_sessions.

Revision ID: 046
Revises: 045
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "046"
down_revision: str | Sequence[str] | None = "045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("quiz_sessions", "question_count")
    op.drop_column("quiz_sessions", "completed_at")


def downgrade() -> None:
    op.add_column(
        "quiz_sessions",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "quiz_sessions",
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="5"),
    )
