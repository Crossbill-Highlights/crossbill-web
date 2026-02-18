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

    # 4. Migrate data from JSON column to highlight_styles table
    conn = op.get_bind()

    rows = conn.execute(
        sa.text("""
            SELECT DISTINCT user_id, book_id,
                   highlight_style->>'color' as color,
                   highlight_style->>'style' as style
            FROM highlights
            WHERE highlight_style IS NOT NULL
        """)
    ).fetchall()

    for row in rows:
        result = conn.execute(
            sa.text("""
                INSERT INTO highlight_styles (user_id, book_id, device_color, device_style)
                VALUES (:user_id, :book_id, :color, :style)
                RETURNING id
            """),
            {"user_id": row.user_id, "book_id": row.book_id, "color": row.color, "style": row.style},
        )
        style_id = result.scalar_one()

        conn.execute(
            sa.text("""
                UPDATE highlights
                SET highlight_style_id = :style_id
                WHERE user_id = :user_id
                  AND book_id = :book_id
                  AND highlight_style->>'color' = :color
                  AND highlight_style->>'style' = :style
            """),
            {
                "style_id": style_id,
                "user_id": row.user_id,
                "book_id": row.book_id,
                "color": row.color,
                "style": row.style,
            },
        )

    # 5. Drop the old JSON column
    op.drop_column("highlights", "highlight_style")


def downgrade() -> None:
    op.add_column(
        "highlights",
        sa.Column(
            "highlight_style",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{\"color\": \"gray\", \"style\": \"lighten\"}'"),
        ),
    )

    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE highlights h
            SET highlight_style = json_build_object(
                'color', hs.device_color,
                'style', hs.device_style
            )
            FROM highlight_styles hs
            WHERE h.highlight_style_id = hs.id
        """)
    )

    op.drop_column("highlights", "highlight_style_id")
    op.drop_table("highlight_styles")
