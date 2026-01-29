# Crossbill Backend Architecture Guide

## Overview

The Crossbill backend is transitioning from a traditional layered architecture to a **Domain-Driven Design (DDD)** architecture with bounded contexts. This guide documents the current architecture, migration status, and best practices.

## Architecture Status

**Current State**: Hybrid (Migration in Progress)
- ✅ Reading context migrated to DDD
- ⏳ Library context partially migrated
- ⏳ Legacy services still exist alongside new DDD services

---

## Table of Contents

1. [Architecture Principles](#architecture-principles)
2. [Directory Structure](#directory-structure)
3. [Bounded Contexts](#bounded-contexts)
4. [Layer Responsibilities](#layer-responsibilities)
5. [Migration Guide](#migration-guide)
6. [Code Examples](#code-examples)
7. [Testing Strategy](#testing-strategy)

---

## Architecture Principles

### 1. Domain-Driven Design (DDD)

We follow DDD principles to organize code around business domains:

- **Bounded Contexts**: Separate domains (Reading, Library) with clear boundaries
- **Ubiquitous Language**: Domain concepts reflect business terminology
- **Domain Entities**: Rich models with business logic
- **Value Objects**: Immutable objects representing domain concepts
- **Repositories**: Abstract data persistence

### 2. Clean Architecture

Layers depend inward (Domain → Application → Infrastructure → API):

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← Handles HTTP, DTOs (Pydantic schemas)
├─────────────────────────────────────┤
│     Application Layer (Services)    │  ← Use cases, orchestration
├─────────────────────────────────────┤
│    Infrastructure Layer (Repos)     │  ← Persistence, external services
├─────────────────────────────────────┤
│       Domain Layer (Entities)       │  ← Business logic, rules
└─────────────────────────────────────┘
```

**Dependency Rule**: Outer layers depend on inner layers, never the reverse.

### 3. Separation of Concerns

- **Domain Layer**: Business logic only, no infrastructure knowledge
- **Application Layer**: Orchestrates workflows, converts between primitives and value objects
- **Infrastructure Layer**: Database, mappers, external services
- **API Layer**: HTTP concerns, schema validation, DTO conversion

---

## Directory Structure

```
backend/
├── src/
│   ├── domain/                      # Domain Layer (Business Logic)
│   │   ├── common/                  # Shared domain concepts
│   │   │   ├── entity.py           # Base entity class
│   │   │   ├── aggregate_root.py   # Base aggregate root
│   │   │   ├── exceptions.py       # Domain exceptions
│   │   │   └── value_objects/      # Shared value objects
│   │   │       └── ids.py          # ID value objects (UserId, BookId, etc.)
│   │   ├── reading/                 # Reading bounded context ✅ Migrated
│   │   │   ├── entities/
│   │   │   │   └── highlight.py    # Highlight aggregate root
│   │   │   └── exceptions.py       # Reading-specific exceptions
│   │   └── library/                 # Library bounded context ⏳ Partial
│   │       ├── entities/
│   │       │   ├── book.py         # Book aggregate root
│   │       │   └── chapter.py      # Chapter entity
│   │       └── exceptions.py
│   │
│   ├── application/                 # Application Layer (Use Cases)
│   │   └── reading/
│   │       └── services/
│   │           ├── highlight_upload_service.py          ✅ DDD
│   │           ├── search_highlights_service.py         ✅ DDD
│   │           ├── get_recently_viewed_books_service.py ✅ DDD
│   │           └── update_highlight_note_service.py     ✅ DDD
│   │
│   ├── infrastructure/              # Infrastructure Layer (Persistence)
│   │   ├── reading/
│   │   │   ├── repositories/
│   │   │   │   └── highlight_repository.py  # DDD repository
│   │   │   └── mappers/
│   │   │       └── highlight_mapper.py      # ORM ↔ Domain conversion
│   │   └── library/
│   │       ├── repositories/
│   │       │   ├── book_repository.py       # DDD repository
│   │       │   └── chapter_repository.py
│   │       └── mappers/
│   │           ├── book_mapper.py
│   │           └── chapter_mapper.py
│   │
│   ├── routers/                     # API Layer (HTTP Routes)
│   │   ├── highlights.py            # Highlight endpoints
│   │   ├── books.py                 # Book endpoints
│   │   └── ...
│   │
│   ├── services/                    # Legacy Services ⚠️ Being phased out
│   │   ├── highlight_service.py     # Partially migrated
│   │   ├── book_service.py
│   │   └── ...
│   │
│   ├── repositories/                # Legacy Repositories ⚠️ Being phased out
│   │   ├── highlight_repository.py
│   │   ├── book_repository.py
│   │   └── ...
│   │
│   ├── schemas/                     # Pydantic Schemas (DTOs)
│   │   ├── highlight_schemas.py
│   │   ├── book_schemas.py
│   │   └── ...
│   │
│   └── models.py                    # SQLAlchemy ORM Models
```

---

## Bounded Contexts

### Reading Context ✅ Fully Migrated

**Purpose**: Manage user highlights, notes, and annotations

**Domain Entities**:
- `Highlight` - Text highlights from e-readers with optional notes
- Related value objects: `HighlightId`, `ContentHash`, `XPointRange`

**Use Cases** (Application Services):
- Upload highlights from KOReader
- Search highlights (full-text)
- Update highlight notes
- Get recently viewed books (cross-context)

**Repositories**:
- `HighlightRepository` - Persistence for Highlight aggregate

### Library Context ⏳ Partially Migrated

**Purpose**: Manage books, chapters, and book metadata

**Domain Entities**:
- `Book` - Book metadata and information
- `Chapter` - Book chapters (table of contents)

**Repositories**:
- `BookRepository` - Book persistence
- `ChapterRepository` - Chapter persistence

---

## Layer Responsibilities

### 1. Domain Layer (`src/domain/`)

**Purpose**: Core business logic and rules

**Contains**:
- **Entities**: Objects with identity (e.g., `Highlight`, `Book`)
- **Value Objects**: Immutable objects (e.g., `UserId`, `BookId`, `ContentHash`)
- **Aggregate Roots**: Entities that control consistency boundaries
- **Domain Exceptions**: Business rule violations

**Rules**:
- ✅ No dependencies on outer layers
- ✅ No database, HTTP, or framework code
- ✅ Pure Python business logic
- ✅ Testable without infrastructure

**Example Entity**:
```python
@dataclass
class Highlight(AggregateRoot[HighlightId]):
    """Highlight aggregate root."""

    id: HighlightId
    user_id: UserId
    book_id: BookId
    text: str
    content_hash: ContentHash
    note: str | None = None
    datetime: str = ""  # KOReader datetime
    created_at: datetime
    updated_at: datetime

    # Command method - encapsulates business logic
    def update_note(self, note: str | None) -> None:
        """Update the note attached to this highlight."""
        self.note = note.strip() if note else None
```

### 2. Application Layer (`src/application/`)

**Purpose**: Use cases and application workflows

**Contains**:
- **Application Services**: Orchestrate domain operations
- **Use case implementations**: Business workflows

**Responsibilities**:
- Convert primitives (int, str) to value objects
- Orchestrate repository and domain operations
- Transaction management (service boundary)
- Return domain entities or primitives

**Rules**:
- ✅ Use domain entities and value objects
- ✅ No Pydantic schemas
- ✅ No HTTP/routing logic
- ✅ Delegate to repositories for persistence

**Example Service**:
```python
class UpdateHighlightNoteService:
    """Application service for updating highlight notes."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.highlight_repository = HighlightRepository(db)

    def update_note(
        self, highlight_id: int, user_id: int, note: str | None
    ) -> Highlight | None:
        """Update a highlight's note field."""
        # Convert primitives to value objects
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Load aggregate
        highlight = self.highlight_repository.find_by_id(
            highlight_id_vo, user_id_vo
        )

        if highlight is None:
            return None

        # Use domain method (business logic in entity)
        highlight.update_note(note)

        # Persist changes
        updated_highlight = self.highlight_repository.save(highlight)

        return updated_highlight
```

### 3. Infrastructure Layer (`src/infrastructure/`)

**Purpose**: Technical implementation details

**Contains**:
- **Repositories**: Implement data persistence
- **Mappers**: Convert between ORM models and domain entities
- **External service adapters**

**Responsibilities**:
- Database queries (SQLAlchemy)
- ORM ↔ Domain entity conversion
- External API calls
- File system operations

**Rules**:
- ✅ Depends on domain layer
- ✅ Returns domain entities (not ORM models)
- ✅ Uses mappers for conversion
- ✅ Hides persistence details from domain

**Example Repository**:
```python
class HighlightRepository:
    """Repository for Highlight persistence (domain-centric)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = HighlightMapper()

    def find_by_id(
        self, highlight_id: HighlightId, user_id: UserId
    ) -> Highlight | None:
        """Load highlight by ID."""
        stmt = (
            select(HighlightORM)
            .where(HighlightORM.id == highlight_id.value)
            .where(HighlightORM.user_id == user_id.value)
        )
        orm_model = self.db.execute(stmt).scalar_one_or_none()

        if not orm_model:
            return None

        # Convert ORM → Domain entity
        return self.mapper.to_domain(orm_model)

    def save(self, highlight: Highlight) -> Highlight:
        """Persist highlight to database."""
        if highlight.id.value == 0:
            # Create new
            orm_model = self.mapper.to_orm(highlight)
            self.db.add(orm_model)
            self.db.flush()
            return self.mapper.to_domain(orm_model)

        # Update existing
        stmt = select(HighlightORM).where(
            HighlightORM.id == highlight.id.value
        )
        existing_orm = self.db.execute(stmt).scalar_one()
        self.mapper.to_orm(highlight, existing_orm)
        self.db.flush()

        return self.mapper.to_domain(existing_orm)
```

**Example Mapper**:
```python
class HighlightMapper:
    """Mapper for Highlight ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: HighlightORM) -> Highlight:
        """Convert ORM model to domain entity."""
        return Highlight.create_with_id(
            id=HighlightId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            book_id=BookId(orm_model.book_id),
            text=orm_model.text,
            content_hash=ContentHash(orm_model.content_hash),
            datetime_str=orm_model.datetime,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            # ... other fields
        )

    def to_orm(
        self, domain_entity: Highlight, orm_model: HighlightORM | None = None
    ) -> HighlightORM:
        """Convert domain entity to ORM model."""
        # Implementation...
```

### 4. API Layer (`src/routers/`)

**Purpose**: HTTP interface and request/response handling

**Contains**:
- **FastAPI routers**: HTTP endpoints
- **Request validation**: Pydantic schemas
- **Response formatting**: DTO conversion

**Responsibilities**:
- Handle HTTP requests/responses
- Validate input (Pydantic)
- Convert domain entities → DTOs (schemas)
- Error handling and HTTP status codes
- Authentication/authorization

**Rules**:
- ✅ Use application services for business logic
- ✅ Convert between DTOs and domain concepts
- ✅ No business logic in routes
- ✅ Handle transactions (commit/rollback)

**Example Route**:
```python
@router.post("/{highlight_id}/note")
def update_highlight_note(
    highlight_id: int,
    request: schemas.HighlightNoteUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightNoteUpdateResponse:
    """Update the note field of a highlight."""
    try:
        # Use application service
        service = UpdateHighlightNoteService(db)
        highlight = service.update_note(
            highlight_id, current_user.id, request.note
        )

        if highlight is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Highlight with id {highlight_id} not found",
            )

        # Commit transaction
        db.commit()

        # Convert domain entity → DTO (schema)
        # (Fetch ORM for relationships not yet in domain)
        from src.repositories.highlight_repository import (
            HighlightRepository as LegacyRepo
        )
        legacy_repo = LegacyRepo(db)
        highlight_orm = legacy_repo.get_by_id(highlight_id, current_user.id)

        highlight_schema = schemas.Highlight.model_validate(highlight_orm)

        return schemas.HighlightNoteUpdateResponse(
            success=True,
            message="Note updated successfully",
            highlight=highlight_schema,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update highlight note: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred.",
        ) from e
```

---

## Migration Guide

### Migration Status

#### ✅ Completed Migrations

| Feature | Legacy Service | New Service | Status |
|---------|---------------|-------------|--------|
| Upload highlights | `HighlightService.upload_highlights()` | `HighlightUploadService` | ✅ Migrated |
| Search highlights | `HighlightService.search_highlights()` | `SearchHighlightsService` | ✅ Migrated |
| Update note | `HighlightService.update_highlight_note()` | `UpdateHighlightNoteService` | ✅ Migrated |
| Recently viewed books | `HighlightService.get_recently_viewed_books()` | `GetRecentlyViewedBooksService` | ✅ Migrated |

#### ⏳ Pending Migrations

| Feature | Legacy Service | Status |
|---------|---------------|--------|
| Get books with counts | `HighlightService.get_books_with_counts()` | ⏳ Not yet migrated |
| Book CRUD operations | `BookService` | ⏳ Not yet migrated |
| Chapter management | `ChapterRepository` | ⏳ Not yet migrated |
| Tags | `TagService` | ⏳ Not yet migrated |
| Flashcards | `FlashcardService` | ⏳ Not yet migrated |

### How to Migrate a Feature

Follow this step-by-step process to migrate legacy code to DDD:

#### Step 1: Identify the Domain

Determine which bounded context the feature belongs to:
- Reading: Highlights, notes, annotations, reading sessions
- Library: Books, chapters, metadata, tags

#### Step 2: Create/Update Domain Entities

Add domain entities with business logic in `src/domain/{context}/entities/`.

**Before (ORM model with logic scattered)**:
```python
# In repository or service
def update_note(highlight_id, note):
    highlight = db.query(Highlight).get(highlight_id)
    highlight.note = note.strip() if note else None
    db.commit()
```

**After (Domain entity with encapsulated logic)**:
```python
# In domain/reading/entities/highlight.py
@dataclass
class Highlight(AggregateRoot[HighlightId]):
    # ... fields ...

    def update_note(self, note: str | None) -> None:
        """Update note - business logic here."""
        self.note = note.strip() if note else None
```

#### Step 3: Create Repository (Infrastructure)

Implement repository in `src/infrastructure/{context}/repositories/`.

**Requirements**:
- Return domain entities (not ORM models)
- Use mapper for ORM ↔ Domain conversion
- Generic methods: `find_by_id()`, `save()`, `bulk_save()`

**Template**:
```python
class EntityRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = EntityMapper()

    def find_by_id(self, id: EntityId, user_id: UserId) -> Entity | None:
        stmt = select(EntityORM).where(...)
        orm_model = self.db.execute(stmt).scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    def save(self, entity: Entity) -> Entity:
        # Create or update logic
        pass
```

#### Step 4: Create Application Service

Create service in `src/application/{context}/services/`.

**Requirements**:
- Accept primitives (int, str) as parameters
- Convert to value objects internally
- Use domain entities
- Return domain entities or primitives
- No Pydantic schemas

**Template**:
```python
class DoSomethingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = EntityRepository(db)

    def do_something(self, entity_id: int, user_id: int, ...) -> Entity | None:
        # Convert primitives to value objects
        entity_id_vo = EntityId(entity_id)
        user_id_vo = UserId(user_id)

        # Load entity
        entity = self.repository.find_by_id(entity_id_vo, user_id_vo)

        if entity is None:
            return None

        # Use domain method
        entity.do_something(...)

        # Persist
        return self.repository.save(entity)
```

#### Step 5: Update API Route

Update route in `src/routers/` to use new service.

**Requirements**:
- Use application service
- Convert domain entities → Pydantic schemas
- Handle transactions (commit/rollback)
- HTTP error handling

**Before**:
```python
@router.post("/endpoint")
def endpoint(db: Session, ...):
    service = LegacyService(db)
    return service.do_something(...)  # Returns schema directly
```

**After**:
```python
@router.post("/endpoint")
def endpoint(db: Session, ...):
    try:
        # Use application service
        service = DoSomethingService(db)
        entity = service.do_something(...)

        if entity is None:
            raise HTTPException(status_code=404, ...)

        # Commit transaction
        db.commit()

        # Convert domain → schema
        schema = schemas.Entity.model_validate(entity)

        return schemas.Response(success=True, data=schema)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, ...)
```

#### Step 6: Remove Legacy Code

After verifying the migration:
1. Remove method from legacy service
2. Update imports throughout codebase
3. Verify tests pass
4. Keep backwards compatibility aliases if needed

---

## Code Examples

### Example 1: Simple Use Case (Update Note)

**Domain Entity** (`src/domain/reading/entities/highlight.py`):
```python
def update_note(self, note: str | None) -> None:
    """Update the note attached to this highlight."""
    self.note = note.strip() if note else None
```

**Application Service** (`src/application/reading/services/update_highlight_note_service.py`):
```python
class UpdateHighlightNoteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.highlight_repository = HighlightRepository(db)

    def update_note(
        self, highlight_id: int, user_id: int, note: str | None
    ) -> Highlight | None:
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        highlight = self.highlight_repository.find_by_id(
            highlight_id_vo, user_id_vo
        )

        if highlight is None:
            return None

        highlight.update_note(note)  # Domain method

        return self.highlight_repository.save(highlight)
```

**API Route** (`src/routers/highlights.py`):
```python
@router.post("/{highlight_id}/note")
def update_highlight_note(
    highlight_id: int,
    request: schemas.HighlightNoteUpdate,
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
) -> schemas.HighlightNoteUpdateResponse:
    service = UpdateHighlightNoteService(db)
    highlight = service.update_note(highlight_id, current_user.id, request.note)

    if highlight is None:
        raise HTTPException(status_code=404, ...)

    db.commit()

    # Convert to schema (simplified)
    highlight_schema = schemas.Highlight.model_validate(highlight)

    return schemas.HighlightNoteUpdateResponse(
        success=True,
        message="Note updated successfully",
        highlight=highlight_schema,
    )
```

### Example 2: Complex Query (Search with Relations)

**Repository** (`src/infrastructure/reading/repositories/highlight_repository.py`):
```python
def search(
    self,
    search_text: str,
    user_id: UserId,
    book_id: BookId | None = None,
    limit: int = 100,
) -> list[tuple[Highlight, Book, Chapter | None, HighlightORM]]:
    """Search highlights with related entities."""
    is_postgresql = self.db.bind.dialect.name == "postgresql"

    stmt = (
        select(HighlightORM)
        .options(
            joinedload(HighlightORM.book),
            joinedload(HighlightORM.chapter),
            joinedload(HighlightORM.highlight_tags),
        )
        .where(
            HighlightORM.user_id == user_id.value,
            HighlightORM.deleted_at.is_(None),
        )
    )

    if is_postgresql:
        search_query = func.plainto_tsquery("english", search_text)
        stmt = stmt.where(
            HighlightORM.text_search_vector.op("@@")(search_query)
        )
    else:
        stmt = stmt.where(HighlightORM.text.ilike(f"%{search_text}%"))

    if book_id is not None:
        stmt = stmt.where(HighlightORM.book_id == book_id.value)

    stmt = stmt.limit(limit)

    results = self.db.execute(stmt).scalars().all()

    return [
        (
            self.mapper.to_domain(h_orm),
            self.book_mapper.to_domain(h_orm.book),
            self.chapter_mapper.to_domain(h_orm.chapter) if h_orm.chapter else None,
            h_orm,  # Include ORM for tags relationship
        )
        for h_orm in results
    ]
```

**Application Service**:
```python
class SearchHighlightsService:
    def search(
        self,
        search_text: str,
        user_id: int,
        book_id: int | None = None,
        limit: int = 100,
    ) -> list[tuple[Highlight, Book, Chapter | None, HighlightORM]]:
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id) if book_id is not None else None

        return self.highlight_repository.search(
            search_text=search_text,
            user_id=user_id_vo,
            book_id=book_id_vo,
            limit=limit,
        )
```

**API Route**:
```python
@router.get("/search")
def search_highlights(
    db: DatabaseSession,
    current_user: Annotated[User, Depends(get_current_user)],
    search_text: str = Query(...),
    book_id: int | None = Query(None),
    limit: int = Query(100),
) -> schemas.HighlightSearchResponse:
    service = SearchHighlightsService(db)
    results = service.search(search_text, current_user.id, book_id, limit)

    # Convert domain entities to schemas
    search_results = [
        schemas.HighlightSearchResult(
            id=highlight.id.value,
            text=highlight.text,
            page=highlight.page,
            note=highlight.note,
            datetime=highlight.datetime,
            book_id=book.id.value,
            book_title=book.title,
            book_author=book.author,
            chapter_id=chapter.id.value if chapter else None,
            chapter_name=chapter.name if chapter else None,
            chapter_number=chapter.chapter_number if chapter else None,
            highlight_tags=[
                schemas.HighlightTagInBook.model_validate(tag)
                for tag in highlight_orm.highlight_tags
            ],
            created_at=highlight.created_at,
            updated_at=highlight.updated_at,
        )
        for highlight, book, chapter, highlight_orm in results
    ]

    return schemas.HighlightSearchResponse(
        highlights=search_results,
        total=len(search_results)
    )
```

---

## Testing Strategy

### Unit Tests (Domain Layer)

Test domain entities and value objects in isolation:

```python
def test_highlight_update_note():
    # Arrange
    highlight = Highlight.create(
        user_id=UserId(1),
        book_id=BookId(1),
        text="Sample text",
    )

    # Act
    highlight.update_note("New note")

    # Assert
    assert highlight.note == "New note"

def test_highlight_update_note_strips_whitespace():
    highlight = Highlight.create(...)
    highlight.update_note("  Note with spaces  ")
    assert highlight.note == "Note with spaces"
```

### Integration Tests (Repository Layer)

Test repositories with real database:

```python
def test_highlight_repository_save_creates_new(db_session):
    # Arrange
    repository = HighlightRepository(db_session)
    highlight = Highlight.create(...)

    # Act
    saved = repository.save(highlight)

    # Assert
    assert saved.id.value > 0

    # Verify in database
    found = repository.find_by_id(saved.id, saved.user_id)
    assert found is not None
    assert found.text == highlight.text
```

### API Tests (Route Layer)

Test HTTP endpoints with TestClient:

```python
def test_update_highlight_note_success(client, auth_headers):
    # Create highlight
    highlight_id = create_test_highlight()

    # Update note
    response = client.post(
        f"/highlights/{highlight_id}/note",
        headers=auth_headers,
        json={"note": "Updated note"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["highlight"]["note"] == "Updated note"
```

---

## Best Practices

### 1. Domain Entities

✅ **DO**:
- Keep entities focused on business logic
- Use command methods (verbs) for state changes
- Use query methods (predicates) for queries
- Make entities self-validating (in `__post_init__`)
- Use factory methods (`create()`, `create_with_id()`)

❌ **DON'T**:
- Put database queries in entities
- Reference ORM models
- Use Pydantic schemas in entities
- Add HTTP/API concerns

### 2. Value Objects

✅ **DO**:
- Make immutable (frozen dataclasses)
- Validate in constructor
- Provide meaningful methods
- Use for domain concepts (UserId, Email, etc.)

❌ **DON'T**:
- Make mutable
- Use primitives where value objects make sense

### 3. Repositories

✅ **DO**:
- Return domain entities
- Use mappers for conversion
- Keep methods generic (find, save, delete)
- Hide persistence details

❌ **DON'T**:
- Return ORM models (except temporarily during migration)
- Put business logic in repositories
- Return Pydantic schemas

### 4. Application Services

✅ **DO**:
- One service per use case
- Accept primitives, convert to value objects
- Return domain entities or primitives
- Orchestrate workflows

❌ **DON'T**:
- Put business logic here (belongs in domain)
- Return Pydantic schemas
- Handle HTTP concerns

### 5. API Routes

✅ **DO**:
- Use application services
- Convert domain → DTOs
- Handle transactions
- Provide good error messages

❌ **DON'T**:
- Put business logic in routes
- Access repositories directly
- Bypass application services

---

## Transitional Patterns

### Working with Legacy Code

During migration, you may need to:

**Use Legacy Repositories for Relationships**:
```python
# In route, after getting domain entity
legacy_repo = LegacyHighlightRepository(db)
highlight_orm = legacy_repo.get_by_id(highlight_id, user_id)

# Access ORM relationships not yet in domain
tags = highlight_orm.highlight_tags
flashcards = highlight_orm.flashcards
```

**Return ORM with Domain Entities** (temporary):
```python
# Repository returns both for accessing relationships
def find_with_relations(self, id: EntityId) -> tuple[Entity, EntityORM]:
    orm = self.db.query(EntityORM).get(id.value)
    return self.mapper.to_domain(orm), orm
```

**Backwards Compatibility Aliases**:
```python
# Keep old import working
HighlightUploadService = HighlightService
```

---

## Common Questions

### Q: Why return ORM models with domain entities?

**A**: During migration, some relationships (like `highlight_tags`) haven't been modeled in the domain yet. Returning the ORM model alongside the domain entity lets us access these relationships temporarily. Eventually, these will be properly modeled in the domain.

### Q: Should I add `updated_at` to domain entities?

**A**: Yes, if the API layer needs it for schemas. Domain entities should have all fields needed by the application, even if they're infrastructure concerns like timestamps.

### Q: When to use value objects vs primitives?

**A**: Use value objects for domain concepts with validation or behavior (UserId, Email, ContentHash). Use primitives for simple data (strings, numbers) without domain meaning.

### Q: How to handle transactions?

**A**: Commit/rollback in the API layer (routes). Application services use `flush()` but don't commit. This gives routes control over transaction boundaries.

### Q: What about relationships between aggregates?

**A**: Reference by ID (value object), not by object reference. For example, Highlight references Book via `BookId`, not by holding a `Book` instance.

---

## Troubleshooting

### Import Errors

**Problem**: `ImportError: cannot import name 'SomeService'`

**Solution**: Check the import path matches the new structure:
```python
# Old
from src.services.highlight_service import HighlightService

# New
from src.application.reading.services.search_highlights_service import (
    SearchHighlightsService
)
```

### Type Errors with Value Objects

**Problem**: `Expected int, got UserId`

**Solution**: Extract the value: `user_id.value`

### ORM Relationships Not Loaded

**Problem**: `AttributeError: 'Highlight' object has no attribute 'book'`

**Solution**: Use `joinedload()` or `selectinload()` in repository query:
```python
stmt = select(HighlightORM).options(
    joinedload(HighlightORM.book),
    joinedload(HighlightORM.chapter),
)
```

---

## Future Improvements

### Short Term
- [ ] Migrate remaining services to DDD
- [ ] Add tags to domain entities (remove ORM dependency)
- [ ] Improve mapper testing
- [ ] Document domain events

### Long Term
- [ ] Implement CQRS (separate read/write models)
- [ ] Add domain events for cross-context communication
- [ ] Extract contexts into separate modules
- [ ] Consider microservices architecture

---

## References

- [Domain-Driven Design (Eric Evans)](https://www.domainlanguage.com/ddd/)
- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Implementing DDD (Vaughn Vernon)](https://vaughnvernon.com/)

---

**Last Updated**: 2025-01-29
**Status**: Living document - updated as architecture evolves
