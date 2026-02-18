# Highlight Labels Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the `highlight_style` JSON column on highlights with a dedicated `highlight_styles` table, enabling user-configurable labels and UI colors per device style/color combination, with book-specific overrides and global defaults.

**Architecture:** New `HighlightStyle` domain entity with its own repository, mapper, and use cases. The `Highlight` entity switches from embedding a `HighlightStyle` value object to referencing one by `HighlightStyleId` FK. A `HighlightStyleResolver` domain service resolves effective labels via a priority chain. API routes use the user-facing term "highlight-labels".

**Tech Stack:** Python, SQLAlchemy, FastAPI, Alembic, Pydantic, dependency-injector

**Design doc:** `docs/plans/2026-02-18-highlight-labels-design.md`

---

### Task 1: Add HighlightStyleId to value objects

**Files:**
- Modify: `backend/src/domain/common/value_objects/ids.py`
- Modify: `backend/src/domain/common/value_objects/__init__.py`

**Step 1: Add HighlightStyleId class**

In `backend/src/domain/common/value_objects/ids.py`, add after the `HighlightId` class (after line 36):

```python
@dataclass(frozen=True)
class HighlightStyleId(EntityId):
    """Strongly-typed highlight style identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("HighlightStyleId must be non-negative")

    @classmethod
    def generate(cls) -> "HighlightStyleId":
        return cls(0)  # Database assigns real ID
```

**Step 2: Export HighlightStyleId**

In `backend/src/domain/common/value_objects/__init__.py`:
- Add `HighlightStyleId` to the import from `.ids`
- Add `"HighlightStyleId"` to `__all__`

**Step 3: Run type check**

Run: `cd backend && .venv/bin/pyright src/domain/common/value_objects/ids.py`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/src/domain/common/value_objects/ids.py backend/src/domain/common/value_objects/__init__.py
git commit -m "Add HighlightStyleId value object"
```

---

### Task 2: Create HighlightStyle domain entity

**Files:**
- Rewrite: `backend/src/domain/common/value_objects/highlight_style.py` → move to `backend/src/domain/reading/entities/highlight_style.py`
- Create: `backend/src/domain/reading/entities/highlight_style.py`
- Modify: `backend/src/domain/common/value_objects/__init__.py` (remove old HighlightStyle export)

The current `HighlightStyle` is a frozen dataclass value object in `backend/src/domain/common/value_objects/highlight_style.py`. It needs to become a full entity in the reading domain.

**Step 1: Create the new HighlightStyle entity**

Create `backend/src/domain/reading/entities/highlight_style.py`:

```python
"""
HighlightStyle entity.

Represents a device highlight style (color + drawing style combination)
with optional user-assigned label and UI color.
"""

from __future__ import annotations

import datetime as dt_module
from dataclasses import dataclass, field
from datetime import UTC

from src.domain.common.entity import Entity
from src.domain.common.value_objects import (
    BookId,
    HighlightStyleId,
    UserId,
)


