"""Replace highlight_style JSON column with highlight_styles table.

Revision ID: 041
Revises: 040
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "041"
down_revision: str | Sequence[str] | None = "040"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create highlight_styles table
    op.create_table(
        "highlight_styles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("device_color", sa.String(50), nullable=True),
        sa.Column("device_style", sa.String(50), nullable=True),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("ui_color", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. Create partial unique indexes for PostgreSQL
    op.create_index(
        "uq_hs_all",
        "highlight_styles",
        ["user_id", "book_id", "device_color", "device_style"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NOT NULL AND device_color IS NOT NULL AND device_style IS NOT NULL"
        ),
    )
    op.create_index(
        "uq_hs_book_color",
        "highlight_styles",
        ["user_id", "book_id", "device_color"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NOT NULL AND device_color IS NOT NULL AND device_style IS NULL"
        ),
    )
    op.create_index(
        "uq_hs_book_style",
        "highlight_styles",
        ["user_id", "book_id", "device_style"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NOT NULL AND device_color IS NULL AND device_style IS NOT NULL"
        ),
    )
    op.create_index(
        "uq_hs_global_combo",
        "highlight_styles",
        ["user_id", "device_color", "device_style"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NULL AND device_color IS NOT NULL AND device_style IS NOT NULL"
        ),
    )
    op.create_index(
        "uq_hs_global_color",
        "highlight_styles",
        ["user_id", "device_color"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NULL AND device_color IS NOT NULL AND device_style IS NULL"
        ),
    )
    op.create_index(
        "uq_hs_global_style",
        "highlight_styles",
        ["user_id", "device_style"],
        unique=True,
        postgresql_where=sa.text(
            "book_id IS NULL AND device_color IS NULL AND device_style IS NOT NULL"
        ),
    )

    # 3. Add highlight_style_id FK column to highlights
    op.add_column(
        "highlights",
        sa.Column(
            "highlight_style_id",
            sa.Integer(),
            sa.ForeignKey("highlight_styles.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )

    # 4. Migrate existing highlights: create a default "gray/lighten" style per (user, book)
    #    and link all highlights to it. Production does NOT have the old highlight_style JSON column.
    conn = op.get_bind()

    rows = conn.execute(
        sa.text("""
            SELECT DISTINCT user_id, book_id
            FROM highlights
            WHERE deleted_at IS NULL
        """)
    ).fetchall()

    for row in rows:
        result = conn.execute(
            sa.text("""
                INSERT INTO highlight_styles (user_id, book_id, device_color, device_style)
                VALUES (:user_id, :book_id, 'gray', 'lighten')
                RETURNING id
            """),
            {"user_id": row.user_id, "book_id": row.book_id},
        )
        style_id = result.scalar_one()

        conn.execute(
            sa.text("""
                UPDATE highlights
                SET highlight_style_id = :style_id
                WHERE user_id = :user_id
                  AND book_id = :book_id
            """),
            {
                "style_id": style_id,
                "user_id": row.user_id,
                "book_id": row.book_id,
            },
        )


def downgrade() -> None:
    op.drop_column("highlights", "highlight_style_id")
    op.drop_table("highlight_styles")
