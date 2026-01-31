# Bounded Context Analysis for Crossbill Modular Monolith

## Context

Evaluating whether the four bounded contexts (Library, Reading, Learning, Identity) proposed in the DDD/hexagonal architecture plan make sense for Crossbill as a small modular monolith application.

## Current Codebase Analysis

### Existing Domain Entities (from models.py)

**Book Management:**
- Book (title, author, ISBN, cover, metadata)
- Chapter (hierarchical structure with parent-child relationships)
- Tag (book categorization)

**Reading & Annotation:**
- Highlight (text, page, note, xpoint coordinates, content_hash)
- HighlightTag & HighlightTagGroup (highlight organization)
- Bookmark (reading progress tracking)
- ReadingSession (session tracking with timestamps, pages, AI summaries)

**Learning:**
- Flashcard (question/answer pairs from highlights)

**User Management:**
- User (authentication, multi-user support)

### Existing Services
- BookService, HighlightService, ReadingSessionService, FlashcardService
- BookmarkService, HighlightTagService, BookTagService
- AuthService, UsersService
- EbookService (EPUB/PDF parsing)
- AI services (summary generation)

## Bounded Context Evaluation

### What DDD Distilled Actually Says

You're right to question this! The book emphasizes:
- **Bounded contexts are linguistic boundaries** - different meanings for the same concepts
- **Associated with team ownership** - which doesn't apply here (solo developer)
- **Separate deployments/services** - not relevant for a monolith
- **Don't over-architect** - especially for small teams

### The Reality: Modules vs Bounded Contexts

For Crossbill, we're NOT building microservices with:
- ❌ Separate databases per context
- ❌ Separate deployments
- ❌ Different teams owning different contexts
- ❌ Anti-corruption layers between contexts
- ❌ Event-driven integration

We're building a **modular monolith** with:
- ✅ Shared database with single migration strategy
- ✅ Clear module boundaries in code
- ✅ Dependency rules (domain → no external deps)
- ✅ Testable, maintainable architecture
- ✅ Practice DDD patterns without microservice overhead

## Recommendation: Simplified Module Structure

### Option A: Three Core Modules

**1. Books Module** (combines Library + Reading tracking)
- **Why together**: Tightly coupled - you can't have highlights without books
- **Aggregates**:
  - Book (with chapters, tags)
  - Highlight (with highlight tags, notes)
  - ReadingSession (with bookmarks)
- **Reasoning**: These concepts share the same ubiquitous language - "book", "chapter", "page", "highlight" all relate to the reading experience

**2. Learning Module**
- **Why separate**: Different problem domain - studying vs reading
- **Aggregates**: Flashcard
- **Reasoning**: Flashcards represent spaced repetition study, which is conceptually different from active reading. Could be extended with study sessions, review algorithms, etc.

**3. Identity Module**
- **Why separate**: Cross-cutting authentication/authorization concern
- **Aggregates**: User
- **Reasoning**: User management is orthogonal to the core domain

### Option B: Four Modules (RECOMMENDED)

Keep the original four contexts but treat them as **modules, not microservice-style bounded contexts**:

**1. Library Module**
- Book catalog management
- Aggregates: Book (with chapters, book tags)
- Focus: Managing your book collection

**2. Reading Module**
- Active reading activities
- Aggregates: Highlight, ReadingSession, Bookmark (with highlight tags)
- Focus: The act of reading and annotating

**3. Learning Module**
- Study and retention
- Aggregates: Flashcard
- Focus: Learning from what you've read

**4. Identity Module**
- User management
- Aggregates: User
- Focus: Authentication and user profiles

**Rationale for separation**:
- Library: "I have this book" (possession)
- Reading: "I'm reading and annotating" (activity)
- Learning: "I'm studying this material" (retention)

These DO represent different activities/use cases with potential for distinct evolution.

## Shared Database Strategy for Modular Monolith

