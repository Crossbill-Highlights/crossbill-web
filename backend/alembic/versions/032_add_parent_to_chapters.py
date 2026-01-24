"""Add parent_id to chapters for hierarchical structure.

Revision ID: 032
Revises: 031
Create Date: 2026-01-24

This migration adds a self-referential foreign key to support hierarchical
chapter structures (e.g., parts, sections, subsections in EPUB TOC).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "032"
down_revision: str | None = "031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add parent_id column to chapters table."""
    op.add_column(
        "chapters",
        sa.Column(
            "parent_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # Add foreign key constraint with CASCADE delete
    # When a parent chapter is deleted, all child chapters are deleted too
    op.create_foreign_key(
        "fk_chapters_parent_id",
        "chapters",
        "chapters",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Add index for efficient parent lookups
    op.create_index(
        "ix_chapters_parent_id",
        "chapters",
        ["parent_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove parent_id column from chapters table."""
    op.drop_index("ix_chapters_parent_id", table_name="chapters")
    op.drop_constraint("fk_chapters_parent_id", "chapters", type_="foreignkey")
    op.drop_column("chapters", "parent_id")
