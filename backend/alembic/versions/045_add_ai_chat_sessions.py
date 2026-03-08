"""Add ai_chat_sessions table.

Revision ID: 045
Revises: 044
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "045"
down_revision: str | Sequence[str] | None = "044"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("session_type", sa.String(50), nullable=False, index=True),
        sa.Column("message_history", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("ai_chat_sessions")