### What You CAN Share (Pragmatic)

✅ **Single PostgreSQL database**
- One Alembic migration chain
- MUCH simpler than separate databases
- Transactions can span modules if needed (carefully)

✅ **Direct foreign keys between modules**
- Highlight → Book via book_id (Reading → Library)
- Flashcard → Highlight via highlight_id (Learning → Reading)
- All entities → User via user_id (all → Identity)

✅ **Shared value objects**
- XPoint, ContentHash, etc. can live in `domain/common/value_objects/`

### What You SHOULD Separate (DDD Principles)

🔒 **Module boundaries in code**
```
domain/
  books/        # Can't import from reading or learning
  reading/      # Can import books.BookId but not books.Book entity
  learning/     # Can import reading.HighlightId
  identity/     # Standalone
  common/       # Shared value objects
```

🔒 **Separate repositories per module**
- Reading module uses BookRepository port (defined in application/reading/ports/)
- Implementation lives in infrastructure
- No cross-module repository access

🔒 **Module-specific use cases**
```
application/
  books/commands/     # CreateBook, UpdateBook, DeleteBook
  reading/commands/   # UploadHighlights, CreateSession
  learning/commands/  # CreateFlashcard
```

## Practical Implementation Approach

### 1. ID Sharing Across Modules

**Instead of separate types per context:**
```python
# DON'T over-engineer
class LibraryBookId(BookId): ...  # Unnecessary
class ReadingBookId(BookId): ...  # Overkill
```

**Use shared value objects:**
```python
# domain/common/value_objects/ids.py
@dataclass(frozen=True)
class BookId(EntityId):
    value: int

# Used everywhere - reading, learning, library
```

### 2. Cross-Module References

**Reading module referencing Library:**
```python
# domain/reading/services/highlight.py
from domain.common.value_objects import BookId  # ✅ Shared value object

@dataclass
class Highlight(AggregateRoot[HighlightId]):
    book_id: BookId  # Reference by ID, not entity
    # Don't store Book entity here!
```

### 3. Use Case Coordination

**When use case needs cross-module data:**
```python
# application/learning/commands/create_flashcard.py
class CreateFlashcardHandler:
    def __init__(
        self,
        flashcard_repo: FlashcardRepository,
        highlight_repo: HighlightRepository,  # ✅ Port from reading module
    ):
        ...

    def execute(self, cmd: CreateFlashcardCommand):
        # Fetch highlight from reading module
        highlight = self.highlight_repo.find_by_id(cmd.highlight_id)
        # Create flashcard in learning module
        flashcard = Flashcard.create(...)
```

### 4. Single ORM Models, Multiple Domain Entities

**Shared persistence:**
```python
# infrastructure/persistence/models/book_orm.py
class BookORM(Base):
    __tablename__ = "books"
    # Used by all modules via mappers
```

**Different domain representations** (if needed):
```python
# domain/library/services/book.py - rich entity with business rules
class Book(AggregateRoot[BookId]):
    def add_chapter(self, chapter: Chapter): ...
    def update_metadata(self, metadata: BookMetadata): ...

# domain/reading/value_objects/book_reference.py - lightweight reference
@dataclass(frozen=True)
class BookReference:
    book_id: BookId
    title: str
    # Minimal info needed for reading context
```

## Final Recommendation

### For Crossbill: Go with **Option B (Four Modules)**

**Why?**
1. ✅ **Clear separation of concerns**: Library, Reading, Learning are conceptually distinct
2. ✅ **Room to grow**: Each module can evolve independently
3. ✅ **Practice DDD**: You want to practice these patterns for your career
4. ✅ **Not over-engineered**: Still a monolith with shared database

**But treat them as MODULES, not microservice-style bounded contexts:**
- ❌ Don't create separate databases
- ❌ Don't use async messaging between modules (yet)
- ❌ Don't create elaborate anti-corruption layers
- ✅ DO enforce dependency rules via import-linter
- ✅ DO keep domain logic in each module isolated
- ✅ DO use ports/adapters for external dependencies
- ✅ DO share value objects (BookId, UserId, etc.) in common/

