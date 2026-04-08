"""Switch books PK from int to UUID.

Revision ID: 051
Revises: 050
Create Date: 2026-04-08

Drops old int-based columns and constraints, renames UUID columns to be the
primary key, and recreates all foreign key constraints with UUID references.

This migration is NOT safely reversible (int IDs are gone).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "051"
down_revision: str | None = "050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables that have a book_uuid column (from migration 050) to be renamed to book_id.
# (table_name, nullable, old_int_fk_constraint_name)
# FK constraint names:
#   - chapters, highlights: named via op.f() in migration 001 -> fk_chapters_book_id_books etc.
#   - All others: PostgreSQL auto-generated names -> {table}_book_id_fkey
REFERENCING_TABLES = [
    ("chapters", False, "fk_chapters_book_id_books"),
    ("highlights", False, "fk_highlights_book_id_books"),
    ("highlight_styles", True, "highlight_styles_book_id_fkey"),
    ("highlight_tags", False, "highlight_tags_book_id_fkey"),
    ("highlight_tag_groups", False, "highlight_tag_groups_book_id_fkey"),
    ("bookmarks", False, "bookmarks_book_id_fkey"),
    ("flashcards", False, "flashcards_book_id_fkey"),
    ("reading_sessions", False, "reading_sessions_book_id_fkey"),
    ("book_tags", False, "book_tags_book_id_fkey"),
]


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. Drop int-based FK constraints on all referencing tables.
    # ------------------------------------------------------------------ #
    for table, _nullable, fk_name in REFERENCING_TABLES:
        op.drop_constraint(fk_name, table, type_="foreignkey")

    # ------------------------------------------------------------------ #
    # 2. Drop book_tags composite PK (contains int book_id).
    # ------------------------------------------------------------------ #
    op.drop_constraint("book_tags_pkey", "book_tags", type_="primary")

    # ------------------------------------------------------------------ #
    # 3. Drop books int PK.
    # ------------------------------------------------------------------ #
    op.drop_constraint("books_pkey", "books", type_="primary")

    # ------------------------------------------------------------------ #
    # 4. Drop old int book_id columns on all referencing tables.
    # ------------------------------------------------------------------ #
    for table, _nullable, _fk_name in REFERENCING_TABLES:
        # Also drop the old ix_{table}_book_id index (int-based) if it exists.
        # Some tables had this index, some did not. Use IF EXISTS via raw SQL.
        op.execute(
            sa.text(f"DROP INDEX IF EXISTS ix_{table}_book_id")
        )
        op.drop_column(table, "book_id")

    # ------------------------------------------------------------------ #
    # 5. Drop old int id column on books, plus its index.
    # ------------------------------------------------------------------ #
    op.execute(sa.text("DROP INDEX IF EXISTS ix_books_id"))
    op.drop_column("books", "id")

    # ------------------------------------------------------------------ #
    # 6. Rename books.uuid -> books.id.
    # ------------------------------------------------------------------ #
    op.alter_column("books", "uuid", new_column_name="id")
    op.execute(sa.text("DROP INDEX IF EXISTS ix_books_uuid"))

    # ------------------------------------------------------------------ #
    # 7. Rename *.book_uuid -> *.book_id on all referencing tables.
    # ------------------------------------------------------------------ #
    for table, _nullable, _fk_name in REFERENCING_TABLES:
        op.alter_column(table, "book_uuid", new_column_name="book_id")
        op.execute(
            sa.text(f"DROP INDEX IF EXISTS ix_{table}_book_uuid")
        )

    # ------------------------------------------------------------------ #
    # 8. Create PK on books.id (UUID).
    # ------------------------------------------------------------------ #
    op.create_primary_key("books_pkey", "books", ["id"])

    # ------------------------------------------------------------------ #
    # 9. Create index on books.id.
    # ------------------------------------------------------------------ #
    op.create_index("ix_books_id", "books", ["id"], unique=False)

    # ------------------------------------------------------------------ #
    # 10. Recreate FKs from *.book_id (UUID) -> books.id (UUID) with CASCADE.
    # ------------------------------------------------------------------ #
    for table, _nullable, _fk_name in REFERENCING_TABLES:
        op.create_foreign_key(
            f"fk_{table}_book_id_books",
            table,
            "books",
            ["book_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # ------------------------------------------------------------------ #
    # 11. Recreate book_tags composite PK with UUID book_id + tag_id.
    # ------------------------------------------------------------------ #
    op.create_primary_key("book_tags_pkey", "book_tags", ["book_id", "tag_id"])

    # ------------------------------------------------------------------ #
    # 12. Remove server_default on books.id (app will provide UUIDs).
    # ------------------------------------------------------------------ #
    op.alter_column(
        "books",
        "id",
        server_default=None,
        existing_type=UUID(as_uuid=True),
        existing_nullable=False,
    )

    # ------------------------------------------------------------------ #
    # 13. Create ix_{table}_book_id indexes for all referencing tables.
    # ------------------------------------------------------------------ #
    for table, _nullable, _fk_name in REFERENCING_TABLES:
        op.create_index(f"ix_{table}_book_id", table, ["book_id"], unique=False)


def downgrade() -> None:
    raise RuntimeError(
        "Migration 051 is not reversible: the original int IDs have been dropped "
        "and cannot be recovered."
    )
