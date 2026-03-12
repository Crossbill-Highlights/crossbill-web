# FastAPI Sync-to-Async Migration Plan

## Overview

Migrate the backend from synchronous SQLAlchemy + sync FastAPI routes to fully async using SQLAlchemy's async extension. This improves concurrency under load — sync routes in FastAPI run in a threadpool, meaning each concurrent request consumes a thread, while async routes use cooperative multitasking on the event loop.

### Current State

- **35+ sync routes**, ~10 already async (auth, AI-powered endpoints)
- **14 repositories** — all synchronous, using `Session` directly
- **~50 use cases** — all synchronous
- **Database**: sync `create_engine` + `sessionmaker[Session]`, PostgreSQL via `psycopg[binary]`/`psycopg2-binary`
- **Tests**: sync `TestClient`, sync fixtures, in-memory SQLite with `StaticPool`
- **DI**: `dependency-injector` container with `providers.Dependency(instance_of=Session)`

---

## Phase 1: Add Async Dependencies

**Files changed:** `pyproject.toml`

### Steps

1. Add `aiosqlite` to dev dependencies (for async SQLite in tests)
2. Note: `psycopg[binary]` v3 already supports async mode natively — no need to add `asyncpg`. SQLAlchemy's `create_async_engine` works with `psycopg` v3 via the `postgresql+psycopg` dialect URL. The async adapter is built into psycopg v3.
3. Remove `psycopg2-binary` (legacy sync-only driver, no longer needed once migration is complete — can defer this to the end)
4. Add `greenlet` if not pulled in transitively (needed by SQLAlchemy async on some platforms)

### Dependency changes

```toml
# In [project] dependencies, no new package needed for PostgreSQL async
# psycopg v3 handles both sync and async

# In [dependency-groups] dev:
"aiosqlite>=0.20.0",  # async SQLite for tests
```

---

## Phase 2: Async Database Layer

**Files changed:** `backend/src/database.py`

### Steps

1. Replace `create_engine` → `create_async_engine` from `sqlalchemy.ext.asyncio`
2. Replace `sessionmaker[Session]` → `async_sessionmaker[AsyncSession]`
3. Convert `get_db()` from sync generator to async generator yielding `AsyncSession`
4. Update `DatabaseSession` type alias: `Annotated[AsyncSession, Depends(get_db)]`
5. Update `initialize_database()` to create async engine
6. Update `dispose_engine()` to use `await engine.dispose()` (or keep sync if called from lifespan which is already async)
7. Keep `Base` (DeclarativeBase) unchanged — ORM model definitions don't change

### Before

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

def get_db(session_factory: ...) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()

DatabaseSession = Annotated[Session, Depends(get_db)]
```

### After

```python
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

async def get_db(session_factory: ...) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as db:
        yield db

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
```

### Database URL changes

The async engine requires an async-compatible dialect string:
- PostgreSQL: `postgresql+psycopg://...` (psycopg v3 async mode, same URL works for both sync/async in psycopg v3)
- SQLite (tests): `sqlite+aiosqlite:///:memory:`

Update `Settings` or `initialize_database()` to handle the URL prefix if needed.

---

## Phase 3: Update DI Container and Injection Helper

**Files changed:** `backend/src/core.py`, `backend/src/infrastructure/common/di.py`

### Steps

1. Update the container's `db` dependency type from `Session` to `AsyncSession`:
   ```python
   db = providers.Dependency(instance_of=AsyncSession)
   ```

2. Update `inject_use_case()` — the function itself can remain synchronous since it's just wiring up the container override, but it now receives an `AsyncSession` via the `DatabaseSession` dependency:
   ```python
   def inject_use_case(provider: Provider[T]) -> Callable[[DatabaseSession], T]:
       def dependency(db: DatabaseSession) -> T:
           try:
               container.db.override(db)
               return provider()
           finally:
               container.db.reset_override()
       return dependency
   ```
   The signature stays the same; the `DatabaseSession` type alias change propagates automatically.

---

## Phase 4: Convert Repositories to Async

**Files changed:** All files in `backend/src/infrastructure/*/repositories/`

This is the largest phase. Every repository method that touches the database must become `async def` and `await` its database calls.

### Repositories to convert (14 total)

