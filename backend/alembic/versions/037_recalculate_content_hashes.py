"""Recalculate content hashes for highlights and reading_sessions.

This migration recalculates content_hash values to match the current hash
calculation logic in the domain entities:

- Highlights: SHA256(text) - simplified from previous logic
- Reading Sessions: SHA256(book_id|user_id|start_time|device_id or '')

This ensures consistency between existing records and new records created
using the current entity logic.

Revision ID: 037
Revises: 249c9ffd1b90
Create Date: 2026-02-02

"""

import hashlib
from collections.abc import Sequence

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "037"
down_revision: str | Sequence[str] | None = "249c9ffd1b90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def compute_content_hash(content: str) -> str:
    """
    Compute SHA-256 hash matching ContentHash.compute() logic.

    Must match: src/domain/common/value_objects/content_hash.py
    """
    if not content:
        raise ValueError("Cannot compute hash of empty content")

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def upgrade() -> None:
    """Recalculate content hashes for highlights and reading_sessions."""
    connection = op.get_bind()

    # 1. First, identify and remove duplicate highlights
    # The new hash formula (SHA256(text)) will create duplicates where same user/book/text exist
    print("Identifying duplicate highlights...")
    duplicates = connection.execute(
        text("""
            SELECT user_id, book_id, text, MIN(id) as keep_id, ARRAY_AGG(id) as all_ids
            FROM highlights
            GROUP BY user_id, book_id, text
            HAVING COUNT(*) > 1
        """)
    ).fetchall()

    if duplicates:
        print(f"Found {len(duplicates)} sets of duplicate highlights")
        for dup in duplicates:
            keep_id = dup[3]  # MIN(id) - keep the oldest
            all_ids = dup[4]  # ARRAY_AGG(id) - all IDs
            delete_ids = [id for id in all_ids if id != keep_id]

            if delete_ids:
                print(f"  Keeping highlight {keep_id}, deleting {len(delete_ids)} duplicates")
                connection.execute(
                    text("DELETE FROM highlights WHERE id = ANY(:ids)"),
                    {"ids": delete_ids},
                )

    # 2. Update highlights table
    print("Updating highlight content hashes...")
    highlights = connection.execute(text("SELECT id, text FROM highlights")).fetchall()

    for row in highlights:
        highlight_id = row[0]
        text_content = row[1]
        new_hash = compute_content_hash(text_content)

        connection.execute(
            text("UPDATE highlights SET content_hash = :hash WHERE id = :id"),
            {"hash": new_hash, "id": highlight_id},
        )

    print(f"Updated {len(highlights)} highlights")

    # 3. Check for potential duplicate reading sessions
    print("Checking for duplicate reading sessions...")
    session_dups = connection.execute(
        text("""
            SELECT book_id, user_id, start_time, device_id, COUNT(*) as count, ARRAY_AGG(id) as ids
            FROM reading_sessions
            GROUP BY book_id, user_id, start_time, device_id
            HAVING COUNT(*) > 1
        """)
    ).fetchall()

    if session_dups:
        print(f"Found {len(session_dups)} sets of duplicate reading sessions")
        for dup in session_dups:
            all_ids = dup[5]
            keep_id = min(all_ids)  # Keep the oldest
            delete_ids = [id for id in all_ids if id != keep_id]

            if delete_ids:
                print(f"  Keeping session {keep_id}, deleting {len(delete_ids)} duplicates")
                connection.execute(
                    text("DELETE FROM reading_sessions WHERE id = ANY(:ids)"),
                    {"ids": delete_ids},
                )

    # 4. Update reading_sessions table
    print("Updating reading session content hashes...")
    sessions = connection.execute(
        text("SELECT id, book_id, user_id, start_time, device_id FROM reading_sessions")
    ).fetchall()

    for row in sessions:
        session_id = row[0]
        book_id = row[1]
        user_id = row[2]
        start_time = row[3]
        device_id = row[4]

        # Build hash input matching entity logic
        # Note: str(start_time) produces the format matching f-string behavior
        hash_input = f"{book_id}|{user_id}|{start_time}|{device_id or ''}"
        new_hash = compute_content_hash(hash_input)

        connection.execute(
            text("UPDATE reading_sessions SET content_hash = :hash WHERE id = :id"),
            {"hash": new_hash, "id": session_id},
        )

    print(f"Updated {len(sessions)} reading sessions")


def downgrade() -> None:
    """
    Downgrade not applicable for hash recalculation.

    Cannot meaningfully revert to old hash values since we don't know what they were.
    The new hashes are correct according to current entity logic.
    """
