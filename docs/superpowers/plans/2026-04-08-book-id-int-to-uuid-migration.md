# Book ID: Integer to UUID Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `books.id` from auto-incrementing integer to UUID, including all foreign keys, file storage, API layer, and frontend.

**Architecture:** Four sequential phases: (1) Alembic migration adding UUID columns alongside existing int columns, (2) cover file rename script using both columns, (3) Alembic migration dropping int columns and promoting UUIDs to PK/FKs, (4) code changes across all layers. Phases 1-2 deploy independently; phases 3-4 deploy together.

**Tech Stack:** Python/FastAPI, SQLAlchemy, Alembic, PostgreSQL, React/TypeScript, TanStack Router, orval (API codegen)

**Spec:** `docs/superpowers/specs/2026-04-08-book-id-int-to-uuid-migration-design.md`

---

## File Structure

### New files
- `backend/alembic/versions/050_add_uuid_columns_to_books.py` — Phase 1 migration
- `backend/scripts/rename_cover_files.py` — Phase 2 cover file rename script
- `backend/alembic/versions/051_switch_books_to_uuid_pk.py` — Phase 3 migration

### Modified files (Phase 4 — code changes)

**Domain layer:**
- `backend/src/domain/common/value_objects/ids.py` — Change `BookId.value` from `int` to `UUID`

**ORM model:**
- `backend/src/models.py` — Change `Book.id` to UUID, change `book_id` FK columns on 8 models + `book_tags` association table

**Mapper:**
- `backend/src/infrastructure/library/mappers/book_mapper.py` — `BookId(orm_model.id)` now wraps UUID

**Schemas:**
- `backend/src/infrastructure/library/schemas/book_schemas.py` — `id: int` -> `id: str` in `BookWithHighlightCount`
- `backend/src/infrastructure/reading/schemas/highlight_schemas.py` — `id: int` -> `id: str` in `BookDetails`
- `backend/src/infrastructure/library/schemas/book_schemas.py` — `book_id: int` -> `book_id: str` in `EreaderBookMetadata`

**Routers:**
- `backend/src/infrastructure/library/routers/books.py` — `book_id: int` -> `book_id: UUID` in path params, `id=book.id.value` -> `id=str(book.id.value)` in schema construction
- `backend/src/infrastructure/library/routers/ereader.py` — `book_id=metadata.book_id` now passes string

**Use cases:**
- `backend/src/application/library/use_cases/book_files/book_cover_use_case.py` — `book_id: int` -> `book_id: UUID` param
- `backend/src/application/library/use_cases/book_queries/get_books_with_counts_use_case.py` — `user_id: int` stays, no book_id param to change
- `backend/src/application/library/use_cases/book_queries/get_ereader_metadata_use_case.py` — `EreaderMetadata.book_id: int` -> `str`
- `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py` — `book_id: int` -> `book_id: UUID`
- `backend/src/application/library/use_cases/book_management/update_book_use_case.py` — `book_id: int` -> `book_id: UUID`
- `backend/src/application/library/use_cases/book_management/delete_book_use_case.py` — `book_id: int` -> `book_id: UUID`

**Frontend:**
- `frontend/src/components/BookCover.tsx` — `bookId: number` -> `bookId: string`
- `frontend/src/pages/LandingPage/components/BookCard.tsx` — Remove `String(book.id)` conversion
- `frontend/src/pages/BookPage/BookPage.tsx` — Remove `Number(bookId)` conversion
- `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx` — BookCover prop now string
- `frontend/src/pages/BookPage/BookTitle/BookEditModal.tsx` — BookCover prop now string
- `frontend/src/api/generated/` — Regenerated from OpenAPI spec

**Tests:**
- `backend/tests/conftest.py` — `create_test_book` adapts (ORM model handles UUID generation)
- `backend/tests/test_books.py` — API calls use UUID strings instead of ints
- Other test files using `book.id` as int

---

## Task 1: Alembic Migration — Add UUID Columns

**Files:**
- Create: `backend/alembic/versions/050_add_uuid_columns_to_books.py`

- [ ] **Step 1: Create the migration file**