| Repository | Location |
|---|---|
| `UserRepository` | `infrastructure/identity/repositories/user_repository.py` |
| `BookRepository` | `infrastructure/library/repositories/book_repository.py` |
| `ChapterRepository` | `infrastructure/library/repositories/chapter_repository.py` |
| `TagRepository` | `infrastructure/library/repositories/tag_repository.py` |
| `FileRepository` | `infrastructure/library/repositories/file_repository.py` |
| `HighlightRepository` | `infrastructure/reading/repositories/highlight_repository.py` |
| `HighlightTagRepository` | `infrastructure/reading/repositories/highlight_tag_repository.py` |
| `HighlightStyleRepository` | `infrastructure/reading/repositories/highlight_style_repository.py` |
| `BookmarkRepository` | `infrastructure/reading/repositories/bookmark_repository.py` |
| `ReadingSessionRepository` | `infrastructure/reading/repositories/reading_session_repository.py` |
| `ChapterPrereadingRepository` | `infrastructure/reading/repositories/chapter_prereading_repository.py` |
| `FlashcardRepository` | `infrastructure/learning/repositories/flashcard_repository.py` |
| `AIUsageRepository` | `infrastructure/ai/repositories/ai_usage_repository.py` |
| `AIChatSessionRepository` | `infrastructure/learning/repositories/ai_chat_session_repository.py` |

### Conversion pattern

```python
# BEFORE (sync)
def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None:
    stmt = select(BookORM).where(BookORM.id == book_id.value)
    orm_model = self.db.execute(stmt).scalar_one_or_none()
    return self.mapper.to_domain(orm_model) if orm_model else None

def save(self, book: Book) -> Book:
    orm_model = self.mapper.to_orm(book)
    self.db.add(orm_model)
    self.db.commit()
    return self.mapper.to_domain(orm_model)

# AFTER (async)
async def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None:
    stmt = select(BookORM).where(BookORM.id == book_id.value)
    result = await self.db.execute(stmt)
    orm_model = result.scalar_one_or_none()
    return self.mapper.to_domain(orm_model) if orm_model else None

async def save(self, book: Book) -> Book:
    orm_model = self.mapper.to_orm(book)
    self.db.add(orm_model)       # add() is NOT awaited (it's synchronous)
    await self.db.commit()
    return self.mapper.to_domain(orm_model)
```

### Key async SQLAlchemy differences

| Sync | Async |
|---|---|
| `session.execute(stmt).scalars().all()` | `result = await session.execute(stmt); result.scalars().all()` |
| `session.execute(stmt).scalar_one_or_none()` | `result = await session.execute(stmt); result.scalar_one_or_none()` |
| `session.commit()` | `await session.commit()` |
| `session.rollback()` | `await session.rollback()` |
| `session.refresh(obj)` | `await session.refresh(obj)` |
| `session.delete(obj)` | `await session.delete(obj)` |
| `session.add(obj)` | `session.add(obj)` (**still sync**) |
| `session.flush()` | `await session.flush()` |

### Important: Lazy loading is disabled in async mode

SQLAlchemy async sessions do **not** support implicit lazy loading. Any relationship access that would trigger a lazy load will raise `MissingGreenlet`. Solutions:
- Use `selectinload()` or `joinedload()` in queries (already mostly done in this codebase)
- Use `await session.refresh(obj, ["relationship_name"])` when needed
- Audit all repository methods for implicit relationship access after `commit()`

### Repository protocol updates

If there are abstract base classes or Protocol definitions for repositories in the domain layer, their method signatures must also become `async def` and return `Coroutine`/`Awaitable` types. Check `backend/src/domain/*/repositories/` for any protocol definitions.

---

## Phase 5: Convert Use Cases to Async

**Files changed:** All files in `backend/src/application/*/use_cases/`

Every use case that calls repository methods must become async.

### Conversion pattern

```python
# BEFORE
class GetBookDetailsUseCase:
    def execute(self, book_id: int, user_id: int) -> BookDetails:
        book = self.book_repository.find_by_id(BookId(book_id), UserId(user_id))
        ...

# AFTER
class GetBookDetailsUseCase:
    async def execute(self, book_id: int, user_id: int) -> BookDetails:
        book = await self.book_repository.find_by_id(BookId(book_id), UserId(user_id))
        ...
```

### Use cases by domain (~50 total)

