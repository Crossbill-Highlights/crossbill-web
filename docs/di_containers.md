# DDD Architecture with Dependency Injection Using Python Protocols

## Goal
Introduce proper decoupling between domain, application, and infrastructure layers using:
- Python Protocols (PEP 544) for port interfaces without separate interface files
- dependency_injector library for managing dependencies
- Move business validation logic from application layer to domain layer

## Architecture Principles

### Layer Dependencies (Hexagonal/Clean Architecture)
```
┌─────────────────────────────────────────┐
│         Infrastructure Layer            │
│  (Repositories, Mappers, Routers, DI)   │
│            depends on ↓                  │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         Application Layer                │
│    (Use Case Services, Protocols)        │
│            depends on ↓                  │
└─────────────────────────────────────────┐
              ↓
┌─────────────────────────────────────────┐
│           Domain Layer                   │
│  (Entities, Value Objects, Services)     │
│         depends on nothing               │
└─────────────────────────────────────────┘
```

**Key Rules:**
- Domain layer: Pure business logic, no framework dependencies
- Application layer: Defines Protocols (ports), orchestrates use cases
- Infrastructure layer: Implements Protocols (adapters), provides DI container
- Pragmatic: Domain can import from application layer abstractions (Protocols)

## Current Issues

### 1. Business Logic in Wrong Layer
`BookmarkService` (application) contains validation that should be in domain:
- Checking if highlight belongs to book
- Idempotency checks
- Cross-aggregate validation

### 2. No Abstraction Between Layers
Repositories are concrete classes directly instantiated in services:
```python
class BookmarkService:
    def __init__(self, db: Session):
        self.bookmark_repository = BookmarkRepository(db)  # Concrete class
        self.book_repository = BookRepository(db)          # Concrete class
```

### 3. DI Container Too Simple
Current container only manages one service with direct database dependency.

## Implementation Strategy

### Phase 1: Define Repository Protocols in Application Layer

**Why application layer?**
- Protocols define the needs of use cases (application concerns)
- Infrastructure provides implementations
- Domain services can import these Protocols when needed

**File:** `backend/src/application/reading/protocols.py` (NEW)

```python
from typing import Protocol
from src.domain.reading.entities.bookmark import Bookmark
from src.domain.common.value_objects.ids import BookmarkId, BookId, HighlightId, UserId

class BookmarkRepositoryProtocol(Protocol):
    """Port for bookmark persistence operations."""

    def find_by_id(self, bookmark_id: BookmarkId, user_id: UserId) -> Bookmark | None: ...
    def find_by_book_and_highlight(
        self, book_id: BookId, highlight_id: HighlightId, user_id: UserId
    ) -> Bookmark | None: ...
    def find_by_book(self, book_id: BookId, user_id: UserId) -> list[Bookmark]: ...
    def save(self, bookmark: Bookmark) -> Bookmark: ...
    def delete(self, bookmark_id: BookmarkId, user_id: UserId) -> bool: ...

class HighlightRepositoryProtocol(Protocol):
    """Port for highlight persistence operations."""

    def find_by_id(self, highlight_id: HighlightId, user_id: UserId) -> Highlight | None: ...
    # ... other methods

class BookRepositoryProtocol(Protocol):
    """Port for book persistence operations."""

    def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None: ...
    # ... other methods
```

**Benefits:**
- Single file per bounded context (e.g., all reading protocols together)
- No inheritance required - existing repositories already match these signatures
- Type-safe with mypy
- Easy to mock for testing

### Phase 2: Move Validation Logic to Domain Layer

Create a domain service for bookmark-related business rules:

**File:** `backend/src/domain/reading/services/bookmark_service.py` (NEW)

```python
from dataclasses import dataclass
from src.domain.reading.entities.bookmark import Bookmark
from src.domain.common.value_objects.ids import BookmarkId, BookId, HighlightId, UserId
from src.exceptions import ValidationError

@dataclass
class BookmarkDomainService:
    """Domain service for bookmark business logic."""

    @staticmethod
    def validate_bookmark_creation(
        book_id: BookId,
        highlight_id: HighlightId,
        book_owner: UserId,
        highlight_book_id: BookId,
        highlight_owner: UserId,
    ) -> None:
        """
        Validates business rules for bookmark creation.

        Rules:
        - Highlight must belong to the specified book
        - User must own both the book and highlight

        Raises:
            ValidationError: If validation fails
        """
        if highlight_book_id != book_id:
            raise ValidationError(
                f"Highlight {highlight_id.value} does not belong to book {book_id.value}"
            )

        # Additional validations...

    @staticmethod
    def is_duplicate_bookmark(existing_bookmark: Bookmark | None) -> bool:
        """Check if bookmark already exists (idempotency)."""
        return existing_bookmark is not None
```

**Key Points:**
- Stateless domain service (no dependencies)
- Contains pure business logic
- Can be used by application services or other domain services
- No infrastructure imports

