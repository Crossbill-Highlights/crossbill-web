"""Rename file_path to ebook_file, add cover_file column.

Decouples file references from book IDs by storing filenames
directly in the database. This prepares for the int-to-UUID
book ID migration.

Revision ID: 050
Revises: 049
Create Date: 2026-04-09

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "050"
down_revision: str | None = "049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename file_path to ebook_file
    op.alter_column("books", "file_path", new_column_name="ebook_file")

    # Add cover_file column
    op.add_column("books", sa.Column("cover_file", sa.String(500), nullable=True))

    # Populate cover_file for existing books using the current naming convention
    op.execute("UPDATE books SET cover_file = CAST(id AS TEXT) || '.jpg'")


def downgrade() -> None:
    op.drop_column("books", "cover_file")
    op.alter_column("books", "ebook_file", new_column_name="file_path")