```python
"""Add UUID columns to books and referencing tables.

Revision ID: 050
Revises: 049
Create Date: 2026-04-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "050"
down_revision: str = "049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add uuid column to books with default
    op.add_column(
        "books",
        sa.Column(
            "uuid",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_books_uuid", "books", ["uuid"])
    op.create_index("ix_books_uuid", "books", ["uuid"])

    # 2. Add book_uuid columns to all referencing tables (nullable first)
    referencing_tables = [
        ("chapters", False),
        ("highlights", False),
        ("highlight_styles", True),  # nullable FK
        ("highlight_tags", False),
        ("highlight_tag_groups", False),
        ("bookmarks", False),
        ("flashcards", False),
        ("reading_sessions", False),
        ("book_tags", False),
    ]

    for table_name, is_nullable in referencing_tables:
        op.add_column(
            table_name,
            sa.Column("book_uuid", UUID(as_uuid=True), nullable=True),
        )

    # 3. Backfill book_uuid from books.uuid via join on book_id
    for table_name, is_nullable in referencing_tables:
        op.execute(
            sa.text(
                f"UPDATE {table_name} SET book_uuid = books.uuid "
                f"FROM books WHERE {table_name}.book_id = books.id"
            )
        )

    # 4. Set NOT NULL on non-nullable FK columns
    for table_name, is_nullable in referencing_tables:
        if not is_nullable:
            op.alter_column(table_name, "book_uuid", nullable=False)

    # 5. Add indexes on book_uuid columns
    for table_name, _is_nullable in referencing_tables:
        op.create_index(
            f"ix_{table_name}_book_uuid", table_name, ["book_uuid"]
        )


def downgrade() -> None:
    referencing_tables = [
        "chapters",
        "highlights",
        "highlight_styles",
        "highlight_tags",
        "highlight_tag_groups",
        "bookmarks",
        "flashcards",
        "reading_sessions",
        "book_tags",
    ]

    for table_name in referencing_tables:
        op.drop_index(f"ix_{table_name}_book_uuid", table_name=table_name)
        op.drop_column(table_name, "book_uuid")

    op.drop_index("ix_books_uuid", table_name="books")
    op.drop_constraint("uq_books_uuid", "books", type_="unique")
    op.drop_column("books", "uuid")
```

- [ ] **Step 2: Run the migration**

Run: `cd backend && uv run alembic upgrade head`
Expected: Migration applies successfully, no errors.

- [ ] **Step 3: Verify the migration**

Run: `cd backend && uv run python -c "import asyncio; from sqlalchemy import text; from src.db import async_session_maker; exec(open('/dev/stdin').read())" <<'EOF'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import settings

async def check():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, uuid FROM books LIMIT 5"))
        for row in result:
            print(f"id={row[0]}, uuid={row[1]}")
        result2 = await conn.execute(text("SELECT book_id, book_uuid FROM chapters LIMIT 5"))
        for row in result2:
            print(f"chapter book_id={row[0]}, book_uuid={row[1]}")

asyncio.run(check())
EOF
```

Expected: Both int id and UUID columns present with matching relationships.

