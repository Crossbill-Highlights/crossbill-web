"""Add batch processing tables.

Revision ID: 046
Revises: 045
Create Date: 2026-03-12
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "046"
down_revision: str | Sequence[str] | None = "045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_batch_jobs_active_lookup",
        "batch_jobs",
        ["user_id", "book_id", "job_type", "status"],
    )

    op.create_table(
        "batch_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "batch_job_id",
            sa.Integer(),
            sa.ForeignKey("batch_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_batch_items_job_id",
        "batch_items",
        ["batch_job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_batch_items_job_id", table_name="batch_items")
    op.drop_table("batch_items")
    op.drop_index("ix_batch_jobs_active_lookup", table_name="batch_jobs")
    op.drop_table("batch_jobs")
