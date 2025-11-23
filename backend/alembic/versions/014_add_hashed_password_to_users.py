"""Add hashed_password column to users table.

Revision ID: 014
Revises: 013
Create Date: 2025-11-23 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add hashed_password column to users table."""
    op.add_column("users", sa.Column("hashed_password", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove hashed_password column from users table."""
    op.drop_column("users", "hashed_password")
