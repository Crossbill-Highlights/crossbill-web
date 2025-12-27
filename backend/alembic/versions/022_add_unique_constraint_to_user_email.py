"""add_unique_constraint_to_user_email

Revision ID: 022
Revises: 021
Create Date: 2025-12-27 10:33:29.894030

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "022"
down_revision: str | Sequence[str] | None = "021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index(op.f("ix_users_name"), table_name="users")
    op.create_unique_constraint("uq_user_email", "users", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_user_email", "users", type_="unique")
    op.create_index(op.f("ix_users_name"), "users", ["email"], unique=False)
