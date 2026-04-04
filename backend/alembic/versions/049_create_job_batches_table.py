"""Create job_batches table.

Revision ID: 049
Revises: 048
Create Date: 2026-04-04

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "049"
down_revision: str | None = "048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("batch_type", sa.String(50), nullable=False),
        sa.Column("reference_id", sa.String(255), nullable=False),
        sa.Column("total_jobs", sa.Integer(), nullable=False),
        sa.Column("completed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("job_keys", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_batches_id"), "job_batches", ["id"], unique=False)
    op.create_index(op.f("ix_job_batches_user_id"), "job_batches", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_job_batches_reference_id"), "job_batches", ["reference_id"], unique=False
    )
    op.create_index(op.f("ix_job_batches_status"), "job_batches", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_batches_status"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_reference_id"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_user_id"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_id"), table_name="job_batches")
    op.drop_table("job_batches")