- [ ] **Step 4: Run existing tests to confirm nothing is broken**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: All tests pass (the UUID columns exist but existing code doesn't use them yet).

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/050_add_uuid_columns_to_books.py
git commit -m "feat: add UUID columns to books and referencing tables (migration 050)"
```

---

## Task 2: Cover File Rename Script

**Files:**
- Create: `backend/scripts/rename_cover_files.py`

- [ ] **Step 1: Create the rename script**

```python
"""Rename cover files from {int_id}.jpg to {uuid}.jpg.

Run after migration 050 (UUID columns added) and before migration 051 (int columns dropped).

Usage:
    cd backend && uv run python -m scripts.rename_cover_files
    cd backend && uv run python -m scripts.rename_cover_files --dry-run
"""

import argparse
import asyncio
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.config import BOOK_COVERS_DIR, settings

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def rename_covers(dry_run: bool = False) -> None:
    """Rename cover files from {int_id}.* to {uuid}.*"""
    engine = create_async_engine(settings.database_url)

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, uuid FROM books"))
        books = result.fetchall()

    logger.info(f"Found {len(books)} books in database")

    renamed = 0
    skipped = 0
    missing = 0

    for int_id, book_uuid in books:
        # Find cover files matching the int ID pattern
        cover_files = list(BOOK_COVERS_DIR.glob(f"{int_id}.*"))

        if not cover_files:
            missing += 1
            continue

        for cover_file in cover_files:
            new_name = BOOK_COVERS_DIR / f"{book_uuid}{cover_file.suffix}"

            if new_name.exists():
                logger.warning(f"Target already exists, skipping: {new_name}")
                skipped += 1
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Would rename: {cover_file.name} -> {new_name.name}")
            else:
                cover_file.rename(new_name)
                logger.info(f"Renamed: {cover_file.name} -> {new_name.name}")
            renamed += 1

    await engine.dispose()

    logger.info(f"Done. Renamed: {renamed}, Skipped: {skipped}, No cover: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename book cover files from int IDs to UUIDs")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without renaming")
    args = parser.parse_args()

    asyncio.run(rename_covers(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add `__init__.py` for scripts package if needed**

Run: `touch backend/scripts/__init__.py` (only if the directory doesn't already have one)

- [ ] **Step 3: Test with dry run**

Run: `cd backend && uv run python -m scripts.rename_cover_files --dry-run`
Expected: Logs showing which files would be renamed, no actual changes.

- [ ] **Step 4: Run the rename**

Run: `cd backend && uv run python -m scripts.rename_cover_files`
Expected: Cover files renamed from `{int}.jpg` to `{uuid}.jpg`.

- [ ] **Step 5: Commit**

```bash
git add backend/scripts/
git commit -m "feat: add cover file rename script (int ID to UUID)"
```

---

## Task 3: Alembic Migration — Switch to UUID Primary/Foreign Keys

**Files:**
- Create: `backend/alembic/versions/051_switch_books_to_uuid_pk.py`

- [ ] **Step 1: Create the migration file**

```python
"""Switch books from int PK to UUID PK.

Drops int id/book_id columns, renames uuid/book_uuid columns to id/book_id,
and recreates primary keys and foreign keys.

Revision ID: 051
Revises: 050
Create Date: 2026-04-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "051"
down_revision: str = "050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables that reference books.id with their FK constraint names and nullability
REFERENCING_TABLES = [
    "chapters",
    "highlights",
    "highlight_styles",
    "highlight_tags",
    "highlight_tag_groups",
    "bookmarks",
    "flashcards",
    "reading_sessions",
    "book_tags",
]


def upgrade() -> None:
    # 1. Drop all existing FK constraints on book_id (int) columns
    #    We need to look up the actual constraint names from the DB
    for table_name in REFERENCING_TABLES:
        op.drop_constraint(
            f"{table_name}_book_id_fkey", table_name, type_="foreignkey"
        )

    # 2. Drop book_tags composite PK (contains int book_id)
    op.drop_constraint("book_tags_pkey", "book_tags", type_="primary")

    # 3. Drop books int PK
    op.drop_constraint("books_pkey", "books", type_="primary")

    # 4. Drop old int columns
    for table_name in REFERENCING_TABLES:
        op.drop_index(f"ix_{table_name}_book_id", table_name=table_name)
        op.drop_column(table_name, "book_id")

    op.drop_column("books", "id")

    # 5. Rename uuid columns to id/book_id
    op.alter_column("books", "uuid", new_column_name="id")

    for table_name in REFERENCING_TABLES:
        op.alter_column(table_name, "book_uuid", new_column_name="book_id")
        # Rename the index too
        op.drop_index(f"ix_{table_name}_book_uuid", table_name=table_name)
        op.create_index(f"ix_{table_name}_book_id", table_name, ["book_id"])

    # 6. Create new PK on books.id (UUID)
    #    First drop the unique constraint (PK implies uniqueness)
    op.drop_constraint("uq_books_uuid", "books", type_="unique")
    op.drop_index("ix_books_uuid", table_name="books")
    op.create_primary_key("books_pkey", "books", ["id"])
    op.create_index("ix_books_id", "books", ["id"])

    # 7. Recreate FK constraints pointing to UUID books.id
    for table_name in REFERENCING_TABLES:
        op.create_foreign_key(
            f"{table_name}_book_id_fkey",
            table_name,
            "books",
            ["book_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # 8. Recreate book_tags composite PK
    op.create_primary_key("book_tags_pkey", "book_tags", ["book_id", "tag_id"])

    # 9. Remove the server_default on books.id (app will provide UUIDs)
    op.alter_column("books", "id", server_default=None)


def downgrade() -> None:
    # This migration is not safely reversible without data loss.
    # The int IDs have been dropped and cannot be reconstructed.
    raise RuntimeError(
        "Downgrade not supported: int book IDs have been dropped. "
        "Restore from backup if needed."
    )
```

- [ ] **Step 2: Verify FK constraint names match your database**

Before running, check the actual constraint names:

Run:
```bash
cd backend && uv run python -c "
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config import settings

async def check():
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as conn:
        result = await conn.execute(text(\"\"\"
            SELECT tc.table_name, tc.constraint_name, tc.constraint_type
            FROM information_schema.table_constraints tc
            WHERE tc.constraint_name LIKE '%book%'
            ORDER BY tc.table_name, tc.constraint_type
        \"\"\"))
        for row in result:
            print(f'{row[0]}: {row[1]} ({row[2]})')
    await engine.dispose()

asyncio.run(check())
"
```

Expected: List of constraint names. If any don't match the `{table_name}_book_id_fkey` pattern, update the migration accordingly.

- [ ] **Step 3: This migration is applied together with Task 4 code changes — do not run it yet**

Commit the migration file only:

```bash
git add backend/alembic/versions/051_switch_books_to_uuid_pk.py
git commit -m "feat: migration to switch books PK from int to UUID (migration 051)"
```

---

## Task 4: Domain Layer — Change BookId Value Object

**Files:**
- Modify: `backend/src/domain/common/value_objects/ids.py:6-14`

- [ ] **Step 1: Update BookId to use UUID**

In `backend/src/domain/common/value_objects/ids.py`, replace the BookId class:

```python
# Old (lines 6-14):
@dataclass(frozen=True)
class BookId(EntityId):
    """Strongly-typed book identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("BookId must be non-negative")

# New:
@dataclass(frozen=True)
class BookId(EntityId):
    """Strongly-typed book identifier."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise TypeError(f"BookId value must be a UUID, got {type(self.value).__name__}")

    @classmethod
    def generate(cls) -> "BookId":
        """Generate a new random BookId."""
        return cls(uuid4())
```

Also add the import at the top of the file:

```python
from uuid import UUID, uuid4
```

- [ ] **Step 2: Verify the import doesn't conflict**

Check that `UUID` isn't already imported. The base `EntityId` in `entity.py` already imports `UUID` from `uuid`, but `ids.py` needs its own import.

Run: `cd backend && uv run pyright src/domain/common/value_objects/ids.py`
Expected: No errors (other files will have errors until we update them — that's expected).

- [ ] **Step 3: Commit**

```bash
git add backend/src/domain/common/value_objects/ids.py
git commit -m "feat: change BookId value object from int to UUID"
```

---

## Task 5: ORM Model — Change Column Types

**Files:**
- Modify: `backend/src/models.py`

- [ ] **Step 1: Add UUID import**

At the top of `backend/src/models.py`, add to imports:

```python
from uuid import uuid4
```

And ensure `sqlalchemy.dialects.postgresql` import includes `UUID`:

```python
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
```

- [ ] **Step 2: Update Book model primary key**

Change `backend/src/models.py` line 170:

```python
# Old:
id: Mapped[int] = mapped_column(primary_key=True, index=True)

# New:
id: Mapped[uuid_lib.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
```

Note: You'll need `import uuid as uuid_lib` at the top to use `Mapped[uuid_lib.UUID]` (to avoid conflict with the PG_UUID alias). Alternatively, use the stdlib UUID directly:

```python
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PgUUID

# Then in the model:
id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
```

Choose whichever import style doesn't conflict with existing imports in models.py.

- [ ] **Step 3: Update book_tags association table**

Change `backend/src/models.py` line 30 (in the `book_tags` Table definition):

```python
# Old:
"book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, index=True

# New:
"book_id", PgUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, index=True
```

- [ ] **Step 4: Update all 8 models with book_id foreign key**

For each of these models, change `book_id` from `Mapped[int]` to `Mapped[UUID]`:

**Chapter** (line 240):
```python
# Old:
book_id: Mapped[int] = mapped_column(
    ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
)
# New:
book_id: Mapped[UUID] = mapped_column(
    PgUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
)
```

**HighlightStyle** (line 294):
```python
# Old:
book_id: Mapped[int | None] = mapped_column(
    ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=True
)
# New:
book_id: Mapped[UUID | None] = mapped_column(
    PgUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=True
)
```

**Highlight** (line 333):
```python
# Old:
book_id: Mapped[int] = mapped_column(
    ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
)
# New:
book_id: Mapped[UUID] = mapped_column(
    PgUUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), index=True, nullable=False
)
```

**HighlightTagGroup** (line 436):
```python
# Same pattern: Mapped[int] -> Mapped[UUID], add PgUUID(as_uuid=True)
```

**HighlightTag** (line 471):
```python
# Same pattern
```

**Bookmark** (line 514):
```python
# Same pattern
```

**Flashcard** (line 542):
```python
# Same pattern
```

**ReadingSession** (line 585):
```python
# Same pattern
```

- [ ] **Step 5: Run type check on models**

Run: `cd backend && uv run pyright src/models.py`
Expected: May have errors from other files importing these, but models.py itself should be clean.

- [ ] **Step 6: Commit**

```bash
git add backend/src/models.py
git commit -m "feat: change Book ORM model and FKs from int to UUID"
```

---

## Task 6: Schemas — Change ID Types

**Files:**
- Modify: `backend/src/infrastructure/library/schemas/book_schemas.py`
- Modify: `backend/src/infrastructure/reading/schemas/highlight_schemas.py`

- [ ] **Step 1: Update BookWithHighlightCount schema**

In `backend/src/infrastructure/library/schemas/book_schemas.py`, change the `id` field (line 61):

```python
# Old:
id: int

# New:
id: str
```

- [ ] **Step 2: Update EreaderBookMetadata schema**

In the same file (line 116):

```python
# Old:
book_id: int = Field(..., description="Internal book ID")

# New:
book_id: str = Field(..., description="Internal book ID")
```

- [ ] **Step 3: Update BookDetails schema**

In `backend/src/infrastructure/reading/schemas/highlight_schemas.py` (line 173):

```python
# Old:
id: int

# New:
id: str
```

- [ ] **Step 4: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/library/schemas/book_schemas.py src/infrastructure/reading/schemas/highlight_schemas.py`
Expected: No errors in these files.

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/library/schemas/book_schemas.py backend/src/infrastructure/reading/schemas/highlight_schemas.py
git commit -m "feat: change book ID type from int to str in Pydantic schemas"
```

---

## Task 7: Routers — Change Path Parameters and Schema Construction

**Files:**
- Modify: `backend/src/infrastructure/library/routers/books.py`
- Modify: `backend/src/infrastructure/library/routers/ereader.py`

- [ ] **Step 1: Add UUID import to books router**

In `backend/src/infrastructure/library/routers/books.py`, add at top:

```python
from uuid import UUID
```

- [ ] **Step 2: Update all endpoint path parameters**

Change every `book_id: int` path parameter to `book_id: UUID`. These are at:

- `get_book_details` (around line 340): `book_id: int` -> `book_id: UUID`
- `update_book` (line 372): `book_id: int` -> `book_id: UUID`
- `delete_book` (find the endpoint): `book_id: int` -> `book_id: UUID`
- `get_book_cover` (line 443): `book_id: int` -> `book_id: UUID`

FastAPI handles UUID path parameters natively — it will parse the UUID string from the URL automatically.

- [ ] **Step 3: Update schema construction — BookWithHighlightCount**

Every place that constructs `BookWithHighlightCount(id=book.id.value, ...)` needs to serialize the UUID to string:

```python
# Old:
id=book.id.value,

# New:
id=str(book.id.value),
```

This appears in:
- `get_books` endpoint (around line 256)
- `get_recently_viewed_books` endpoint (around line 319)
- `update_book` endpoint (line 396)

- [ ] **Step 4: Update schema construction — BookDetails**

In `_build_book_details_schema()` (around line 161):

```python
# Old:
id=agg.book.id.value,

# New:
id=str(agg.book.id.value),
```

- [ ] **Step 5: Update ereader router**

In `backend/src/infrastructure/library/routers/ereader.py`, the `EreaderBookMetadata` construction (lines 62, 100) uses `book_id=metadata.book_id`. This will work if `EreaderMetadata.book_id` is updated to `str` (done in Task 8).

No changes needed in the ereader router itself — it doesn't take book_id as a path parameter (it uses `client_book_id`).

- [ ] **Step 6: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/library/routers/books.py src/infrastructure/library/routers/ereader.py`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add backend/src/infrastructure/library/routers/books.py backend/src/infrastructure/library/routers/ereader.py
git commit -m "feat: change book_id path params from int to UUID in routers"
```

---

## Task 8: Use Cases — Change Parameter Types

**Files:**
- Modify: `backend/src/application/library/use_cases/book_files/book_cover_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_queries/get_ereader_metadata_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_management/update_book_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_management/delete_book_use_case.py`

- [ ] **Step 1: Update BookCoverUseCase**

In `backend/src/application/library/use_cases/book_files/book_cover_use_case.py`, change `get_cover`:

```python
# Old (line 24):
async def get_cover(self, book_id: int, user_id: int) -> bytes | None:
    ...
    book_id_vo = BookId(book_id)

# New:
async def get_cover(self, book_id: UUID, user_id: int) -> bytes | None:
    ...
    book_id_vo = BookId(book_id)
```

Add import at top:

```python
from uuid import UUID
```

- [ ] **Step 2: Update EreaderMetadata dataclass**

In `backend/src/application/library/use_cases/book_queries/get_ereader_metadata_use_case.py`:

```python
# Old (line 15):
book_id: int

# New:
book_id: str
```

And update the construction (line 57):

```python
# Old:
book_id=book.id.value,

# New:
book_id=str(book.id.value),
```

- [ ] **Step 3: Update GetBookDetailsUseCase**

In `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py`, change the `get_book_details` method signature:

```python
# Old:
async def get_book_details(self, book_id: int, user_id: int) -> BookDetailsAggregation:
    ...
    book_id_vo = BookId(book_id)

# New:
async def get_book_details(self, book_id: UUID, user_id: int) -> BookDetailsAggregation:
    ...
    book_id_vo = BookId(book_id)
```

Add `from uuid import UUID` import.

- [ ] **Step 4: Update UpdateBookUseCase**

Same pattern — change `book_id: int` to `book_id: UUID` in the main method. Add UUID import.

- [ ] **Step 5: Update DeleteBookUseCase**

Same pattern — change `book_id: int` to `book_id: UUID`. Add UUID import.

- [ ] **Step 6: Run type check on all use cases**

Run: `cd backend && uv run pyright src/application/library/use_cases/`
Expected: No errors.

- [ ] **Step 7: Commit**

```bash
git add backend/src/application/library/use_cases/
git commit -m "feat: change book_id params from int to UUID in use cases"
```

---

## Task 9: Run Migration 051 and Full Backend Tests

**Files:** No new files — this validates Tasks 3-8 together.

- [ ] **Step 1: Run the migration**

Run: `cd backend && uv run alembic upgrade head`
Expected: Migration 051 applies successfully.

- [ ] **Step 2: Run full backend test suite**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: Tests may fail due to test fixtures still using int IDs — that's expected and fixed in Task 10.

- [ ] **Step 3: Run pyright on the full backend**

Run: `cd backend && uv run pyright`
Expected: Identify any remaining type errors for fixing.

---

## Task 10: Fix Tests

**Files:**
- Modify: `backend/tests/conftest.py`
- Modify: `backend/tests/test_books.py`
- Modify: Other test files as needed

- [ ] **Step 1: Update create_test_book helper**

In `backend/tests/conftest.py`, the `create_test_book` function (line 38) creates ORM `Book` objects directly. Since the ORM model now has `default=uuid4` on the `id` column, new books will get UUIDs automatically. The `user_id` parameter is still `int`.

No change needed to `create_test_book` itself — the ORM model's `default=uuid4` handles ID generation.

- [ ] **Step 2: Update test_books.py API calls**

In `backend/tests/test_books.py`, any test that constructs API URLs using integer book IDs needs updating. For example:

```python
# Old:
response = await client.get(f"/api/v1/books/{book.id}/cover")

# New (book.id is now a UUID):
response = await client.get(f"/api/v1/books/{book.id}/cover")
```

This actually works as-is because f-string formatting calls `str()` on UUIDs. But any test that asserts `response.json()["id"]` is an `int` needs updating:

```python
# Old:
assert response.json()["id"] == book.id

# New:
assert response.json()["id"] == str(book.id)
```

- [ ] **Step 3: Grep for any remaining int-based book ID usage in tests**

Run: `cd backend && grep -rn "BookId(" tests/ | grep -v __pycache__`

Update any `BookId(42)` or similar to `BookId(UUID('...'))` or `BookId(uuid4())`.

- [ ] **Step 4: Run full test suite**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: All tests pass.

- [ ] **Step 5: Run full pyright check**

Run: `cd backend && uv run pyright`
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add backend/tests/
git commit -m "fix: update tests for UUID book IDs"
```

---

## Task 11: Frontend — Update Components and Types

**Files:**
- Modify: `frontend/src/components/BookCover.tsx`
- Modify: `frontend/src/pages/LandingPage/components/BookCard.tsx`
- Modify: `frontend/src/pages/BookPage/BookPage.tsx`
- Modify: `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx`
- Modify: `frontend/src/pages/BookPage/BookTitle/BookEditModal.tsx`

- [ ] **Step 1: Regenerate API types**

Run: `cd frontend && npm run generate-api` (or whatever the orval generation command is)

Expected: Generated types in `frontend/src/api/generated/` update — `BookWithHighlightCount.id` changes from `number` to `string`, `BookDetails.id` changes from `number` to `string`. API function signatures change `bookId: number` to `bookId: string`.

- [ ] **Step 2: Update BookCover component**

In `frontend/src/components/BookCover.tsx`, change the prop type (line 7):

```typescript
// Old:
bookId: number;

// New:
bookId: string;
```

The `imageUrl` construction (line 43) works with strings already:
```typescript
const imageUrl = hasCover ? `${apiUrl}/api/v1/books/${bookId}/cover` : null;
```

No change needed there.

- [ ] **Step 3: Update BookCard**

In `frontend/src/pages/LandingPage/components/BookCard.tsx` (line 23):

```typescript
// Old:
params={{ bookId: String(book.id) }}

// New:
params={{ bookId: book.id }}
```

And the BookCover usage (line 43):

```typescript
// Old:
bookId={book.id}  // was number, now string — matches updated prop type
```

No change needed if prop type is already updated to `string`.

- [ ] **Step 4: Update BookPage**

In `frontend/src/pages/BookPage/BookPage.tsx` (line 20):

```typescript
// Old:
const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(Number(bookId));

// New:
const { data: book, isLoading, isError } = useGetBookDetailsApiV1BooksBookIdGet(bookId!);
```

The `bookId` from `useParams` is already a `string`. The generated API function now accepts `string` instead of `number`, so we can pass it directly.

- [ ] **Step 5: Update BookTitle and BookEditModal**

In `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx` (line 56) and `BookEditModal.tsx` (line 157):

The `BookCover` is called with `bookId={book.id}`. Since `book.id` is now `string` in the generated types and `BookCover` now accepts `string`, no change needed.

- [ ] **Step 6: Check for any remaining Number(bookId) conversions**

Run from the frontend directory:
```bash
grep -rn "Number(bookId\|Number(book\.id\|Number(book_id" frontend/src/ --include="*.tsx" --include="*.ts" | grep -v node_modules | grep -v generated
```

Update any remaining instances.

- [ ] **Step 7: Run frontend type check**

Run: `cd frontend && npm run type-check`
Expected: No type errors.

- [ ] **Step 8: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: No lint errors.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: update frontend for UUID book IDs"
```

---

## Task 12: Final Verification

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && uv run pytest --tb=short -q`
Expected: All tests pass.

- [ ] **Step 2: Run full backend type check**

Run: `cd backend && uv run pyright`
Expected: No errors.

- [ ] **Step 3: Run frontend type check and lint**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: No errors.

- [ ] **Step 4: Manual smoke test (optional)**

Start the app and verify:
1. Book list loads with UUID-based IDs in the response
2. Book detail page loads via UUID route
3. Book covers display correctly
4. Creating/updating a book works

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: final adjustments for book ID UUID migration"
```