**Identity (4):** `RegisterUserUseCase`, `AuthenticateUserUseCase`, `RefreshAccessTokenUseCase`, `GetUserByIdUseCase`, `UpdateUserUseCase`

**Library (10):** `CreateBookUseCase`, `GetBookDetailsUseCase`, `UpdateBookUseCase`, `DeleteBookUseCase`, `GetBooksWithCountsUseCase`, `GetRecentlyViewedBooksUseCase`, `GetEreaderMetadataUseCase`, `BookCoverUseCase`, `EbookUploadUseCase`, `EbookDeletionUseCase`, `AddTagsToBookUseCase`, `ReplaceBookTagsUseCase`, `GetBookTagsUseCase`

**Reading (25+):** All bookmark, highlight, highlight tag, highlight label, reading session, chapter prereading, and chapter content use cases

**Learning (9):** All flashcard and quiz use cases

### Note on use cases that call other use cases

Some use cases compose other use cases (e.g., `CreateBookUseCase` calls `AddTagsToBookUseCase`). These inner calls also need `await`.

---

## Phase 6: Convert Routes to Async

**Files changed:** All files in `backend/src/infrastructure/*/routers/`

### Steps

1. Convert all remaining `def` route handlers to `async def`
2. Add `await` to all use case `.execute()` calls
3. The ~10 routes that are already `async def` also need `await` added to their use case calls (they're currently async but calling sync use cases)

### Example

```python
# BEFORE
@router.get("/books/")
def get_books(
    db: DatabaseSession,
    use_case: GetBooksWithCountsUseCase = Depends(...),
    current_user: User = Depends(get_current_user),
) -> list[BookWithCountsResponse]:
    books = use_case.execute(current_user.id.value)
    return [BookWithCountsResponse.from_domain(b) for b in books]

# AFTER
@router.get("/books/")
async def get_books(
    db: DatabaseSession,
    use_case: GetBooksWithCountsUseCase = Depends(...),
    current_user: User = Depends(get_current_user),
) -> list[BookWithCountsResponse]:
    books = await use_case.execute(current_user.id.value)
    return [BookWithCountsResponse.from_domain(b) for b in books]
```

### Routes already async that need await updates

These routes are already `async def` but currently call sync use cases. After Phase 5, they need `await`:
- Auth routes: `/auth/login`, `/auth/refresh`, `/auth/logout`
- User routes: `/users/register`, `/users/me` (GET and POST)
- AI routes: flashcard suggestions, quiz sessions, prereading generate, highlight upload, reading session upload

---

## Phase 7: Update Alembic for Async (Optional)

**Files changed:** `backend/alembic/env.py`

Alembic can run migrations with an async engine. This is optional — Alembic migrations are a one-time operation and can continue using sync mode since psycopg v3 supports both.

If desired:
```python
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations_online():
    connectable = create_async_engine(database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
```

**Recommendation:** Defer this. Alembic migrations don't benefit from async.

---

## Phase 8: Update Tests

**Files changed:** `backend/tests/conftest.py`, all test files

### Steps

1. Switch test engine to async:
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

   TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
   test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
   TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession)
   ```

2. Convert `db_session` fixture to async:
   ```python
   @pytest.fixture
   async def db_session() -> AsyncGenerator[AsyncSession, None]:
       async with test_engine.begin() as conn:
           await conn.run_sync(Base.metadata.create_all)
       async with TestSessionLocal() as session:
           # Create default user
           session.add(User(id=1, email="admin@test.com"))
           await session.commit()
           yield session
       async with test_engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
   ```

3. Switch from `TestClient` to `httpx.AsyncClient`:
   ```python
   from httpx import ASGITransport, AsyncClient

   @pytest.fixture
   async def client(db_session: AsyncSession, test_user: User) -> AsyncGenerator[AsyncClient, None]:
       async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
           yield db_session

       app.dependency_overrides[get_db] = override_get_db
       app.dependency_overrides[get_current_user] = override_get_current_user

       transport = ASGITransport(app=app)
       async with AsyncClient(transport=transport, base_url="http://test") as ac:
           yield ac

       app.dependency_overrides.clear()
   ```

4. Update all test methods: they're already configured with `asyncio_mode = "auto"` in pyproject.toml, so just change test functions to `async def` and `await` the client calls:
   ```python
   # BEFORE
   def test_get_books(client: TestClient):
       response = client.get("/api/v1/books/")

   # AFTER
   async def test_get_books(client: AsyncClient):
       response = await client.get("/api/v1/books/")
   ```

5. Update helper functions (`create_test_book`, `create_test_highlight`, etc.) to be async or use `run_sync` patterns.

---

## Phase 9: Update Main App Lifespan

**Files changed:** `backend/src/main.py`

The lifespan is already `async`. Update:
1. `dispose_engine()` — if the async engine's `dispose()` is async, await it
2. `_initialize_admin_password()` — this function uses a sync repo; either make it async or use `run_sync`

---

## Execution Order and Risk Mitigation

### Recommended execution order

1. **Phase 1** (dependencies) — low risk, no behavior change
2. **Phase 2** (database layer) — foundational change, breaks everything downstream
3. **Phase 3** (DI container) — small change, follows Phase 2
4. **Phase 4** (repositories) — large scope, mechanical conversion
5. **Phase 5** (use cases) — large scope, mechanical conversion
6. **Phase 6** (routes) — large scope, mechanical conversion
7. **Phase 8** (tests) — must be done alongside or after Phase 6
8. **Phase 9** (main app) — small cleanup
9. **Phase 7** (Alembic) — optional, defer

### Strategy: Big-bang vs. incremental

**Recommended: Big-bang migration.** The reason is that converting `database.py` to async immediately breaks all repositories, use cases, and routes. There's no clean way to have a sync `Session` and `AsyncSession` coexist in the same DI container without significant shim complexity (like maintaining parallel `get_db` / `get_async_db` dependencies).

An incremental approach would require:
- Maintaining both sync and async database sessions simultaneously
- Dual DI injection for sync/async repositories
- Gradual route-by-route conversion

This adds significant complexity for little benefit. Since the conversions are mechanical (`def` → `async def`, add `await`), a single focused migration pass is cleaner.

### Validation at each phase

After Phases 2-6 are complete:
```bash
cd backend && uv run pyright    # Type check
cd backend && uv run ruff check # Lint
cd backend && uv run pytest     # Run tests (after Phase 8)
```

---

## Gotchas and Edge Cases

### 1. Lazy loading breaks in async mode
SQLAlchemy async sessions prohibit implicit lazy loading. Any ORM relationship access that hasn't been eagerly loaded will raise `MissingGreenlet`. Audit all repository queries to ensure eager loading (`joinedload`, `selectinload`) covers all accessed relationships.

### 2. `session.add()` remains synchronous
Don't add `await` to `session.add()` — it's purely in-memory and doesn't hit the database.

### 3. `.unique()` still required with `joinedload`
The existing `.unique()` pattern for `joinedload` collections applies identically in async mode.

### 4. `psycopg` v3 dialect URL
The async-compatible URL for psycopg v3 is `postgresql+psycopg://...` (not `postgresql+asyncpg`). The same driver works in both modes.

