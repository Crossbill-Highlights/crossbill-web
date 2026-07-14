"""Rename highlight_tags to tags (tag system consolidation).

The HighlightTag system is now the single tag system, renamed to Tag:
- highlight_tags            -> tags
- highlight_tag_groups      -> tag_groups
- highlight_highlight_tags  -> highlight_tags (join table highlight <-> tag)
- note_highlight_tags       -> note_tags (join table note <-> tag)

Named indexes/constraints are renamed to match. Auto-generated pkey/fkey/
not-null constraint names keep their historical names (cosmetic only).

Revision ID: 055
Revises: 054
Create Date: 2026-07-14 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "055"
down_revision: str | None = "054"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename highlight tag tables, columns, indexes and constraints."""
    # Tables — the entity table must vacate the highlight_tags name before
    # the highlight<->tag join table takes it.
    op.rename_table("highlight_tags", "tags")
    op.rename_table("highlight_tag_groups", "tag_groups")
    op.rename_table("highlight_highlight_tags", "highlight_tags")
    op.rename_table("note_highlight_tags", "note_tags")

    # Columns
    op.alter_column("highlight_tags", "highlight_tag_id", new_column_name="tag_id")
    op.alter_column("note_tags", "highlight_tag_id", new_column_name="tag_id")

    # Indexes — tags (former highlight_tags entity table)
    op.execute("ALTER INDEX ix_highlight_tags_id RENAME TO ix_tags_id")
    op.execute("ALTER INDEX ix_highlight_tags_book_id RENAME TO ix_tags_book_id")
    op.execute("ALTER INDEX ix_highlight_tags_name RENAME TO ix_tags_name")
    op.execute("ALTER INDEX ix_highlight_tags_tag_group_id RENAME TO ix_tags_tag_group_id")
    op.execute("ALTER INDEX ix_highlight_tags_user_id RENAME TO ix_tags_user_id")

    # Indexes — tag_groups
    op.execute("ALTER INDEX ix_highlight_tag_groups_id RENAME TO ix_tag_groups_id")
    op.execute("ALTER INDEX ix_highlight_tag_groups_book_id RENAME TO ix_tag_groups_book_id")
    op.execute("ALTER INDEX ix_highlight_tag_groups_name RENAME TO ix_tag_groups_name")

    # Indexes — highlight_tags (former highlight_highlight_tags join table)
    op.execute(
        "ALTER INDEX ix_highlight_highlight_tags_highlight_id "
        "RENAME TO ix_highlight_tags_highlight_id"
    )
    op.execute(
        "ALTER INDEX ix_highlight_highlight_tags_highlight_tag_id "
        "RENAME TO ix_highlight_tags_tag_id"
    )

    # Indexes — note_tags (former note_highlight_tags join table)
    op.execute("ALTER INDEX ix_note_highlight_tags_note_id RENAME TO ix_note_tags_note_id")
    op.execute("ALTER INDEX ix_note_highlight_tags_highlight_tag_id RENAME TO ix_note_tags_tag_id")

    # Named constraints (renaming a unique constraint renames its backing index)
    op.execute(
        "ALTER TABLE tags RENAME CONSTRAINT uq_highlight_tag_user_book_name "
        "TO uq_tag_user_book_name"
    )
    op.execute(
        "ALTER TABLE tag_groups RENAME CONSTRAINT uq_highlight_tag_group_book_name "
        "TO uq_tag_group_book_name"
    )
    op.execute("ALTER TABLE tags RENAME CONSTRAINT fk_highlight_tags_user_id TO fk_tags_user_id")
    op.execute(
        "ALTER TABLE tags RENAME CONSTRAINT fk_highlight_tags_tag_group_id TO fk_tags_tag_group_id"
    )


def downgrade() -> None:
    """Restore the highlight_tag names."""
    op.execute(
        "ALTER TABLE tags RENAME CONSTRAINT fk_tags_tag_group_id TO fk_highlight_tags_tag_group_id"
    )
    op.execute("ALTER TABLE tags RENAME CONSTRAINT fk_tags_user_id TO fk_highlight_tags_user_id")
    op.execute(
        "ALTER TABLE tag_groups RENAME CONSTRAINT uq_tag_group_book_name "
        "TO uq_highlight_tag_group_book_name"
    )
    op.execute(
        "ALTER TABLE tags RENAME CONSTRAINT uq_tag_user_book_name "
        "TO uq_highlight_tag_user_book_name"
    )

    op.execute("ALTER INDEX ix_note_tags_tag_id RENAME TO ix_note_highlight_tags_highlight_tag_id")
    op.execute("ALTER INDEX ix_note_tags_note_id RENAME TO ix_note_highlight_tags_note_id")

    op.execute(
        "ALTER INDEX ix_highlight_tags_tag_id "
        "RENAME TO ix_highlight_highlight_tags_highlight_tag_id"
    )
    op.execute(
        "ALTER INDEX ix_highlight_tags_highlight_id "
        "RENAME TO ix_highlight_highlight_tags_highlight_id"
    )

    op.execute("ALTER INDEX ix_tag_groups_name RENAME TO ix_highlight_tag_groups_name")
    op.execute("ALTER INDEX ix_tag_groups_book_id RENAME TO ix_highlight_tag_groups_book_id")
    op.execute("ALTER INDEX ix_tag_groups_id RENAME TO ix_highlight_tag_groups_id")

    op.execute("ALTER INDEX ix_tags_user_id RENAME TO ix_highlight_tags_user_id")
    op.execute("ALTER INDEX ix_tags_tag_group_id RENAME TO ix_highlight_tags_tag_group_id")
    op.execute("ALTER INDEX ix_tags_name RENAME TO ix_highlight_tags_name")
    op.execute("ALTER INDEX ix_tags_book_id RENAME TO ix_highlight_tags_book_id")
    op.execute("ALTER INDEX ix_tags_id RENAME TO ix_highlight_tags_id")

    op.alter_column("note_tags", "tag_id", new_column_name="highlight_tag_id")
    op.alter_column("highlight_tags", "tag_id", new_column_name="highlight_tag_id")

    op.rename_table("note_tags", "note_highlight_tags")
    op.rename_table("highlight_tags", "highlight_highlight_tags")
    op.rename_table("tag_groups", "highlight_tag_groups")
    op.rename_table("tags", "highlight_tags")
