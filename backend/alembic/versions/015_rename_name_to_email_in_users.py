"""Rename name column to email in users table

Revision ID: 015
Revises: 014
Create Date: 2025-01-15

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: str | None = "014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename name column to email in users table."""
    op.alter_column("users", "name", new_column_name="email")


def downgrade() -> None:
    """Rename email column back to name in users table."""
    op.alter_column("users", "email", new_column_name="name")
