"""update_book_cover_urls_to_new_endpoint

Revision ID: 023
Revises: 022
Create Date: 2025-12-27 11:01:56.841054

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "023"
down_revision: str | Sequence[str] | None = "022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Update book cover URLs from static mount format to authenticated endpoint format."""
    # Update all cover URLs from /media/covers/{book_id}.jpg to /api/v1/books/{book_id}/cover
    op.execute(
        """
        UPDATE books
        SET cover = REGEXP_REPLACE(cover, '^/media/covers/(\\d+)\\.jpg$', '/api/v1/books/\\1/cover')
        WHERE cover LIKE '/media/covers/%';
        """
    )


def downgrade() -> None:
    """Revert book cover URLs back to static mount format."""
    # Revert cover URLs from /api/v1/books/{book_id}/cover to /media/covers/{book_id}.jpg
    op.execute(
        """
        UPDATE books
        SET cover = REGEXP_REPLACE(cover, '^/api/v1/books/(\\d+)/cover$', '/media/covers/\\1.jpg')
        WHERE cover LIKE '/api/v1/books/%/cover';
        """
    )