## Implementation Guidelines

### Full Directory Structure (Hexagonal Architecture)

**We're keeping the full 3-layer hexagonal architecture:**

```
backend/src/
  domain/                         # INNER LAYER: Pure business logic
    common/
      entity.py                   # Base classes
      value_object.py
      aggregate_root.py
      exceptions.py
      value_objects/              # Shared value objects
        ids.py                    # BookId, UserId, HighlightId, etc.
        xpoint.py                 # XPoint, XPointRange
        content_hash.py
    books/                        # Books module
      entities/
        book.py
        chapter.py
      value_objects/
        book_metadata.py
        isbn.py
      repositories.py             # Repository INTERFACES (ports)
    reading/                      # Reading module
      entities/
        highlight.py
        reading_session.py
        bookmark.py
      value_objects/
        highlight_text.py
      repositories.py             # Repository INTERFACES (ports)
    learning/                     # Learning module
      entities/
        flashcard.py
      repositories.py
    identity/                     # Identity module
      entities/
        user.py
      repositories.py

  application/                    # MIDDLE LAYER: Use cases & ports
    common/
      command.py                  # Base classes
      query.py
      unit_of_work.py
    ports/                        # Ports for external services
      file_storage.py             # FileStoragePort interface
      ebook_parser.py             # EbookParserPort interface
      ai_service.py               # AIServicePort interface
    books/
      commands/                   # CreateBook, UpdateBook, etc.
      queries/                    # ListBooks, GetBook, etc.
      dtos/                       # Input/output DTOs
    reading/
      commands/                   # UploadHighlights, CreateSession
      queries/                    # SearchHighlights, GetHighlights
      dtos/
    learning/
      commands/
      queries/
      dtos/
    identity/
      commands/
      queries/
      dtos/

  infrastructure/                 # OUTER LAYER: Adapters ✅ KEEP THIS!
    persistence/
      database.py                 # SQLAlchemy session management
      unit_of_work.py             # UoW implementation
      models/                     # ORM models (BookORM, HighlightORM)
        base.py
        book_orm.py
        highlight_orm.py
        reading_session_orm.py
        flashcard_orm.py
        user_orm.py
      mappers/                    # Domain ↔ ORM conversion
        book_mapper.py
        highlight_mapper.py
      repositories/               # Repository IMPLEMENTATIONS
        postgres_book_repository.py
        postgres_highlight_repository.py
        postgres_flashcard_repository.py
    storage/                      # File storage adapters
      local_file_storage.py       # Implements FileStoragePort
      s3_file_storage.py
    ebook/                        # Ebook parsing adapters
      epub_parser.py              # Implements EbookParserPort
      pdf_parser.py
    ai/                           # AI service adapters
      openai_adapter.py           # Implements AIServicePort
      anthropic_adapter.py
    api/                          # HTTP adapters (driving)
      main.py                     # FastAPI app setup
      dependencies.py             # DI container
      routers/                    # HTTP controllers
        books.py
        highlights.py
        flashcards.py
      schemas/                    # API request/response Pydantic models
        book_schemas.py
        highlight_schemas.py
```

**Key points:**
- ✅ Full hexagonal architecture with domain/application/infrastructure
- ✅ `infrastructure/` is essential for the architecture
- ✅ But shared between all modules (not separate infrastructure per module)
- ✅ Single database, single ORM setup, single DI container

### Module Dependencies

```
┌─────────────────────────────────────┐
│         Identity (User)             │ ← No dependencies
└─────────────────────────────────────┘
                  ▲
                  │ UserId
     ┌────────────┴────────────┐
     │                         │
┌────▼────────┐        ┌───────▼──────┐
│   Books     │◄───────│   Reading    │
│  (Library)  │ BookId │ (Highlights) │
└─────────────┘        └───────┬──────┘
                              │ HighlightId
                       ┌──────▼────────┐
                       │   Learning    │
                       │  (Flashcards) │
                       └───────────────┘
```

