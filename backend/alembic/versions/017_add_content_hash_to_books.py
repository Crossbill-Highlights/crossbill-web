"""Add content_hash column to books for hash-based deduplication.

This migration:
1. Adds a content_hash column for hash-based book deduplication
2. Computes hashes for all existing books based on title + author
3. Removes duplicate books (keeping the oldest one and reassigning highlights)
4. Adds a unique constraint on (user_id, content_hash)

Revision ID: 017
Revises: 016
Create Date: 2025-12-13

"""

import hashlib
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "017"
down_revision: str | None = "016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def compute_book_hash(title: str, author: str | None) -> str:
    """Compute SHA-256 hash for a book (same logic as src/hash_utils.py)."""
    normalized_title = title.strip()
    normalized_author = (author or "").strip()
    hash_input = f"{normalized_title}|{normalized_author}"
    return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()


def upgrade() -> None:
    """Add content_hash column and migrate to hash-based deduplication."""
    # Step 1: Add content_hash column (nullable initially for data migration)
    op.add_column(
        "books",
        sa.Column("content_hash", sa.String(64), nullable=True),
    )

    # Step 2: Compute hashes for all existing books
    connection = op.get_bind()

    # Get all books
    result = connection.execute(
        text("""
            SELECT id, title, author
            FROM books
        """)
    )

    # Update each book with its computed hash
    for row in result:
        book_id = row[0]
        book_title = row[1]
        book_author = row[2]

        content_hash = compute_book_hash(book_title, book_author)

        connection.execute(
            text("UPDATE books SET content_hash = :hash WHERE id = :id"),
            {"hash": content_hash, "id": book_id},
        )

    # Step 3: Remove duplicate books (keep the oldest one based on id)
    # For each duplicate, reassign highlights, chapters, tags, etc. to the kept book
    duplicates_result = connection.execute(
        text("""
            SELECT user_id, content_hash, COUNT(*) as cnt
            FROM books
            GROUP BY user_id, content_hash
            HAVING COUNT(*) > 1
        """)
    ).fetchall()

    for dup_row in duplicates_result:
        user_id = dup_row[0]
        dup_content_hash = dup_row[1]

        # Get all book IDs with this user_id + content_hash, ordered by id (keep oldest)
        books_to_check = connection.execute(
            text("""
                SELECT id
                FROM books
                WHERE user_id = :user_id AND content_hash = :content_hash
                ORDER BY id
            """),
            {"user_id": user_id, "content_hash": dup_content_hash},
        ).fetchall()

        # Keep the first one (oldest), process the rest
        book_to_keep_id = books_to_check[0][0]
        books_to_delete_ids = [b[0] for b in books_to_check[1:]]

        for book_to_delete_id in books_to_delete_ids:
            # Reassign highlights to the book we're keeping
            connection.execute(
                text("""
                    UPDATE highlights
                    SET book_id = :keep_id
                    WHERE book_id = :delete_id
                """),
                {"keep_id": book_to_keep_id, "delete_id": book_to_delete_id},
            )

            # Reassign chapters to the book we're keeping
            # But first check if a chapter with same name already exists in kept book
            chapters_to_move = connection.execute(
                text("""
                    SELECT id, name
                    FROM chapters
                    WHERE book_id = :delete_id
                """),
                {"delete_id": book_to_delete_id},
            ).fetchall()

            for chapter_row in chapters_to_move:
                chapter_id = chapter_row[0]
                chapter_name = chapter_row[1]

                # Check if chapter with same name exists in kept book
                existing_chapter = connection.execute(
                    text("""
                        SELECT id
                        FROM chapters
                        WHERE book_id = :keep_id AND name = :name
                    """),
                    {"keep_id": book_to_keep_id, "name": chapter_name},
                ).fetchone()

                if existing_chapter:
                    # Reassign highlights from this chapter to existing chapter
                    connection.execute(
                        text("""
                            UPDATE highlights
                            SET chapter_id = :existing_id
                            WHERE chapter_id = :chapter_id
                        """),
                        {"existing_id": existing_chapter[0], "chapter_id": chapter_id},
                    )
                    # Delete the duplicate chapter
                    connection.execute(
                        text("DELETE FROM chapters WHERE id = :id"),
                        {"id": chapter_id},
                    )
                else:
                    # Move chapter to kept book
                    connection.execute(
                        text("""
                            UPDATE chapters
                            SET book_id = :keep_id
                            WHERE id = :chapter_id
                        """),
                        {"keep_id": book_to_keep_id, "chapter_id": chapter_id},
                    )

            # Reassign book_tags (many-to-many relationship)
            # Get tags from the book being deleted
            tags_to_move = connection.execute(
                text("""
                    SELECT tag_id
                    FROM book_tags
                    WHERE book_id = :delete_id
                """),
                {"delete_id": book_to_delete_id},
            ).fetchall()

            for tag_row in tags_to_move:
                tag_id = tag_row[0]
                # Check if tag already associated with kept book
                existing_tag = connection.execute(
                    text("""
                        SELECT 1
                        FROM book_tags
                        WHERE book_id = :keep_id AND tag_id = :tag_id
                    """),
                    {"keep_id": book_to_keep_id, "tag_id": tag_id},
                ).fetchone()

                if not existing_tag:
                    # Add tag to kept book
                    connection.execute(
                        text("""
                            INSERT INTO book_tags (book_id, tag_id)
                            VALUES (:keep_id, :tag_id)
                        """),
                        {"keep_id": book_to_keep_id, "tag_id": tag_id},
                    )

            # Delete book_tags for deleted book
            connection.execute(
                text("DELETE FROM book_tags WHERE book_id = :id"),
                {"id": book_to_delete_id},
            )

            # Reassign highlight_tags
            connection.execute(
                text("""
                    UPDATE highlight_tags
                    SET book_id = :keep_id
                    WHERE book_id = :delete_id
                """),
                {"keep_id": book_to_keep_id, "delete_id": book_to_delete_id},
            )

            # Reassign highlight_tag_groups
            connection.execute(
                text("""
                    UPDATE highlight_tag_groups
                    SET book_id = :keep_id
                    WHERE book_id = :delete_id
                """),
                {"keep_id": book_to_keep_id, "delete_id": book_to_delete_id},
            )

            # Reassign bookmarks
            connection.execute(
                text("""
                    UPDATE bookmarks
                    SET book_id = :keep_id
                    WHERE book_id = :delete_id
                """),
                {"keep_id": book_to_keep_id, "delete_id": book_to_delete_id},
            )

            # Delete the duplicate book
            connection.execute(
                text("DELETE FROM books WHERE id = :id"),
                {"id": book_to_delete_id},
            )

    # Step 4: Make content_hash non-nullable now that all rows have values
    op.alter_column("books", "content_hash", nullable=False)

    # Step 5: Add index on content_hash for efficient lookups
    op.create_index("ix_books_content_hash", "books", ["content_hash"])

    # Step 6: Add new unique constraint on (user_id, content_hash)
    op.create_unique_constraint("uq_book_content_hash", "books", ["user_id", "content_hash"])


def downgrade() -> None:
    """Revert to old deduplication method."""
    # Step 1: Drop the unique constraint
    op.drop_constraint("uq_book_content_hash", "books", type_="unique")

    # Step 2: Drop the content_hash index
    op.drop_index("ix_books_content_hash", table_name="books")

    # Step 3: Drop the content_hash column
    op.drop_column("books", "content_hash")