### 5. `dependency-injector` and async
The `dependency-injector` library works fine with async — the container itself is synchronous (just wiring), and the injected objects can have async methods.

### 6. Infrastructure services that use repositories
Some infrastructure services (like `HighlightLabelResolver`, `AIService`) call repository methods. These also need async conversion if they call `await`-requiring repo methods.

### 7. `FileRepository` — likely no DB access
`FileRepository` handles file system operations, not database. Verify whether it needs async conversion (probably not, unless it does I/O that would benefit from `aiofiles`).

### 8. Test helper functions
`create_test_book()`, `create_test_highlight()`, etc. in `conftest.py` use sync `db_session.add()` / `db_session.commit()`. These must become async.

---

## File Change Summary

| Category | Files | Effort |
|---|---|---|
| Dependencies | 1 (`pyproject.toml`) | Small |
| Database layer | 1 (`database.py`) | Small |
| DI | 2 (`core.py`, `di.py`) | Small |
| Repositories | ~14 files | Medium (mechanical) |
| Use cases | ~50 files | Medium (mechanical) |
| Routes | ~15 router files | Medium (mechanical) |
| Infrastructure services | ~5 files | Small |
| Tests | `conftest.py` + ~20 test files | Medium |
| Main app | 1 (`main.py`) | Small |
| **Total** | **~110 files** | |
