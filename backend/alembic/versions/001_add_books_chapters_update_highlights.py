"""Add books and chapters tables, update highlights with foreign keys

Revision ID: 001
Revises:
Create Date: 2025-11-09 09:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create books table
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("author", sa.String(length=500), nullable=True),
        sa.Column("isbn", sa.String(length=20), nullable=True),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_books_id"), "books", ["id"], unique=False)
    op.create_index(op.f("ix_books_file_path"), "books", ["file_path"], unique=True)

    # Create chapters table
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            name=op.f("fk_chapters_book_id_books"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "name", name="uq_chapter_per_book"),
    )
    op.create_index(op.f("ix_chapters_id"), "chapters", ["id"], unique=False)
    op.create_index(op.f("ix_chapters_book_id"), "chapters", ["book_id"], unique=False)

    # Create highlights table
    op.create_table(
        "highlights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("datetime", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["book_id"],
            ["books.id"],
            name=op.f("fk_highlights_book_id_books"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chapter_id"],
            ["chapters.id"],
            name=op.f("fk_highlights_chapter_id_chapters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "text", "datetime", name="uq_highlight_dedup"),
    )
    op.create_index(op.f("ix_highlights_id"), "highlights", ["id"], unique=False)
    op.create_index(op.f("ix_highlights_book_id"), "highlights", ["book_id"], unique=False)
    op.create_index(op.f("ix_highlights_chapter_id"), "highlights", ["chapter_id"], unique=False)


def downgrade() -> None:
    # Drop highlights table
    op.drop_index(op.f("ix_highlights_chapter_id"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_book_id"), table_name="highlights")
    op.drop_index(op.f("ix_highlights_id"), table_name="highlights")
    op.drop_table("highlights")

    # Drop chapters table
    op.drop_index(op.f("ix_chapters_book_id"), table_name="chapters")
    op.drop_index(op.f("ix_chapters_id"), table_name="chapters")
    op.drop_table("chapters")

    # Drop books table
    op.drop_index(op.f("ix_books_file_path"), table_name="books")
    op.drop_index(op.f("ix_books_id"), table_name="books")
    op.drop_table("books")
