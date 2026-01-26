"""rename epub_path to file_path and add file_type

Revision ID: 035
Revises: 034
Create Date: 2026-01-25

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add file_type column
    op.add_column("books", sa.Column("file_type", sa.String(10), nullable=True))

    # Set file_type to 'epub' for all existing books that have an epub_path
    op.execute("UPDATE books SET file_type = 'epub' WHERE epub_path IS NOT NULL")

    # Rename epub_path to file_path
    op.alter_column("books", "epub_path", new_column_name="file_path")


def downgrade() -> None:
    # Rename file_path back to epub_path
    op.alter_column("books", "file_path", new_column_name="epub_path")

    # Drop file_type column
    op.drop_column("books", "file_type")