### Import Rules
```python
# ✅ ALLOWED
domain/books/         → domain/common/
domain/reading/       → domain/common/, domain/books/ (only value objects like BookId)
domain/learning/      → domain/common/, domain/reading/ (only value objects like HighlightId)
domain/identity/      → domain/common/

# ❌ FORBIDDEN
domain/books/         → domain/reading/, domain/learning/
domain/reading/       → domain/learning/
domain/*/             → application/, infrastructure/
```

## Migration Strategy

Given that Phase 0 is already started (common base classes exist), I recommend:

### Phase 1: Complete Foundation (1-2 days)
- ✅ Common value objects (BookId, UserId, HighlightId, XPoint, ContentHash)
- ✅ Shared domain exceptions
- ✅ Verify import-linter rules

### Phase 2: Choose One Module to Migrate Fully (1 week)
**Recommendation: Start with Reading module** (highlights + sessions)
- Most isolated business logic (deduplication, tagging)
- Clear aggregate boundaries
- Good practice case
- High value (core feature)

Complete the full stack for Reading:
1. Domain entities (Highlight, ReadingSession, HighlightTag)
2. Domain services (DeduplicationService)
3. Repository ports + implementations
4. Use cases (UploadHighlights, SearchHighlights)
5. HTTP adapters (refactor routers)

### Phase 3: Repeat for Other Modules
- Books module (2nd priority)
- Learning module (3rd priority)
- Identity module (last - simplest)

---

## Summary

### ✅ Yes, keep four modules (Books, Reading, Learning, Identity)

**Because:**
- Conceptually distinct problem spaces
- Natural aggregate boundaries
- Room for independent evolution
- Good DDD practice

### ✅ But: Pragmatic modular monolith approach

**Which means:**
- Shared database (single Alembic migration)
- Shared value objects (IDs, common domain concepts)
- Direct foreign keys between tables
- No event bus (start simple, add later if needed)
- No anti-corruption layers between modules
- Enforce boundaries via code structure + import linting

**IMPORTANT CLARIFICATION:**
When I say "enforce boundaries in code, not infrastructure":
- ✅ **KEEP the `infrastructure/` directory** - this is the hexagonal architecture infrastructure layer
- ❌ **DON'T use deployment infrastructure** to separate modules (no separate databases, microservices, message queues)

We're using **Hexagonal Architecture (Ports & Adapters)** fully:
```
backend/src/
  domain/           # Pure business logic, no framework deps
  application/      # Use cases, ports (interfaces)
  infrastructure/   # ✅ KEEP THIS! Adapters for DB, HTTP, external services
```

The `infrastructure/` layer is essential for:
- Database adapters (PostgresBookRepository, PostgresHighlightRepository)
- ORM models (BookORM, HighlightORM) - separate from domain entities
- Mappers (domain ↔ ORM conversion)
- HTTP controllers (FastAPI routers)
- External service adapters (AI, file storage, email)

What we're NOT doing:
- ❌ Separate PostgreSQL databases per module
- ❌ Microservice deployments
- ❌ Message queues between modules
- ❌ Different repos per module

### 🎯 Sweet Spot: "DDD-Lite" Architecture

You get:
- ✅ Clean module boundaries
- ✅ Testable domain logic
- ✅ Swappable infrastructure (ports/adapters)
- ✅ Career-relevant DDD practice
- ✅ Room to grow into events/CQRS later

Without:
- ❌ Microservice complexity
- ❌ Distributed transactions
- ❌ Multiple databases
- ❌ Over-engineering for team size

This is **exactly right** for a solo developer building a modular monolith while learning DDD patterns.