### Phase 3: Update Application Service to Use Protocols

**File:** `backend/src/application/reading/services/bookmark_service.py`

```python
from src.application.reading.protocols import (
    BookmarkRepositoryProtocol,
    BookRepositoryProtocol,
    HighlightRepositoryProtocol,
)
from src.domain.reading.services.bookmark_service import BookmarkDomainService
from src.domain.reading.entities.bookmark import Bookmark
from src.domain.common.value_objects.ids import BookmarkId, BookId, HighlightId, UserId
from src.exceptions import BookNotFoundError, HighlightNotFoundError

class BookmarkService:
    """Application service for bookmark use cases."""

    def __init__(
        self,
        bookmark_repository: BookmarkRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
    ) -> None:
        self.bookmark_repository = bookmark_repository
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.domain_service = BookmarkDomainService()

    def create_bookmark(
        self, book_id: int, highlight_id: int, user_id: int
    ) -> Bookmark:
        """
        Use case: Create a bookmark for a highlight.

        Orchestrates:
        1. Convert primitives to value objects
        2. Load required aggregates
        3. Validate business rules (via domain service)
        4. Create and persist bookmark
        """
        # Convert to value objects
        book_id_vo = BookId(book_id)
        highlight_id_vo = HighlightId(highlight_id)
        user_id_vo = UserId(user_id)

        # Load aggregates (raises exceptions if not found)
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise HighlightNotFoundError(highlight_id)

        # Domain validation
        self.domain_service.validate_bookmark_creation(
            book_id=book_id_vo,
            highlight_id=highlight_id_vo,
            book_owner=book.user_id,
            highlight_book_id=highlight.book_id,
            highlight_owner=highlight.user_id,
        )

        # Check for duplicate (idempotency)
        existing = self.bookmark_repository.find_by_book_and_highlight(
            book_id_vo, highlight_id_vo, user_id_vo
        )
        if self.domain_service.is_duplicate_bookmark(existing):
            return existing

        # Create and persist
        bookmark = Bookmark.create(
            book_id=book_id_vo,
            highlight_id=highlight_id_vo,
        )
        return self.bookmark_repository.save(bookmark)

    # ... other methods
```

**Changes:**
- Constructor takes Protocol types instead of concrete classes
- Uses domain service for validation logic
- Focuses on orchestration and transaction management
- Clear separation: application orchestrates, domain validates

### Phase 4: Update DI Container

**File:** `backend/src/core.py`

```python
from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from src.application.reading.services.bookmark_service import BookmarkService
from src.infrastructure.reading.repositories.bookmark_repository import BookmarkRepository
from src.infrastructure.reading.repositories.highlight_repository import HighlightRepository
from src.infrastructure.library.repositories.book_repository import BookRepository

class Container(containers.DeclarativeContainer):
    """Dependency injection container (Composition Root)."""

    # Infrastructure dependencies
    db = providers.Dependency(instance_of=Session)

    # Repository providers (Infrastructure → Application protocol contracts)
    bookmark_repository = providers.Factory(BookmarkRepository, db=db)
    book_repository = providers.Factory(BookRepository, db=db)
    highlight_repository = providers.Factory(HighlightRepository, db=db)

    # Application service providers
    bookmark_service = providers.Factory(
        BookmarkService,
        bookmark_repository=bookmark_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )

# Global container instance
container = Container()
```

**Benefits:**
- All dependencies registered in one place
- Easy to override for testing (e.g., mock repositories)
- Type-safe: mypy verifies BookmarkRepository satisfies BookmarkRepositoryProtocol
- No changes needed to repository implementations

### Phase 5: Router Layer (No Changes Needed)

**File:** `backend/src/infrastructure/reading/routers/bookmarks.py`

The router layer remains the same - it already uses the container correctly:

```python
def get_bookmark_service(db: DatabaseSession) -> BookmarkService:
    container.db.override(db)
    return container.bookmark_service()

@router.post("/{book_id}/bookmarks", response_model=Bookmark)
def create_bookmark(
    book_id: int,
    request: BookmarkCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: BookmarkService = Depends(get_bookmark_service),
) -> Bookmark:
    # ... existing implementation
```

## File Organization

```
backend/src/
├── domain/
│   └── reading/
│       ├── entities/
│       │   └── bookmark.py              (existing)
│       └── services/
│           ├── deduplication_service.py (existing)
│           └── bookmark_service.py      (NEW - domain validation logic)
├── application/
│   └── reading/
│       ├── protocols.py                 (NEW - repository protocols)
│       └── services/
│           └── bookmark_service.py      (MODIFIED - use protocols, delegate to domain)
└── infrastructure/
    ├── reading/
    │   └── repositories/
    │       └── bookmark_repository.py   (existing - no changes needed!)
    └── core.py                          (MODIFIED - wire up dependencies)
```

## Testing Benefits

### Mock Repositories Using Protocols

