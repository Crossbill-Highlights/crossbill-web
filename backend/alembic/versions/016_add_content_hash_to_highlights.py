"""Add content_hash column to highlights for hash-based deduplication.

This migration:
1. Adds a content_hash column for hash-based highlight deduplication
2. Computes hashes for all existing highlights based on text + book_title + book_author
3. Removes duplicate highlights (keeping the oldest non-deleted one)
4. Replaces the old unique constraint (book_id, text, datetime) with (user_id, content_hash)

Revision ID: 016
Revises: 015
Create Date: 2025-12-12

"""

import hashlib
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def compute_highlight_hash(text_content: str, book_title: str, book_author: str | None) -> str:
    """Compute SHA-256 hash for a highlight (same logic as src/utils.py)."""
    normalized_text = text_content.strip()
    normalized_title = book_title.strip()
    normalized_author = (book_author or "").strip()
    hash_input = f"{normalized_text}|{normalized_title}|{normalized_author}"
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def upgrade() -> None:
    """Add content_hash column and migrate to hash-based deduplication."""
    # Step 1: Add content_hash column (nullable initially for data migration)
    op.add_column(
        "highlights",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # Step 2: Compute hashes for all existing highlights
    # We need to join with books to get title and author
    connection = op.get_bind()

    # Get all highlights with their book info
    result = connection.execute(
        text("""
            SELECT h.id, h.text, b.title, b.author
            FROM highlights h
            JOIN books b ON h.book_id = b.id
        """)
    )

    # Update each highlight with its computed hash
    for row in result:
        highlight_id = row[0]
        highlight_text = row[1]
        book_title = row[2]
        book_author = row[3]

        content_hash = compute_highlight_hash(highlight_text, book_title, book_author)

        connection.execute(
            text("UPDATE highlights SET content_hash = :hash WHERE id = :id"),
            {"hash": content_hash, "id": highlight_id},
        )

    # Step 3: Remove duplicate highlights (keep the oldest non-deleted, or just oldest)
    # Find all duplicates and delete all but the one to keep
    # We keep: prefer non-deleted, then oldest (smallest id)
    duplicates_result = connection.execute(
        text("""
            SELECT user_id, content_hash, COUNT(*) as cnt
            FROM highlights
            GROUP BY user_id, content_hash
            HAVING COUNT(*) > 1
        """)
    ).fetchall()

    for dup_row in duplicates_result:
        user_id = dup_row[0]
        dup_content_hash = dup_row[1]

        # Get all highlight IDs with this user_id + content_hash, ordered to pick the best one
        # Prefer: non-deleted first (deleted_at IS NULL), then oldest (smallest id)
        highlights_to_check = connection.execute(
            text("""
                SELECT id, deleted_at
                FROM highlights
                WHERE user_id = :user_id AND content_hash = :content_hash
                ORDER BY (CASE WHEN deleted_at IS NULL THEN 0 ELSE 1 END), id
            """),
            {"user_id": user_id, "content_hash": dup_content_hash},
        ).fetchall()

        # Keep the first one (best candidate), delete the rest
        ids_to_delete = [h[0] for h in highlights_to_check[1:]]

        for highlight_id in ids_to_delete:
            # Delete from join table (highlight_highlight_tags)
            connection.execute(
                text("DELETE FROM highlight_highlight_tags WHERE highlight_id = :id"),
                {"id": highlight_id},
            )
            # Delete bookmarks referencing this highlight
            connection.execute(
                text("DELETE FROM bookmarks WHERE highlight_id = :id"),
                {"id": highlight_id},
            )
            # Delete the duplicate highlight
            connection.execute(
                text("DELETE FROM highlights WHERE id = :id"),
                {"id": highlight_id},
            )

    # Step 4: Make content_hash non-nullable now that all rows have values
    op.alter_column("highlights", "content_hash", nullable=False)

    # Step 5: Add index on content_hash for efficient lookups
    op.create_index("ix_highlights_content_hash", "highlights", ["content_hash"])

    # Step 6: Drop the old unique constraint
    op.drop_constraint("uq_highlight_dedup", "highlights", type_="unique")

    # Step 7: Add new unique constraint on (user_id, content_hash)
    op.create_unique_constraint(
        "uq_highlight_content_hash", "highlights", ["user_id", "content_hash"]
    )


def downgrade() -> None:
    """Revert to old deduplication method."""
    # Step 1: Drop the new unique constraint
    op.drop_constraint("uq_highlight_content_hash", "highlights", type_="unique")

    # Step 2: Drop the content_hash index
    op.drop_index("ix_highlights_content_hash", table_name="highlights")

    # Step 3: Recreate the old unique constraint
    op.create_unique_constraint("uq_highlight_dedup", "highlights", ["book_id", "text", "datetime"])

    # Step 4: Drop the content_hash column
    op.drop_column("highlights", "content_hash")
