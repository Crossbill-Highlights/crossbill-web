"""Reset Epub paths to NULL for all books

Revision ID: 034
Revises: 033
Create Date: 2026-01-24 18:37:00.388656

Resets all books epub_paths to NULL to force Koreader to reupload epub files so that the
chapter structure will be parsed from the ebooks.

Note that this will break the UI of the reading sessions
until new upload is done!
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "034"
down_revision: str | Sequence[str] | None = "033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("UPDATE books SET epub_path = NULL"))


def downgrade() -> None:
    """Downgrade schema."""