```python
# tests/unit/application/test_bookmark_service.py

class MockBookmarkRepository:
    """Test double that naturally satisfies BookmarkRepositoryProtocol."""

    def __init__(self):
        self.bookmarks = {}

    def find_by_id(self, bookmark_id: BookmarkId, user_id: UserId) -> Bookmark | None:
        return self.bookmarks.get(bookmark_id.value)

    def save(self, bookmark: Bookmark) -> Bookmark:
        self.bookmarks[bookmark.id.value] = bookmark
        return bookmark

    # ... implement other protocol methods

def test_create_bookmark():
    # Arrange
    mock_bookmark_repo = MockBookmarkRepository()
    mock_book_repo = MockBookRepository()
    mock_highlight_repo = MockHighlightRepository()

    service = BookmarkService(
        bookmark_repository=mock_bookmark_repo,
        book_repository=mock_book_repo,
        highlight_repository=mock_highlight_repo,
    )

    # Act & Assert
    bookmark = service.create_bookmark(book_id=1, highlight_id=1, user_id=1)
    assert bookmark is not None
```

### Test Domain Logic in Isolation

```python
# tests/unit/domain/test_bookmark_domain_service.py

def test_validates_highlight_belongs_to_book():
    # Pure domain logic test - no infrastructure
    with pytest.raises(ValidationError):
        BookmarkDomainService.validate_bookmark_creation(
            book_id=BookId(1),
            highlight_id=HighlightId(10),
            book_owner=UserId(5),
            highlight_book_id=BookId(2),  # Different book!
            highlight_owner=UserId(5),
        )
```

## Migration Strategy

### Step 1: Create Protocols File (Non-Breaking)
- Add `application/reading/protocols.py` with repository protocols
- No changes to existing code

### Step 2: Create Domain Service (Non-Breaking)
- Add `domain/reading/services/bookmark_service.py`
- Extract validation logic from application service
- Both can coexist temporarily

### Step 3: Update Application Service (Breaking - Requires Container Changes)
- Modify `BookmarkService` constructor to use protocols
- Delegate validation to domain service
- Update `core.py` container to inject all dependencies

### Step 4: Update Container (Completes the Migration)
- Register repositories in container
- Wire up application services with repository dependencies

### Step 5: Repeat for Other Services
- Apply same pattern to HighlightService, ReadingSessionService, etc.
- Each bounded context gets its own protocols file

## Critical Files to Modify

1. **NEW:** `backend/src/application/reading/protocols.py` - Repository protocols
2. **NEW:** `backend/src/domain/reading/services/bookmark_service.py` - Domain validation
3. **MODIFY:** `backend/src/application/reading/services/bookmark_service.py` - Use protocols, delegate to domain
4. **MODIFY:** `backend/src/core.py` - Register repositories and wire dependencies
5. **NO CHANGE:** `backend/src/infrastructure/reading/repositories/bookmark_repository.py` - Already compatible!
6. **NO CHANGE:** `backend/src/infrastructure/reading/routers/bookmarks.py` - Router continues to work

## Verification

### Type Checking
```bash
cd backend
mypy src/
```

Should verify that:
- `BookmarkRepository` satisfies `BookmarkRepositoryProtocol`
- All protocol methods are implemented
- Dependency injection types are correct

### Unit Tests
```bash
pytest tests/unit/domain/  # Test domain logic in isolation
pytest tests/unit/application/  # Test use cases with mocks
```

### Integration Tests
```bash
pytest tests/integration/  # Test with real database
```

### Manual Testing
1. Start the backend server
2. Create a bookmark via POST /books/{book_id}/bookmarks
3. Verify validation errors work (e.g., highlight from wrong book)
4. Verify idempotency (creating same bookmark twice returns existing)

## Future Enhancements

### 1. Repository Interfaces for All Contexts
- Create protocol files for library, learning, identity contexts
- Apply same pattern across entire codebase

### 2. Domain Events
- Add event publishing from domain entities
- Use DI to inject event bus

### 3. Specification Pattern
- For complex business rules
- Composable validation logic

### 4. CQRS Separation
- Separate read and write models
- Different repositories for queries vs commands

## Key Takeaways

✅ **What to do:**
- Define Protocols in application layer (define needs of use cases)
- Implement protocols in infrastructure layer (provide adapters)
- Use DI container in infrastructure layer (composition root)
- Move validation logic to domain layer (pure business rules)
- Domain can import application protocols (pragmatic approach)

❌ **What NOT to do:**
- Don't put DI container in domain layer (couples to infrastructure)
- Don't define separate interface files per repository (use Protocols in single file)
- Don't leave validation logic in application services (belongs in domain)
- Don't make repositories inherit from protocols (structural typing is enough)

🎯 **Result:**
- Testable: Easy to mock dependencies
- Decoupled: Domain doesn't depend on infrastructure
- Type-safe: mypy verifies contracts
- Pragmatic: No interface boilerplate, existing code mostly works as-is
