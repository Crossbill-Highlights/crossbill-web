"""scope highlight deduplication by book

Revision ID: 036
Revises: 035
Create Date: 2026-01-29

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Update unique constraint to scope deduplication by book.

    Old constraint: (user_id, content_hash)
    New constraint: (user_id, book_id, content_hash)

    This allows the same highlight text in different books.
    """
    # Drop old constraint
    op.drop_constraint("uq_highlight_content_hash", "highlights", type_="unique")

    # Create new constraint with book_id
    op.create_unique_constraint(
        "uq_highlight_content_hash",
        "highlights",
        ["user_id", "book_id", "content_hash"],
    )


def downgrade() -> None:
    """
    Revert to user-level deduplication.

    WARNING: This may fail if there are duplicate content_hash values
    for the same user across different books.
    """
    # Drop new constraint
    op.drop_constraint("uq_highlight_content_hash", "highlights", type_="unique")

    # Recreate old constraint
    op.create_unique_constraint(
        "uq_highlight_content_hash",
        "highlights",
        ["user_id", "content_hash"],
    )
