"""Add UUID columns to books and referencing tables.

Revision ID: 050
Revises: 049
Create Date: 2026-04-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "050"
down_revision: str | None = "049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables that reference books.id via book_id and should get a book_uuid column.
# (table_name, nullable) — highlight_styles has nullable book_id so book_uuid stays nullable.
REFERENCING_TABLES = [
    ("chapters", False),
    ("highlights", False),
    ("highlight_styles", True),
    ("highlight_tags", False),
    ("highlight_tag_groups", False),
    ("bookmarks", False),
    ("flashcards", False),
    ("reading_sessions", False),
    ("book_tags", False),
]


def upgrade() -> None:
    # 1. Add uuid column to books (non-nullable, auto-generated).
    op.add_column(
        "books",
        sa.Column(
            "uuid",
            UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
    )
    op.create_index("ix_books_uuid", "books", ["uuid"], unique=True)

    # 2. Add nullable book_uuid columns to all referencing tables.
    for table, _ in REFERENCING_TABLES:
        op.add_column(
            table,
            sa.Column("book_uuid", UUID(as_uuid=True), nullable=True),
        )

    # 3. Backfill book_uuid from books.uuid via JOIN on book_id = books.id.
    for table, _ in REFERENCING_TABLES:
        op.execute(
            sa.text(
                f"UPDATE {table} t "  # noqa: S608
                "SET book_uuid = b.uuid "
                "FROM books b "
                "WHERE t.book_id = b.id"
            )
        )

    # 4. Set NOT NULL on book_uuid for tables with non-nullable book_id.
    for table, nullable in REFERENCING_TABLES:
        if not nullable:
            op.alter_column(table, "book_uuid", nullable=False)

    # 5. Add indexes on book_uuid columns.
    for table, _ in REFERENCING_TABLES:
        op.create_index(f"ix_{table}_book_uuid", table, ["book_uuid"], unique=False)


def downgrade() -> None:
    # Drop indexes and columns in reverse order.
    for table, _ in reversed(REFERENCING_TABLES):
        op.drop_index(f"ix_{table}_book_uuid", table_name=table)
        op.drop_column(table, "book_uuid")

    op.drop_index("ix_books_uuid", table_name="books")
    op.drop_column("books", "uuid")
