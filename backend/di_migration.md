# Dependency Injection Migration Guide

This guide describes how to migrate application services to use cases with dependency injection in our DDD hexagonal architecture.

## Overview

Services in `backend/src/application/identity/services/` should be migrated to `backend/src/application/identity/use_cases/` to use dependency injection with repository protocols instead of direct dependencies.

## Migration Steps

### 1. Move and Rename Service File

**Before:**

```
backend/src/application/identity/services/highlight_tag_service.py
class HighlightTagService
```

**After:**

```
backend/src/application/identity/use_cases/highlight_tag_use_case.py
class HighlightTagUseCase
```

- Move file from `services/` to `use_cases/` directory
- Rename file to use `_use_case.py` suffix instead of `_service.py`
- Rename class to use `UseCase` suffix instead of `Service`

### 2. Create Repository Protocols

Before changing the constructor, ensure all required repository protocols exist.

**Protocol locations:**

- `backend/src/application/reading/protocols/` - for reading domain repositories
- `backend/src/application/identity/protocols/` - for identity domain repositories

**Protocol example** (`backend/src/application/reading/protocols/highlight_repository.py`):

```python
from typing import Protocol

from src.domain.common.value_objects import BookId, HighlightId, UserId

class HighlightRepositoryProtocol(Protocol):
    def soft_delete_by_ids(
        self,
        highlight_ids: list[HighlightId],
        user_id: UserId,
        book_id: BookId,
    ) -> int:
        ...

    def find_by_id(self, highlight_id: HighlightId, user_id: UserId) -> Highlight | None:
        ...
```

Create new protocols as needed for repositories used by the service. Use existing repositories in the infrastructure layer as basis for the protocol interface.

### 3. Update Use Case Constructor

Change the constructor to accept repository protocols instead of db session or concrete repository instances.

**Before (Service pattern):**

```python
class HighlightTagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.highlight_repository = HighlightRepository(db)
        self.tag_repository = TagRepository(db)
```

**After (Use Case with DI):**

```python
class HighlightTagUseCase:
    def __init__(
        self,
        highlight_repository: HighlightRepositoryProtocol,
        tag_repository: TagRepositoryProtocol,
    ) -> None:
        self.highlight_repository = highlight_repository
        self.tag_repository = tag_repository
```

**Key changes:**

- Remove `db: Session` parameter
- Accept protocol types instead of concrete repository classes
- Store protocol instances directly (no instantiation)
- Remove any direct database access

### 4. Reference Example

See `backend/src/application/identity/use_cases/highlight_delete_use_case.py` for a complete example:

```python
from src.application.reading.protocols.book_repository import BookRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects import BookId, HighlightId, UserId

class HighlightDeleteUseCase:
    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository

    def delete_highlights(self, book_id: int, highlight_ids: list[int], user_id: int) -> int:
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)
        highlight_ids_vo = [HighlightId(hid) for hid in highlight_ids]

        # Verify book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Perform operation using repository
        return self.highlight_repository.soft_delete_by_ids(
            highlight_ids=highlight_ids_vo,
            user_id=user_id_vo,
            book_id=book_id_vo,
        )
```

### 5. Register in DI Container

Add the use case to `backend/src/core.py`:

```python
from src.application.reading.use_cases.highlight_tag_use_case import HighlightTagUseCase

class Container(containers.DeclarativeContainer):
    # ... existing code ...

    # Repositories
    highlight_repository = providers.Factory(HighlightRepository, db=db)
    tag_repository = providers.Factory(TagRepository, db=db)

    # Application use cases
    highlight_tag_use_case = providers.Factory(
        HighlightTagUseCase,
        highlight_repository=highlight_repository,
        tag_repository=tag_repository,
    )
```

**Steps:**

1. Import the new use case class
2. Ensure all required repositories are registered
3. Add use case as a `providers.Factory`
4. Wire dependencies using named parameters

### 6. Update Routers to Use DI

Update router endpoints in `backend/src/infrastructure/identity/routers/` to inject the use case.

**Before:**

```python
@router.post("/tags")
def create_tag(
    request: TagRequest,
    db: Session = Depends(get_db),
) -> TagResponse:
    service = HighlightTagService(db)
    tag = service.create_tag(request.name)
    return TagResponse.from_entity(tag)
```

**After:**

```python
from src.application.reading.use_cases.highlight_tag_use_case import HighlightTagUseCase
from src.core import container
from src.infrastructure.common.di import inject_use_case

@router.post("/tags")
def create_tag(
    request: TagRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: HighlightTagUseCase = Depends(inject_use_case(container.highlight_tag_use_case)),
) -> TagResponse:
    tag = use_case.create_tag(request.name, current_user.id.value)
    return TagResponse.from_entity(tag)
```

**Key changes:**

1. Import use case class, `container`, and `inject_use_case`
2. Remove `db: Session` dependency
3. Add `use_case` parameter with `Depends(inject_use_case(container.use_case_name))`
4. Replace service instantiation with use case parameter
5. Call methods on `use_case` instead of `service`

**Reference example:** `backend/src/infrastructure/reading/routers/bookmarks.py`

### 7. Update Imports in Router

Ensure the router imports from the correct locations:

```python
from src.application.reading.use_cases.highlight_tag_use_case import HighlightTagUseCase
from src.core import container
from src.infrastructure.common.di import inject_use_case
```

## Checklist

For each service migration:

- [ ] Create required repository protocols if they don't exist
- [ ] Move service file to `use_cases/` directory
- [ ] Rename file and class to use `use_case` suffix
- [ ] Update constructor to accept repository protocols
- [ ] Remove all direct database access (`db.query()`, etc.)
- [ ] Register use case in `backend/src/core.py`
- [ ] Update all router endpoints that use the service
- [ ] Test the migrated endpoints
- [ ] Remove old service file from `services/` directory

## Benefits of This Architecture

1. **Testability**: Use cases can be tested with mock protocols
2. **Decoupling**: Application layer doesn't depend on infrastructure
3. **Flexibility**: Easy to swap repository implementations
4. **Clear boundaries**: Respects hexagonal architecture principles
5. **Dependency management**: Centralized in DI container

## Common Patterns

### Working with Value Objects

Use cases should accept primitive types and convert to value objects:

```python
def create_tag(self, name: str, user_id: int) -> Tag:
    user_id_vo = UserId(user_id)
    # ... use value object
```

### Error Handling

Use cases should raise domain exceptions:

```python
from src.exceptions import BookNotFoundError

if not book:
    raise BookNotFoundError(book_id)
```

### Repository Protocol Methods

Protocol methods should use value objects:

```python
class BookRepositoryProtocol(Protocol):
    def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None:
        ...
```

## Completed Migrations

### Identity Module
- ✅ UserProfileService → UpdateUserUseCase
- ✅ AuthenticationService → AuthenticationUseCase
- ✅ UserRegistrationService → RegisterUserUseCase

All identity services have been successfully migrated to use cases with dependency injection following the DDD hexagonal architecture pattern.

### Reading Module
- ✅ Various reading services migrated to use cases (see git history)

### Library Module
- ✅ Various library services migrated to use cases (see git history)

### Learning Module
- ✅ Flashcard services migrated to use cases (see git history)

## Files to Migrate

Current services in `backend/src/application/identity/services/`: None (all migrated)
