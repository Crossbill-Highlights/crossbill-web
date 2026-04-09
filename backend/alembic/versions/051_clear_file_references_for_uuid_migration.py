"""Clear file references for UUID migration.

Clears ebook_file, file_type, and cover_file columns so that
users re-upload files with new UUID-based filenames.

Revision ID: 051
Revises: 050
Create Date: 2026-04-09

"""

from collections.abc import Sequence

from alembic import op

revision: str = "051"
down_revision: str | None = "050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE books SET ebook_file = NULL, file_type = NULL, cover_file = NULL")


def downgrade() -> None:
    # Cannot restore old filenames; no-op
    pass
