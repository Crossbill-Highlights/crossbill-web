"""Drop the note column from highlights.

Per-highlight notes are superseded by the Note entity, which can link to
highlights. Existing values are discarded intentionally.

Revision ID: 057
Revises: 056
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "057"
down_revision: str | Sequence[str] | None = "056"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("highlights", "note")


def downgrade() -> None:
    op.add_column("highlights", sa.Column("note", sa.Text(), nullable=True))
