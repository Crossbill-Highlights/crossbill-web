# Book ID: Integer to UUID Migration

## Context

Book IDs are currently auto-incrementing integers. This causes problems for features like cover image caching (integer IDs are guessable, so cover endpoints require authentication, which prevents browser HTTP caching). UUIDs are the better default for entity identifiers — this migration switches `books.id` from `int` to `UUID`.

## Scope

- Migrate `books.id` from `int` to `UUID`
- Migrate all 9 foreign keys referencing `books.id`
- Rename cover files from `{int}.jpg` to `{uuid}.jpg`
- Update all backend layers (domain, ORM, repositories, use cases, routers, schemas)
- Update frontend (generated API types, route params, components)

**Out of scope** (follow-up PR): Cover caching improvement (unauthenticated cover endpoint, `cover_url` field, removal of `useAuthenticatedImage`).

## Migration Strategy

Four sequential steps. Steps 1-2 can be deployed independently. Steps 3-4 must be deployed together.

### Step 1: Alembic Migration — Add UUID Columns

Migration `050_add_uuid_columns_to_books.py`.

**Books table:**
- Add column `uuid UUID NOT NULL DEFAULT gen_random_uuid()` with unique index
- Backfill existing rows with generated UUIDs

**Referencing tables** (all with `ON DELETE CASCADE`):

| Table | Current FK column | New column |
|-------|-------------------|------------|
| chapters | book_id (int, NOT NULL) | book_uuid (UUID) |
| highlights | book_id (int, NOT NULL) | book_uuid (UUID) |
| highlight_styles | book_id (int, nullable) | book_uuid (UUID, nullable) |
| highlight_tags | book_id (int, NOT NULL) | book_uuid (UUID) |
| highlight_tag_groups | book_id (int, NOT NULL) | book_uuid (UUID) |
| bookmarks | book_id (int, NOT NULL) | book_uuid (UUID) |
| flashcards | book_id (int, NOT NULL) | book_uuid (UUID) |
| reading_sessions | book_id (int, NOT NULL) | book_uuid (UUID) |
| book_tags | book_id (int, NOT NULL, composite PK) | book_uuid (UUID) |

Backfill process:
1. Add `book_uuid` columns as nullable
2. `UPDATE <table> SET book_uuid = books.uuid FROM books WHERE <table>.book_id = books.id`
3. Set `book_uuid` to NOT NULL (except `highlight_styles` which allows nullable `book_id`)

Existing code continues to work — int columns untouched.

### Step 2: Cover File Rename Script

Standalone Python script (not an Alembic migration):

1. Query `SELECT id, uuid FROM books`
2. For each book with a cover file `{BOOK_COVERS_DIR}/{id}.jpg`, rename to `{BOOK_COVERS_DIR}/{uuid}.jpg`
3. Same for S3: `book-covers/{id}.jpg` -> `book-covers/{uuid}.jpg`
4. Idempotent: skip if target already exists or source doesn't exist
5. Log all operations

Runs after Step 1, before Step 3.

### Step 3: Alembic Migration — Switch to UUID Primary/Foreign Keys

Migration `051_switch_books_to_uuid_pk.py`.

1. Drop all int-based FK constraints on referencing tables
2. Drop `book_tags` composite PK
3. Drop `books.id` int PK
4. Drop old int `book_id` columns on all referencing tables
5. Drop old int `id` column on books
6. Rename: `books.uuid` -> `books.id`, `*.book_uuid` -> `*.book_id`
7. Create PK on `books.id` (UUID)
8. Recreate FKs from `*.book_id` (UUID) -> `books.id` (UUID) with `ON DELETE CASCADE`
9. Recreate `book_tags` composite PK with UUID `book_id`

### Step 4: Code Changes

Deployed together with Step 3.

#### Domain Layer

**`src/domain/common/value_objects/ids.py` — BookId:**
- `value: int` -> `value: UUID`
- Remove non-negative validation
- Update `generate()` to return `cls(uuid4())`

#### ORM Model (`src/models.py`)

- `Book.id`: `Mapped[int]` -> `Mapped[UUID]` with `default=uuid4`
- All 9 referencing models: `book_id: Mapped[int]` -> `Mapped[UUID]`
- `book_tags` association table: `Integer` -> `Uuid`

#### Repositories

- Book repository: queries use `book_id.value` — adapts automatically with value object change
- File repository + S3 repository: file naming uses `str(book_id.value)` (UUID string) instead of int. Glob patterns unchanged (`{book_id.value}.*`)

#### Use Cases

- All use cases accepting `book_id: int` change to `book_id: UUID` (or accept string, parse to UUID)

#### Routers / API

- Path parameters: `book_id: int` -> `book_id: UUID` (FastAPI handles UUID path params)
- Pydantic schemas: `id: int` -> `id: str` (UUID serialized as string)

#### Frontend

- Regenerate API types from OpenAPI spec — `bookId: number` -> `bookId: string`
- Remove `Number(bookId)` conversions in route components
- `BookCover` component: `bookId: number` -> `bookId: string`
- `BookCard`: `String(book.id)` -> `book.id` for route params

#### Tests

- Update all test fixtures creating books with int IDs to use UUIDs

## Affected Files

### Backend
- `src/domain/common/value_objects/ids.py`
- `src/domain/library/entities/book.py`
- `src/models.py`
- `src/infrastructure/library/repositories/book_repository.py`
- `src/infrastructure/library/repositories/file_repository.py`
- `src/infrastructure/library/repositories/s3_file_repository.py`
- `src/infrastructure/library/schemas/book_schemas.py`
- `src/infrastructure/library/routers/books.py`
- `src/infrastructure/library/routers/ereader.py`
- `src/application/library/use_cases/book_queries/*.py`
- `src/application/library/use_cases/book_management/*.py`
- `src/application/library/use_cases/book_files/*.py`
- `src/application/library/protocols/file_repository.py`
- `src/domain/library/services/book_details_aggregator.py`
- `alembic/versions/050_*.py` (new)
- `alembic/versions/051_*.py` (new)
- `scripts/rename_cover_files.py` (new)
- Test files referencing book IDs

### Frontend
- `src/api/generated/` (regenerated)
- `src/components/BookCover.tsx`
- `src/hooks/useAuthenticatedImage.ts` (unchanged in this PR, removed in follow-up)
- `src/pages/LandingPage/components/BookCard.tsx`
- `src/pages/BookPage/BookTitle/BookTitle.tsx`
- `src/pages/BookPage/BookTitle/BookEditModal.tsx`
- `src/pages/BookPage/BookPage.tsx`
- Route files under `src/routes/book.$bookId/`