@dataclass
class HighlightStyle(Entity[HighlightStyleId]):
    """
    Highlight style entity.

    Represents a device highlight style that users can label and color.
    Rows with both device_color and device_style set are combination-level
    and serve as FK targets for highlights. Rows with one NULL dimension
    are individual-level and participate in label resolution only.
    Rows with book_id=None are global defaults.
    """

    id: HighlightStyleId
    user_id: UserId
    book_id: BookId | None
    device_color: str | None
    device_style: str | None
    label: str | None = None
    ui_color: str | None = None
    created_at: dt_module.datetime = field(
        default_factory=lambda: dt_module.datetime.now(UTC)
    )
    updated_at: dt_module.datetime = field(
        default_factory=lambda: dt_module.datetime.now(UTC)
    )

    def update_label(self, label: str | None) -> None:
        """Set or clear the user-assigned label."""
        self.label = label.strip() if label else None
        self.updated_at = dt_module.datetime.now(UTC)

    def update_ui_color(self, ui_color: str | None) -> None:
        """Set or clear the user-chosen UI color."""
        self.ui_color = ui_color
        self.updated_at = dt_module.datetime.now(UTC)

    def is_combination_level(self) -> bool:
        """Check if both device fields are set (combination-level style)."""
        return self.device_color is not None and self.device_style is not None

    def is_global(self) -> bool:
        """Check if this is a global default (no book_id)."""
        return self.book_id is None

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId | None,
        device_color: str | None,
        device_style: str | None,
        label: str | None = None,
        ui_color: str | None = None,
    ) -> HighlightStyle:
        """Factory for creating a new highlight style."""
        now = dt_module.datetime.now(UTC)
        return cls(
            id=HighlightStyleId.generate(),
            user_id=user_id,
            book_id=book_id,
            device_color=device_color,
            device_style=device_style,
            label=label,
            ui_color=ui_color,
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def create_with_id(
        cls,
        id: HighlightStyleId,
        user_id: UserId,
        book_id: BookId | None,
        device_color: str | None,
        device_style: str | None,
        label: str | None,
        ui_color: str | None,
        created_at: dt_module.datetime,
        updated_at: dt_module.datetime,
    ) -> HighlightStyle:
        """Factory for reconstituting from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            device_color=device_color,
            device_style=device_style,
            label=label,
            ui_color=ui_color,
            created_at=created_at,
            updated_at=updated_at,
        )
```

**Step 2: Delete the old value object file**

Delete `backend/src/domain/common/value_objects/highlight_style.py`.

**Step 3: Update value objects __init__.py**

In `backend/src/domain/common/value_objects/__init__.py`:
- Remove the import of `HighlightStyle` from `.highlight_style`
- Remove `"HighlightStyle"` from `__all__`

**Step 4: Fix all imports of the old HighlightStyle**

Search and update all files that import `HighlightStyle` from the old location. The files are:

- `backend/src/domain/reading/entities/highlight.py` — change import source
- `backend/src/infrastructure/reading/mappers/highlight_mapper.py` — change import source
- `backend/src/application/reading/use_cases/highlights/highlight_upload_use_case.py` — change import source

All should now import from `src.domain.reading.entities.highlight_style`.

**Step 5: Run type check and tests**

Run: `cd backend && .venv/bin/pyright src/domain/reading/entities/highlight_style.py`
Run: `cd backend && .venv/bin/pytest -x`
Expected: PASS (the old HighlightStyle API is still available via the entity — `color`→`device_color` and `style`→`device_style` field names will cause failures that we fix in the next task)

Note: Tests may fail at this point because field names changed. That's OK — we fix the Highlight entity and mapper in the next tasks.

**Step 6: Commit**

```bash
git add -A
git commit -m "Promote HighlightStyle from value object to domain entity"
```

---

### Task 3: Update Highlight entity to use HighlightStyleId reference

**Files:**
- Modify: `backend/src/domain/reading/entities/highlight.py`

**Step 1: Update the Highlight entity**

In `backend/src/domain/reading/entities/highlight.py`:

1. Replace `HighlightStyle` import with `HighlightStyleId` (from `src.domain.common.value_objects`)
2. Replace the field `highlight_style: HighlightStyle = field(default_factory=HighlightStyle.default)` with `highlight_style_id: HighlightStyleId | None = None`
3. Update `create()` factory: replace `highlight_style` parameter with `highlight_style_id: HighlightStyleId | None = None`, pass it through
4. Update `create_with_id()` factory: same change

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/domain/reading/entities/highlight.py`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/src/domain/reading/entities/highlight.py
git commit -m "Update Highlight entity to reference HighlightStyleId instead of HighlightStyle value object"
```

---

### Task 4: Add HighlightStyle ORM model and update Highlight ORM model

**Files:**
- Modify: `backend/src/models.py`

**Step 1: Add HighlightStyle ORM model**

Add the new ORM model in `backend/src/models.py` before the `Highlight` class:

```python
class HighlightStyle(Base):
    """ORM model for highlight styles (labels)."""

    __tablename__ = "highlight_styles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    book_id: Mapped[int | None] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=True
    )
    device_color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_style: Mapped[str | None] = mapped_column(String(50), nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ui_color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="highlight_styles")
    book = relationship("Book", back_populates="highlight_styles")
    highlights = relationship("Highlight", back_populates="highlight_style_rel")
```

**Step 2: Update Highlight ORM model**

In the `Highlight` class in `backend/src/models.py`:

1. Remove the `highlight_style` JSON column (lines 272-274)
2. Add `highlight_style_id` FK column:
   ```python
   highlight_style_id: Mapped[int | None] = mapped_column(
       ForeignKey("highlight_styles.id", ondelete="SET NULL"), index=True, nullable=True
   )
   ```
3. Add relationship:
   ```python
   highlight_style_rel = relationship("HighlightStyle", back_populates="highlights")
   ```

**Step 3: Add back_populates to User and Book ORM models**

Add `highlight_styles` relationship to the `User` model and `Book` model:

In `User`:
```python
highlight_styles = relationship("HighlightStyle", back_populates="user", cascade="all, delete-orphan")
```

In `Book`:
```python
highlight_styles = relationship("HighlightStyle", back_populates="book", cascade="all, delete-orphan")
```

**Step 4: Run type check**

Run: `cd backend && .venv/bin/pyright src/models.py`
Expected: PASS

**Step 5: Commit**

```bash
git add backend/src/models.py
git commit -m "Add HighlightStyle ORM model, update Highlight to use FK reference"
```

---

### Task 5: Replace Alembic migration 041

**Files:**
- Rewrite: `backend/alembic/versions/041_add_highlight_style_to_highlights.py`

**Step 1: Rewrite migration 041**

Replace the contents of `backend/alembic/versions/041_add_highlight_style_to_highlights.py` with a migration that:

1. Creates the `highlight_styles` table
2. Creates the 6 partial unique indexes
3. Adds `highlight_style_id` FK column to `highlights`
4. Migrates data from `highlight_style` JSON column to `highlight_styles` table rows
5. Drops the `highlight_style` JSON column

```python
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

    # 2. Create partial unique indexes
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

    # Get all unique (user_id, book_id, color, style) combinations
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
        # Insert highlight_style row
        result = conn.execute(
            sa.text("""
                INSERT INTO highlight_styles (user_id, book_id, device_color, device_style)
                VALUES (:user_id, :book_id, :color, :style)
                RETURNING id
            """),
            {"user_id": row.user_id, "book_id": row.book_id, "color": row.color, "style": row.style},
        )
        style_id = result.scalar_one()

        # Update highlights to reference the new style row
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
    # Re-add JSON column
    op.add_column(
        "highlights",
        sa.Column(
            "highlight_style",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{\"color\": \"gray\", \"style\": \"lighten\"}'"),
        ),
    )

    # Migrate data back from highlight_styles to JSON
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

    # Drop FK column
    op.drop_column("highlights", "highlight_style_id")

    # Drop highlight_styles table (indexes dropped automatically)
    op.drop_table("highlight_styles")
```

**Step 2: Commit**

```bash
git add backend/alembic/versions/041_add_highlight_style_to_highlights.py
git commit -m "Replace migration 041: highlight_style JSON column -> highlight_styles table"
```

---

### Task 6: Create HighlightStyleMapper

**Files:**
- Create: `backend/src/infrastructure/reading/mappers/highlight_style_mapper.py`

**Step 1: Create the mapper**

```python
"""Mapper for converting between HighlightStyle ORM models and domain entities."""

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.models import HighlightStyle as HighlightStyleORM


class HighlightStyleMapper:
    """Mapper for HighlightStyle ORM <-> Domain conversion."""

    def to_domain(self, orm_model: HighlightStyleORM) -> HighlightStyle:
        """Convert ORM model to domain entity."""
        return HighlightStyle.create_with_id(
            id=HighlightStyleId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id) if orm_model.book_id else None,
            device_color=orm_model.device_color,
            device_style=orm_model.device_style,
            label=orm_model.label,
            ui_color=orm_model.ui_color,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
        )

    def to_orm(
        self,
        domain_entity: HighlightStyle,
        orm_model: HighlightStyleORM | None = None,
    ) -> HighlightStyleORM:
        """Convert domain entity to ORM model."""
        if orm_model:
            orm_model.label = domain_entity.label
            orm_model.ui_color = domain_entity.ui_color
            orm_model.updated_at = domain_entity.updated_at
            return orm_model

        return HighlightStyleORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            book_id=domain_entity.book_id.value if domain_entity.book_id else None,
            device_color=domain_entity.device_color,
            device_style=domain_entity.device_style,
            label=domain_entity.label,
            ui_color=domain_entity.ui_color,
            created_at=domain_entity.created_at,
        )
```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/mappers/highlight_style_mapper.py`

**Step 3: Commit**

```bash
git add backend/src/infrastructure/reading/mappers/highlight_style_mapper.py
git commit -m "Add HighlightStyleMapper for ORM-domain conversion"
```

---

### Task 7: Update HighlightMapper for highlight_style_id

**Files:**
- Modify: `backend/src/infrastructure/reading/mappers/highlight_mapper.py`

**Step 1: Update the mapper**

1. Remove the `HighlightStyle` import
2. Add `HighlightStyleId` to imports from value objects
3. In `to_domain()`: replace `highlight_style=HighlightStyle.from_json(orm_model.highlight_style)` with `highlight_style_id=HighlightStyleId(orm_model.highlight_style_id) if orm_model.highlight_style_id else None`
4. In `to_orm()` (update path): replace `orm_model.highlight_style = domain_entity.highlight_style.to_json()` with `orm_model.highlight_style_id = domain_entity.highlight_style_id.value if domain_entity.highlight_style_id else None`
5. In `to_orm()` (create path): replace `highlight_style=domain_entity.highlight_style.to_json()` with `highlight_style_id=domain_entity.highlight_style_id.value if domain_entity.highlight_style_id else None`

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/mappers/highlight_mapper.py`

**Step 3: Commit**

```bash
git add backend/src/infrastructure/reading/mappers/highlight_mapper.py
git commit -m "Update HighlightMapper to use highlight_style_id FK"
```

---

### Task 8: Create HighlightStyleRepository and protocol

**Files:**
- Create: `backend/src/application/reading/protocols/highlight_style_repository.py`
- Create: `backend/src/infrastructure/reading/repositories/highlight_style_repository.py`

**Step 1: Create the protocol**

Create `backend/src/application/reading/protocols/highlight_style_repository.py`:

```python
"""Protocol for HighlightStyle repository."""

from typing import Protocol

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle


class HighlightStyleRepositoryProtocol(Protocol):
    """Interface for HighlightStyle persistence."""

    def find_by_id(
        self, style_id: HighlightStyleId, user_id: UserId
    ) -> HighlightStyle | None: ...

    def find_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        device_color: str | None,
        device_style: str | None,
    ) -> HighlightStyle: ...

    def find_by_book(
        self, book_id: BookId, user_id: UserId
    ) -> list[HighlightStyle]: ...

    def find_global(self, user_id: UserId) -> list[HighlightStyle]: ...

    def find_for_resolution(
        self, user_id: UserId, book_id: BookId
    ) -> list[HighlightStyle]: ...

    def save(self, style: HighlightStyle) -> HighlightStyle: ...

    def count_highlights_by_style(
        self, style_id: HighlightStyleId
    ) -> int: ...
```

**Step 2: Create the repository implementation**

Create `backend/src/infrastructure/reading/repositories/highlight_style_repository.py`:

```python
"""Repository for HighlightStyle persistence."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.domain.common.value_objects import BookId, HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.infrastructure.reading.mappers.highlight_style_mapper import HighlightStyleMapper
from src.models import Highlight as HighlightORM
from src.models import HighlightStyle as HighlightStyleORM


class HighlightStyleRepository:
    """SQLAlchemy implementation of HighlightStyle repository."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = HighlightStyleMapper()

    def find_by_id(
        self, style_id: HighlightStyleId, user_id: UserId
    ) -> HighlightStyle | None:
        """Find a highlight style by ID."""
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.id == style_id.value,
            HighlightStyleORM.user_id == user_id.value,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm) if orm else None

    def find_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        device_color: str | None,
        device_style: str | None,
    ) -> HighlightStyle:
        """Find existing combination-level style or create one."""
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id == book_id.value,
            HighlightStyleORM.device_color == device_color,
            HighlightStyleORM.device_style == device_style,
        )
        orm = self.db.execute(stmt).scalar_one_or_none()
        if orm:
            return self.mapper.to_domain(orm)

        # Create new
        style = HighlightStyle.create(
            user_id=user_id,
            book_id=book_id,
            device_color=device_color,
            device_style=device_style,
        )
        orm = self.mapper.to_orm(style)
        self.db.add(orm)
        self.db.flush()
        return self.mapper.to_domain(orm)

    def find_by_book(
        self, book_id: BookId, user_id: UserId
    ) -> list[HighlightStyle]:
        """Find all styles for a book (combination-level only)."""
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id == book_id.value,
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def find_global(self, user_id: UserId) -> list[HighlightStyle]:
        """Find all global default styles."""
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            HighlightStyleORM.book_id.is_(None),
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def find_for_resolution(
        self, user_id: UserId, book_id: BookId
    ) -> list[HighlightStyle]:
        """Find all styles relevant for label resolution (book-specific + global)."""
        stmt = select(HighlightStyleORM).where(
            HighlightStyleORM.user_id == user_id.value,
            (HighlightStyleORM.book_id == book_id.value)
            | (HighlightStyleORM.book_id.is_(None)),
        )
        orms = self.db.execute(stmt).scalars().all()
        return [self.mapper.to_domain(orm) for orm in orms]

    def save(self, style: HighlightStyle) -> HighlightStyle:
        """Save (create or update) a highlight style."""
        if style.id.value == 0:
            orm = self.mapper.to_orm(style)
            self.db.add(orm)
            self.db.flush()
            return self.mapper.to_domain(orm)

        existing = self.db.execute(
            select(HighlightStyleORM).where(
                HighlightStyleORM.id == style.id.value
            )
        ).scalar_one_or_none()
        if existing:
            self.mapper.to_orm(style, existing)
            self.db.flush()
            return self.mapper.to_domain(existing)

        orm = self.mapper.to_orm(style)
        self.db.add(orm)
        self.db.flush()
        return self.mapper.to_domain(orm)

    def count_highlights_by_style(
        self, style_id: HighlightStyleId
    ) -> int:
        """Count highlights using a given style."""
        stmt = select(func.count()).select_from(HighlightORM).where(
            HighlightORM.highlight_style_id == style_id.value,
            HighlightORM.deleted_at.is_(None),
        )
        result = self.db.execute(stmt).scalar()
        return result or 0
```

**Step 3: Export from repositories __init__.py**

Check if `backend/src/infrastructure/reading/repositories/__init__.py` exists and add `HighlightStyleRepository` to its exports.

**Step 4: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/repositories/highlight_style_repository.py`
Run: `cd backend && .venv/bin/pyright src/application/reading/protocols/highlight_style_repository.py`

**Step 5: Commit**

```bash
git add backend/src/application/reading/protocols/highlight_style_repository.py backend/src/infrastructure/reading/repositories/highlight_style_repository.py backend/src/infrastructure/reading/repositories/__init__.py
git commit -m "Add HighlightStyleRepository with find_or_create for upload flow"
```

---

### Task 9: Create HighlightStyleResolver domain service

**Files:**
- Create: `backend/src/domain/reading/services/highlight_style_resolver.py`

**Step 1: Create the resolver**

```python
"""Domain service for resolving effective highlight labels via priority chain."""

from dataclasses import dataclass

from src.domain.reading.entities.highlight_style import HighlightStyle


@dataclass(frozen=True)
class ResolvedLabel:
    """Result of label resolution."""

    label: str | None
    ui_color: str | None
    source: str  # "book", "global", or "none"


class HighlightStyleResolver:
    """Resolves effective label and ui_color for a highlight style.

    Priority chain:
    1. Combination + book (book_id=X, color=Y, style=Z)
    2. Color-only + book (book_id=X, color=Y, style=NULL)
    3. Style-only + book (book_id=X, color=NULL, style=Z)
    4. Combination + global (book_id=NULL, color=Y, style=Z)
    5. Color-only + global (book_id=NULL, color=Y, style=NULL)
    6. Style-only + global (book_id=NULL, color=NULL, style=Z)
    7. No label
    """

    def resolve(
        self,
        style: HighlightStyle,
        all_styles: list[HighlightStyle],
    ) -> ResolvedLabel:
        """Resolve effective label for a combination-level style.

        Args:
            style: The combination-level style to resolve for
            all_styles: All styles for the user's book + global defaults
        """
        # Priority 1: The style itself (combination + book)
        if style.label is not None:
            return ResolvedLabel(
                label=style.label, ui_color=style.ui_color, source="book"
            )

        # Build lookup helpers
        book_styles = [s for s in all_styles if not s.is_global()]
        global_styles = [s for s in all_styles if s.is_global()]

        # Priority 2: Color-only + book
        resolved = self._find_individual(
            book_styles, style.device_color, None, "book"
        )
        if resolved:
            return resolved

        # Priority 3: Style-only + book
        resolved = self._find_individual(
            book_styles, None, style.device_style, "book"
        )
        if resolved:
            return resolved

        # Priority 4: Combination + global
        resolved = self._find_combination(
            global_styles, style.device_color, style.device_style, "global"
        )
        if resolved:
            return resolved

        # Priority 5: Color-only + global
        resolved = self._find_individual(
            global_styles, style.device_color, None, "global"
        )
        if resolved:
            return resolved

        # Priority 6: Style-only + global
        resolved = self._find_individual(
            global_styles, None, style.device_style, "global"
        )
        if resolved:
            return resolved

        # Priority 7: No label
        return ResolvedLabel(label=None, ui_color=style.ui_color, source="none")

    def _find_combination(
        self,
        styles: list[HighlightStyle],
        color: str | None,
        style_name: str | None,
        source: str,
    ) -> ResolvedLabel | None:
        for s in styles:
            if (
                s.device_color == color
                and s.device_style == style_name
                and s.is_combination_level()
                and s.label is not None
            ):
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
        return None

    def _find_individual(
        self,
        styles: list[HighlightStyle],
        color: str | None,
        style_name: str | None,
        source: str,
    ) -> ResolvedLabel | None:
        for s in styles:
            if color is not None and s.device_color == color and s.device_style is None and s.label is not None:
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
            if style_name is not None and s.device_style == style_name and s.device_color is None and s.label is not None:
                return ResolvedLabel(label=s.label, ui_color=s.ui_color or None, source=source)
        return None
```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/domain/reading/services/highlight_style_resolver.py`

**Step 3: Commit**

```bash
git add backend/src/domain/reading/services/highlight_style_resolver.py
git commit -m "Add HighlightStyleResolver domain service for label priority resolution"
```

---

### Task 10: Update highlight upload use case

**Files:**
- Modify: `backend/src/application/reading/use_cases/highlights/highlight_upload_use_case.py`

**Step 1: Update the use case**

1. Remove `HighlightStyle` from imports
2. Add `HighlightStyleId` to value object imports
3. Add import for `HighlightStyleRepositoryProtocol`
4. Add `highlight_style_repository: HighlightStyleRepositoryProtocol` to `__init__` parameters and store it
5. In `upload_highlights()`, replace the `HighlightStyle(...)` creation (line 171) with:
   ```python
   highlight_style = self.highlight_style_repository.find_or_create(
       user_id=user_id_vo,
       book_id=book_id,
       device_color=data.color,
       device_style=data.drawer,
   )
   ```
6. In `Highlight.create(...)` call (line 181), replace `highlight_style=highlight_style` with `highlight_style_id=highlight_style.id`
7. Remove `drawer` and `color` from the `HighlightUploadData` dataclass (they are no longer needed as direct fields — wait, they ARE still needed as inputs from the router). Keep `color` and `drawer` fields in the DTO.

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/application/reading/use_cases/highlights/highlight_upload_use_case.py`

**Step 3: Commit**

```bash
git add backend/src/application/reading/use_cases/highlights/highlight_upload_use_case.py
git commit -m "Update highlight upload use case to use HighlightStyleRepository.find_or_create"
```

---

### Task 11: Wire HighlightStyleRepository into DI container

**Files:**
- Modify: `backend/src/core.py`

**Step 1: Add imports and register**

1. Add import for `HighlightStyleRepository`:
   ```python
   from src.infrastructure.reading.repositories.highlight_style_repository import HighlightStyleRepository
   ```
2. Add repository to container (in the repositories section):
   ```python
   highlight_style_repository = providers.Factory(HighlightStyleRepository, db=db)
   ```
3. Update `highlight_upload_use_case` to include the new repository:
   ```python
   highlight_upload_use_case = providers.Factory(
       HighlightUploadUseCase,
       highlight_repository=highlight_repository,
       book_repository=book_repository,
       chapter_repository=chapter_repository,
       deduplication_service=highlight_deduplication_service,
       position_index_service=epub_position_index_service,
       file_repository=file_repository,
       highlight_style_repository=highlight_style_repository,
   )
   ```

**Step 2: Run type check**

Run: `cd backend && .venv/bin/pyright src/core.py`

**Step 3: Commit**

```bash
git add backend/src/core.py
git commit -m "Wire HighlightStyleRepository into DI container"
```

---

### Task 12: Update highlight schemas for new response format

**Files:**
- Modify: `backend/src/infrastructure/reading/schemas/highlight_schemas.py`
- Modify: `backend/src/infrastructure/reading/schemas/__init__.py`

**Step 1: Update schemas**

In `backend/src/infrastructure/reading/schemas/highlight_schemas.py`:

1. Replace `HighlightStyleResponse` with a new schema:
   ```python
   class HighlightLabelResponse(BaseModel):
       """Resolved label info for a highlight."""

       highlight_style_id: int | None = Field(None, description="ID of the highlight style")
       label: str | None = Field(None, description="Resolved label for this highlight")
       ui_color: str | None = Field(None, description="Resolved UI color for this highlight")
   ```

2. In `HighlightResponseBase`, replace:
   ```python
   highlight_style: HighlightStyleResponse = Field(...)
   ```
   with:
   ```python
   highlight_style_id: int | None = Field(None, description="ID of the highlight style")
   label: str | None = Field(None, description="Resolved label for this highlight")
   ui_color: str | None = Field(None, description="Resolved UI color for this highlight")
   ```

3. Remove the old `HighlightStyleResponse` class entirely.

**Step 2: Create highlight label schemas**

Add schemas for the `/highlight-labels` endpoints:

```python
class HighlightLabelInBook(BaseModel):
    """Schema for a highlight label as shown in book context."""

    id: int
    device_color: str | None = Field(None, description="Device highlight color")
    device_style: str | None = Field(None, description="Device drawing style")
    label: str | None = Field(None, description="User-assigned label")
    ui_color: str | None = Field(None, description="User-chosen UI color")
    label_source: str = Field(..., description="Where the label comes from: 'book', 'global', or 'none'")
    highlight_count: int = Field(..., description="Number of highlights using this style")


class HighlightLabelUpdate(BaseModel):
    """Schema for updating a highlight label."""

    label: str | None = Field(None, description="New label (null to clear)")
    ui_color: str | None = Field(None, description="New UI color (null to clear)")


class HighlightLabelCreate(BaseModel):
    """Schema for creating a global highlight label."""

    device_color: str | None = Field(None, description="Device color to label")
    device_style: str | None = Field(None, description="Device style to label")
    label: str | None = Field(None, description="Label to assign")
    ui_color: str | None = Field(None, description="UI color to assign")
```

**Step 3: Update schemas __init__.py**

In `backend/src/infrastructure/reading/schemas/__init__.py`:
- Remove `HighlightStyleResponse` export
- Add new schema exports: `HighlightLabelInBook`, `HighlightLabelUpdate`, `HighlightLabelCreate`

**Step 4: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/schemas/highlight_schemas.py`

**Step 5: Commit**

```bash
git add backend/src/infrastructure/reading/schemas/highlight_schemas.py backend/src/infrastructure/reading/schemas/__init__.py
git commit -m "Update highlight schemas: replace HighlightStyleResponse with inline label fields"
```

---

### Task 13: Update all routers to use new highlight response format

**Files:**
- Modify: `backend/src/infrastructure/reading/routers/highlights.py`
- Modify: `backend/src/infrastructure/library/routers/books.py`
- Modify: `backend/src/infrastructure/reading/routers/reading_sessions.py`
- Modify: `backend/src/infrastructure/learning/routers/book_flashcards.py`

For each file, find every place that constructs `HighlightStyleResponse(...)` and replace it with the inline fields `highlight_style_id=..., label=..., ui_color=...`.

**Step 1: Update highlights router**

In `backend/src/infrastructure/reading/routers/highlights.py`:

1. Remove `HighlightStyleResponse` from imports
2. At each location where highlights are converted to response schemas (lines ~222, ~474, ~942, ~1041), replace:
   ```python
   highlight_style=HighlightStyleResponse(**highlight.highlight_style.to_json()),
   ```
   with:
   ```python
   highlight_style_id=highlight.highlight_style_id.value if highlight.highlight_style_id else None,
   label=None,  # TODO: resolve via HighlightStyleResolver
   ui_color=None,  # TODO: resolve via HighlightStyleResolver
   ```

Note: Label resolution will be wired in Task 15 when we add the label resolution use case. For now, pass None.

**Step 2: Update books router**

In `backend/src/infrastructure/library/routers/books.py`:
- Same pattern as above for the highlight_style references

**Step 3: Update reading_sessions router**

In `backend/src/infrastructure/reading/routers/reading_sessions.py`:
- Same pattern as above

**Step 4: Update book_flashcards router**

In `backend/src/infrastructure/learning/routers/book_flashcards.py`:
- Same pattern as above

**Step 5: Run type check across all modified routers**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/routers/highlights.py src/infrastructure/library/routers/books.py src/infrastructure/reading/routers/reading_sessions.py src/infrastructure/learning/routers/book_flashcards.py`

**Step 6: Commit**

```bash
git add backend/src/infrastructure/reading/routers/highlights.py backend/src/infrastructure/library/routers/books.py backend/src/infrastructure/reading/routers/reading_sessions.py backend/src/infrastructure/learning/routers/book_flashcards.py
git commit -m "Update all routers to use inline label fields instead of HighlightStyleResponse"
```

---

### Task 14: Create highlight label use cases

**Files:**
- Create: `backend/src/application/reading/use_cases/highlight_labels/get_book_highlight_labels_use_case.py`
- Create: `backend/src/application/reading/use_cases/highlight_labels/update_highlight_label_use_case.py`
- Create: `backend/src/application/reading/use_cases/highlight_labels/get_global_highlight_labels_use_case.py`
- Create: `backend/src/application/reading/use_cases/highlight_labels/create_global_highlight_label_use_case.py`
- Create: `backend/src/application/reading/use_cases/highlight_labels/__init__.py`

**Step 1: Create GetBookHighlightLabelsUseCase**

```python
"""Use case for getting highlight labels for a book."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)


class GetBookHighlightLabelsUseCase:
    """Get all highlight labels for a book with resolved labels."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_style_resolver: HighlightStyleResolver,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository
        self.book_repository = book_repository
        self.resolver = highlight_style_resolver

    def execute(
        self, book_id: int, user_id: int
    ) -> list[tuple[HighlightStyle, ResolvedLabel, int]]:
        """Returns list of (style, resolved_label, highlight_count) for the book."""
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            from src.exceptions import NotFoundError
            raise NotFoundError(f"Book {book_id} not found")

        # Get all styles for resolution (book + global)
        all_styles = self.highlight_style_repository.find_for_resolution(
            user_id_vo, book_id_vo
        )

        # Filter to combination-level, book-specific styles
        book_combo_styles = [
            s for s in all_styles
            if s.is_combination_level() and not s.is_global()
        ]

        results: list[tuple[HighlightStyle, ResolvedLabel, int]] = []
        for style in book_combo_styles:
            resolved = self.resolver.resolve(style, all_styles)
            count = self.highlight_style_repository.count_highlights_by_style(style.id)
            results.append((style, resolved, count))

        return results
```

**Step 2: Create UpdateHighlightLabelUseCase**

```python
"""Use case for updating a highlight label."""

from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import HighlightStyleId, UserId
from src.domain.reading.entities.highlight_style import HighlightStyle
from src.exceptions import NotFoundError


class UpdateHighlightLabelUseCase:
    """Update label and/or ui_color on a highlight style."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository

    def execute(
        self,
        style_id: int,
        user_id: int,
        label: str | None = None,
        ui_color: str | None = None,
        clear_label: bool = False,
        clear_ui_color: bool = False,
    ) -> HighlightStyle:
        """Update a highlight style's label and/or ui_color."""
        style = self.highlight_style_repository.find_by_id(
            HighlightStyleId(style_id), UserId(user_id)
        )
        if not style:
            raise NotFoundError(f"Highlight style {style_id} not found")

        if label is not None or clear_label:
            style.update_label(label)
        if ui_color is not None or clear_ui_color:
            style.update_ui_color(ui_color)

        return self.highlight_style_repository.save(style)
```

**Step 3: Create GetGlobalHighlightLabelsUseCase**

```python
"""Use case for getting global highlight labels."""

from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import UserId
from src.domain.reading.entities.highlight_style import HighlightStyle


class GetGlobalHighlightLabelsUseCase:
    """Get all global default highlight labels."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository

    def execute(self, user_id: int) -> list[HighlightStyle]:
        """Returns list of global highlight styles."""
        return self.highlight_style_repository.find_global(UserId(user_id))
```

**Step 4: Create CreateGlobalHighlightLabelUseCase**

```python
"""Use case for creating a global highlight label."""

from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import UserId
from src.domain.reading.entities.highlight_style import HighlightStyle


class CreateGlobalHighlightLabelUseCase:
    """Create a global default highlight label."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository

    def execute(
        self,
        user_id: int,
        device_color: str | None,
        device_style: str | None,
        label: str | None = None,
        ui_color: str | None = None,
    ) -> HighlightStyle:
        """Create a new global highlight style."""
        style = HighlightStyle.create(
            user_id=UserId(user_id),
            book_id=None,
            device_color=device_color,
            device_style=device_style,
            label=label,
            ui_color=ui_color,
        )
        return self.highlight_style_repository.save(style)
```

**Step 5: Create __init__.py**

Create empty `backend/src/application/reading/use_cases/highlight_labels/__init__.py`.

**Step 6: Run type check**

Run: `cd backend && .venv/bin/pyright src/application/reading/use_cases/highlight_labels/`

**Step 7: Commit**

```bash
git add backend/src/application/reading/use_cases/highlight_labels/
git commit -m "Add highlight label use cases (get book labels, update, get/create global)"
```

---

### Task 15: Wire label use cases into DI container and create router

**Files:**
- Modify: `backend/src/core.py`
- Create: `backend/src/infrastructure/reading/routers/highlight_labels.py`
- Modify: `backend/src/main.py`

**Step 1: Add use cases to DI container**

In `backend/src/core.py`:

1. Add imports for the four new use cases and the resolver domain service
2. Add resolver to domain services section:
   ```python
   highlight_style_resolver = providers.Factory(HighlightStyleResolver)
   ```
3. Register all four use cases:
   ```python
   get_book_highlight_labels_use_case = providers.Factory(
       GetBookHighlightLabelsUseCase,
       highlight_style_repository=highlight_style_repository,
       book_repository=book_repository,
       highlight_style_resolver=highlight_style_resolver,
   )
   update_highlight_label_use_case = providers.Factory(
       UpdateHighlightLabelUseCase,
       highlight_style_repository=highlight_style_repository,
   )
   get_global_highlight_labels_use_case = providers.Factory(
       GetGlobalHighlightLabelsUseCase,
       highlight_style_repository=highlight_style_repository,
   )
   create_global_highlight_label_use_case = providers.Factory(
       CreateGlobalHighlightLabelUseCase,
       highlight_style_repository=highlight_style_repository,
   )
   ```

**Step 2: Create the highlight labels router**

Create `backend/src/infrastructure/reading/routers/highlight_labels.py`:

```python
"""Router for highlight label management."""

from fastapi import APIRouter, Depends

from src.application.reading.use_cases.highlight_labels.create_global_highlight_label_use_case import (
    CreateGlobalHighlightLabelUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_book_highlight_labels_use_case import (
    GetBookHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_global_highlight_labels_use_case import (
    GetGlobalHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.update_highlight_label_use_case import (
    UpdateHighlightLabelUseCase,
)
from src.core import container
from src.domain.identity.entities.user import User
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user
from src.infrastructure.reading.schemas.highlight_schemas import (
    HighlightLabelCreate,
    HighlightLabelInBook,
    HighlightLabelUpdate,
)

router = APIRouter(tags=["highlight-labels"])


@router.get("/books/{book_id}/highlight-labels", response_model=list[HighlightLabelInBook])
def get_book_highlight_labels(
    book_id: int,
    current_user: User = Depends(get_current_user),
    use_case: GetBookHighlightLabelsUseCase = Depends(
        inject_use_case(container.get_book_highlight_labels_use_case)
    ),
) -> list[HighlightLabelInBook]:
    """Get all highlight labels for a book with resolved labels."""
    results = use_case.execute(book_id=book_id, user_id=current_user.id.value)
    return [
        HighlightLabelInBook(
            id=style.id.value,
            device_color=style.device_color,
            device_style=style.device_style,
            label=resolved.label,
            ui_color=resolved.ui_color,
            label_source=resolved.source,
            highlight_count=count,
        )
        for style, resolved, count in results
    ]


@router.patch("/highlight-labels/{style_id}", response_model=HighlightLabelInBook)
def update_highlight_label(
    style_id: int,
    body: HighlightLabelUpdate,
    current_user: User = Depends(get_current_user),
    use_case: UpdateHighlightLabelUseCase = Depends(
        inject_use_case(container.update_highlight_label_use_case)
    ),
) -> HighlightLabelInBook:
    """Update label and/or ui_color on a highlight style."""
    style = use_case.execute(
        style_id=style_id,
        user_id=current_user.id.value,
        label=body.label,
        ui_color=body.ui_color,
    )
    return HighlightLabelInBook(
        id=style.id.value,
        device_color=style.device_color,
        device_style=style.device_style,
        label=style.label,
        ui_color=style.ui_color,
        label_source="book" if style.book_id else "global",
        highlight_count=0,  # Not critical for PATCH response
    )


@router.get("/highlight-labels/global", response_model=list[HighlightLabelInBook])
def get_global_highlight_labels(
    current_user: User = Depends(get_current_user),
    use_case: GetGlobalHighlightLabelsUseCase = Depends(
        inject_use_case(container.get_global_highlight_labels_use_case)
    ),
) -> list[HighlightLabelInBook]:
    """Get all global default highlight labels."""
    styles = use_case.execute(user_id=current_user.id.value)
    return [
        HighlightLabelInBook(
            id=s.id.value,
            device_color=s.device_color,
            device_style=s.device_style,
            label=s.label,
            ui_color=s.ui_color,
            label_source="global",
            highlight_count=0,
        )
        for s in styles
    ]


@router.post("/highlight-labels/global", response_model=HighlightLabelInBook, status_code=201)
def create_global_highlight_label(
    body: HighlightLabelCreate,
    current_user: User = Depends(get_current_user),
    use_case: CreateGlobalHighlightLabelUseCase = Depends(
        inject_use_case(container.create_global_highlight_label_use_case)
    ),
) -> HighlightLabelInBook:
    """Create a global default highlight label."""
    style = use_case.execute(
        user_id=current_user.id.value,
        device_color=body.device_color,
        device_style=body.device_style,
        label=body.label,
        ui_color=body.ui_color,
    )
    return HighlightLabelInBook(
        id=style.id.value,
        device_color=style.device_color,
        device_style=style.device_style,
        label=style.label,
        ui_color=style.ui_color,
        label_source="global",
        highlight_count=0,
    )
```

**Step 3: Register router in main.py**

In `backend/src/main.py`, add to the Reading section imports and router registration:

```python
from src.infrastructure.reading.routers import highlight_labels
# ...
app.include_router(highlight_labels.router, prefix=settings.API_V1_PREFIX)
```

**Step 4: Run type check**

Run: `cd backend && .venv/bin/pyright src/infrastructure/reading/routers/highlight_labels.py src/core.py src/main.py`

**Step 5: Commit**

```bash
git add backend/src/core.py backend/src/infrastructure/reading/routers/highlight_labels.py backend/src/main.py
git commit -m "Add highlight-labels router and wire use cases into DI container"
```

---

### Task 16: Update test fixtures and conftest

**Files:**
- Modify: `backend/tests/conftest.py`

**Step 1: Update create_test_highlight**

The `create_test_highlight` helper creates ORM Highlight models directly. Update it to handle `highlight_style_id` instead of the old JSON `highlight_style` column:

1. Add `highlight_style_id: int | None = None` parameter
2. Pass it to the `Highlight()` constructor
3. Remove any reference to `highlight_style` JSON

**Step 2: Add create_test_highlight_style helper**

Add a helper function:

```python
from src.models import HighlightStyle as HighlightStyleORM

def create_test_highlight_style(
    db_session: Session,
    user_id: int,
    book_id: int,
    device_color: str = "gray",
    device_style: str = "lighten",
    label: str | None = None,
    ui_color: str | None = None,
) -> HighlightStyleORM:
    """Create a test highlight style."""
    style = HighlightStyleORM(
        user_id=user_id,
        book_id=book_id,
        device_color=device_color,
        device_style=device_style,
        label=label,
        ui_color=ui_color,
    )
    db_session.add(style)
    db_session.commit()
    db_session.refresh(style)
    return style
```

**Step 3: Run type check**

Run: `cd backend && .venv/bin/pyright tests/conftest.py`

**Step 4: Commit**

```bash
git add backend/tests/conftest.py
git commit -m "Update test fixtures for highlight_style_id FK"
```

---

### Task 17: Fix existing tests

**Files:**
- Modify: Various test files that reference `highlight_style`

**Step 1: Find all test references to highlight_style**

Run: `rg "highlight_style" backend/tests/`

**Step 2: Update each test**

For each test that references `highlight_style` in response assertions, update to expect the new fields (`highlight_style_id`, `label`, `ui_color`) instead of the nested object.

For tests that create highlights via the API upload endpoint, the `color` and `drawer` fields on `HighlightCreate` are unchanged — no changes needed there.

**Step 3: Run the full test suite**

Run: `cd backend && .venv/bin/pytest -x`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/tests/
git commit -m "Fix existing tests for new highlight style response format"
```

---

### Task 18: Add tests for highlight labels feature

**Files:**
- Create: `backend/tests/test_highlight_labels.py`
- Create: `backend/tests/unit/domain/reading/services/test_highlight_style_resolver.py`

**Step 1: Add unit tests for HighlightStyleResolver**

Create `backend/tests/unit/domain/reading/services/__init__.py` and `backend/tests/unit/domain/reading/services/test_highlight_style_resolver.py`:

Test cases:
- `test_resolve_combination_book_label` — label set directly on combination+book style
- `test_resolve_color_only_book_fallback` — falls back to color-only book style
- `test_resolve_style_only_book_fallback` — falls back to style-only book style
- `test_resolve_global_combination_fallback` — falls back to global combination
- `test_resolve_global_color_fallback` — falls back to global color-only
- `test_resolve_global_style_fallback` — falls back to global style-only
- `test_resolve_no_label` — returns source="none" when nothing matches
- `test_priority_order` — verifies book > global and combination > individual

**Step 2: Add integration tests for highlight labels endpoints**

Create `backend/tests/test_highlight_labels.py`:

Test cases:
- `test_upload_creates_highlight_style` — uploading highlights auto-creates style rows
- `test_get_book_highlight_labels` — returns styles with resolved labels
- `test_update_highlight_label` — PATCH updates label and ui_color
- `test_get_global_labels` — returns global defaults
- `test_create_global_label` — creates a global default
- `test_highlight_response_includes_style_id` — verify highlight responses include `highlight_style_id`

**Step 3: Run all tests**

Run: `cd backend && .venv/bin/pytest -x`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/tests/test_highlight_labels.py backend/tests/unit/domain/reading/services/
git commit -m "Add tests for highlight labels feature and style resolver"
```

---

### Task 19: Wire label resolution into highlight responses

**Files:**
- Modify: Router files that return highlights (from Task 13)

Now that the resolver and repository are wired, update the routers to actually resolve labels instead of returning `None`.

This requires injecting `HighlightStyleRepository` and `HighlightStyleResolver` into the relevant use cases that return highlights (e.g., `HighlightSearchUseCase`, `GetBookDetailsUseCase`), or doing the resolution at the router level by fetching styles in batch.

The simplest approach: resolve at the router level for endpoints that return highlights. Add a helper that takes a list of highlight domain entities and resolves their labels in batch.

**Step 1: Create a router-level helper for label resolution**

This can be a utility function or added to the relevant routers. The helper:
1. Collects all unique `highlight_style_id` values from the highlights
2. Fetches the corresponding HighlightStyle entities
3. Fetches all styles for resolution (book + global)
4. Resolves labels for each style
5. Returns a mapping from `highlight_style_id` to resolved label

**Step 2: Apply the helper in each router**

Update each router endpoint that returns highlights to use the helper.

**Step 3: Run all tests**

Run: `cd backend && .venv/bin/pytest -x`
Expected: PASS

**Step 4: Commit**

```bash
git add backend/src/infrastructure/reading/routers/ backend/src/infrastructure/library/routers/ backend/src/infrastructure/learning/routers/
git commit -m "Wire label resolution into highlight responses"
```

---

### Task 20: Regenerate frontend types

**Files:**
- Frontend generated types (auto-generated)

**Step 1: Regenerate types**

Run the frontend type generation command (likely `npm run generate` or similar in the frontend directory) to update TypeScript types from the new OpenAPI spec.

**Step 2: Verify frontend types**

Check that the generated types include:
- `HighlightLabelInBook` with `id`, `device_color`, `device_style`, `label`, `ui_color`, `label_source`, `highlight_count`
- Updated `Highlight` response type with `highlight_style_id`, `label`, `ui_color` instead of old `highlight_style` object
- `HighlightLabelUpdate`, `HighlightLabelCreate` types

**Step 3: Run frontend type check**

Run: `cd frontend && npm run type-check`

**Step 4: Fix any frontend compilation errors**

Search frontend code for references to the old `highlight_style` field and update them.

**Step 5: Commit**

```bash
git add frontend/
git commit -m "Regenerate frontend types for highlight labels"
```

---

### Task 21: Final verification

**Step 1: Run full backend test suite**

Run: `cd backend && .venv/bin/pytest`
Expected: All tests PASS

**Step 2: Run backend linting**

Run: `cd backend && .venv/bin/ruff check .`
Expected: No errors

**Step 3: Run backend type checking**

Run: `cd backend && .venv/bin/pyright`
Expected: No errors

**Step 4: Run frontend checks**

Run: `cd frontend && npm run lint && npm run type-check`
Expected: No errors

**Step 5: Verify no stale imports**

Run: `rg "from.*highlight_style import" backend/src/ --type py`
Verify all imports point to correct locations.

Run: `rg "HighlightStyleResponse" backend/`
Expected: No results (fully removed)
