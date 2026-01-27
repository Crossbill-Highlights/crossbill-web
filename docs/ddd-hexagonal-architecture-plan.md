# Domain-Driven Design & Hexagonal Architecture Migration Plan

## Executive Summary

This document outlines a comprehensive plan for migrating the Crossbill backend from its current three-tier layered architecture to a Domain-Driven Design (DDD) approach using Hexagonal Architecture (Ports and Adapters pattern). This migration will improve maintainability, testability, and the ability to evolve the system independently of infrastructure concerns.

---

## Table of Contents

1. [Current Architecture Analysis](#1-current-architecture-analysis)
2. [Target Architecture Overview](#2-target-architecture-overview)
3. [Hexagonal Architecture Layers](#3-hexagonal-architecture-layers)
4. [Domain Model Design](#4-domain-model-design)
5. [Ports and Adapters](#5-ports-and-adapters)
6. [Directory Structure](#6-directory-structure)
7. [Component Diagrams](#7-component-diagrams)
8. [Migration Roadmap](#8-migration-roadmap)
9. [Implementation Guidelines](#9-implementation-guidelines)

---

## 1. Current Architecture Analysis

### 1.1 Current Structure

```
┌─────────────────────────────────────────┐
│  API Layer (routers/)                   │
│  - FastAPI route handlers               │
│  - Request validation via Pydantic      │
└──────────────────┬──────────────────────┘
                   │ direct dependency
┌──────────────────▼──────────────────────┐
│  Service Layer (services/)              │
│  - Business logic (anemic)              │
│  - Repository composition               │
└──────────────────┬──────────────────────┘
                   │ direct dependency
┌──────────────────▼──────────────────────┐
│  Repository Layer (repositories/)       │
│  - SQLAlchemy queries                   │
│  - Database access                      │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  ORM Models (models.py)                 │
│  - SQLAlchemy declarative models        │
│  - 11 entities in single file           │
└─────────────────────────────────────────┘
```

### 1.2 Current Issues

| Issue | Description |
|-------|-------------|
| **Anemic Domain Model** | Models are pure data structures; all behavior lives in services |
| **Monolithic Models** | All 11 entities in a single `models.py` file (~19K lines) |
| **Service God Classes** | `BookService` orchestrates 6+ repositories |
| **No Clear Boundaries** | Services access repositories across domains freely |
| **Infrastructure Leakage** | SQLAlchemy types leak into service layer |
| **Tight Coupling** | Direct dependencies flow top-down, making testing difficult |
| **No Value Objects** | Business concepts like XPoints, ContentHash not encapsulated |

### 1.3 Current Strengths (to preserve)

- Strong typing with Pydantic and type hints
- Repository pattern already in place
- FastAPI dependency injection
- Structured logging with structlog
- User isolation enforced at data layer
- Comprehensive Pydantic schemas for API validation

---

## 2. Target Architecture Overview

### 2.1 Hexagonal Architecture Principles

Hexagonal Architecture (also called Ports and Adapters) organizes code into three concentric layers:

```
                    ┌─────────────────────────────────────┐
                    │         INFRASTRUCTURE              │
                    │    (Adapters: DB, HTTP, Files)      │
                    │  ┌─────────────────────────────┐    │
                    │  │        APPLICATION          │    │
                    │  │    (Use Cases, Ports)       │    │
                    │  │  ┌─────────────────────┐    │    │
                    │  │  │      DOMAIN         │    │    │
                    │  │  │ (Entities, Values,  │    │    │
                    │  │  │  Domain Services)   │    │    │
                    │  │  └─────────────────────┘    │    │
                    │  └─────────────────────────────┘    │
                    └─────────────────────────────────────┘
```

**Core Principle:** Dependencies point inward. The domain layer has NO dependencies on outer layers.

### 2.2 Key Concepts

| Concept | Description |
|---------|-------------|
| **Domain Layer** | Pure business logic, no framework dependencies |
| **Application Layer** | Orchestrates domain objects, defines ports (interfaces) |
| **Infrastructure Layer** | Implements adapters for external systems |
| **Port** | Interface defined by application layer (abstract) |
| **Adapter** | Concrete implementation of a port |
| **Driving Adapter** | Initiates interaction (HTTP, CLI, tests) |
| **Driven Adapter** | Responds to application needs (DB, email, storage) |

---

## 3. Hexagonal Architecture Layers

### 3.1 Domain Layer (Core)

The innermost layer containing pure business logic with zero external dependencies.

#### Contents:
- **Entities** - Objects with identity and lifecycle
- **Value Objects** - Immutable objects defined by their attributes
- **Aggregate Roots** - Consistency boundaries for related entities
- **Domain Services** - Stateless operations spanning multiple entities
- **Domain Events** - Notifications of significant domain occurrences
- **Repository Interfaces** - Abstract contracts (not implementations)

#### Rules:
- No imports from application or infrastructure layers
- No framework dependencies (no SQLAlchemy, FastAPI, Pydantic)
- Pure Python with dataclasses or custom base classes
- All validation and business rules live here

### 3.2 Application Layer

Orchestrates domain objects and defines the boundaries of the system.

#### Contents:
- **Use Cases** - Single-purpose operations (Command/Query handlers)
- **Input/Output DTOs** - Data transfer objects for use case boundaries
- **Port Interfaces** - Abstract interfaces for driven adapters
- **Application Services** - Thin orchestration layer
- **Event Handlers** - React to domain events

#### Rules:
- Depends only on Domain layer
- Defines ports (interfaces) that infrastructure implements
- Framework-agnostic (can be tested without HTTP/DB)
- Transaction boundaries defined here

### 3.3 Infrastructure Layer

Implements adapters that connect the application to the outside world.

#### Contents:
- **Driving Adapters** - HTTP controllers, CLI, message consumers
- **Driven Adapters** - Database repositories, file storage, external APIs
- **ORM Models** - SQLAlchemy models (separate from domain entities)
- **Mappers** - Convert between domain entities and ORM models
- **Configuration** - Environment, DI container setup

#### Rules:
- Implements port interfaces from application layer
- Contains all framework-specific code
- Can be swapped without affecting domain/application layers

---

## 4. Domain Model Design

### 4.1 Identified Bounded Contexts

Based on the current codebase analysis, we identify four bounded contexts:

```
┌──────────────────────────────────────────────────────────────────┐
│                        CROSSBILL SYSTEM                           │
├──────────────────┬──────────────────┬──────────────────┬─────────┤
│  LIBRARY         │  READING         │  LEARNING        │ IDENTITY│
│  CONTEXT         │  CONTEXT         │  CONTEXT         │ CONTEXT │
├──────────────────┼──────────────────┼──────────────────┼─────────┤
│ • Book           │ • ReadingSession │ • Flashcard      │ • User  │
│ • Chapter        │ • Highlight      │ • StudyProgress  │ • Auth  │
│ • BookMetadata   │ • Bookmark       │                  │         │
│ • BookTag        │ • HighlightTag   │                  │         │
│ • EbookFile      │ • XPoint         │                  │         │
└──────────────────┴──────────────────┴──────────────────┴─────────┘
```

### 4.2 Aggregate Design

#### Library Context

```
┌─────────────────────────────────────────────┐
│           BOOK AGGREGATE                     │
│  ┌─────────────────────────────────────┐    │
│  │  Book (Aggregate Root)              │    │
│  │  - BookId (Value Object)            │    │
│  │  - Title, Author, ISBN              │    │
│  │  - BookMetadata (Value Object)      │    │
│  │  - EbookFile (Value Object)         │    │
│  └─────────────────────────────────────┘    │
│           │                                  │
│           │ contains                         │
│           ▼                                  │
│  ┌─────────────────────────────────────┐    │
│  │  Chapter (Entity)                   │    │
│  │  - ChapterId                        │    │
│  │  - ChapterHierarchy (Value Object)  │    │
│  └─────────────────────────────────────┘    │
│           │                                  │
│           │ tagged with                      │
│           ▼                                  │
│  ┌─────────────────────────────────────┐    │
│  │  BookTag (Entity)                   │    │
│  │  - TagId                            │    │
│  │  - TagName (Value Object)           │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

#### Reading Context

```
┌─────────────────────────────────────────────┐
│        HIGHLIGHT AGGREGATE                   │
│  ┌─────────────────────────────────────┐    │
│  │  Highlight (Aggregate Root)         │    │
│  │  - HighlightId (Value Object)       │    │
│  │  - HighlightText (Value Object)     │    │
│  │  - XPointRange (Value Object)       │    │
│  │  - ContentHash (Value Object)       │    │
│  │  - Note                             │    │
│  └─────────────────────────────────────┘    │
│           │                                  │
│           │ tagged with                      │
│           ▼                                  │
│  ┌─────────────────────────────────────┐    │
│  │  HighlightTag (Entity)              │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│     READING SESSION AGGREGATE               │
│  ┌─────────────────────────────────────┐    │
│  │  ReadingSession (Aggregate Root)    │    │
│  │  - SessionId (Value Object)         │    │
│  │  - TimeRange (Value Object)         │    │
│  │  - PageRange (Value Object)         │    │
│  │  - DeviceId (Value Object)          │    │
│  │  - ContentHash (Value Object)       │    │
│  └─────────────────────────────────────┘    │
│           │                                  │
│           │ references                       │
│           ▼                                  │
│  ┌─────────────────────────────────────┐    │
│  │  Highlight References (by ID only)  │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        BOOKMARK AGGREGATE                    │
│  ┌─────────────────────────────────────┐    │
│  │  Bookmark (Aggregate Root)          │    │
│  │  - BookmarkId                       │    │
│  │  - Points to Highlight (by ID)      │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

#### Learning Context

```
┌─────────────────────────────────────────────┐
│        FLASHCARD AGGREGATE                   │
│  ┌─────────────────────────────────────┐    │
│  │  Flashcard (Aggregate Root)         │    │
│  │  - FlashcardId                      │    │
│  │  - Question, Answer                 │    │
│  │  - SourceHighlightId (reference)    │    │
│  │  - StudyMetadata (Value Object)     │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 4.3 Value Objects

Value Objects encapsulate business concepts and validation:

```python
# Example Value Objects for the Domain

@dataclass(frozen=True)
class BookId:
    """Strongly-typed book identifier."""
    value: int

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("BookId must be positive")

@dataclass(frozen=True)
class XPoint:
    """Position within an EPUB document."""
    chapter_index: int
    element_path: str
    character_offset: int

    def __post_init__(self) -> None:
        if self.chapter_index < 0:
            raise ValueError("Chapter index must be non-negative")

@dataclass(frozen=True)
class XPointRange:
    """Range between two XPoints for highlights."""
    start: XPoint
    end: XPoint

    def contains(self, point: XPoint) -> bool:
        """Check if a point falls within this range."""
        ...

@dataclass(frozen=True)
class ContentHash:
    """Hash for deduplication of highlights/sessions."""
    value: str

    @classmethod
    def compute(cls, content: str) -> "ContentHash":
        """Compute hash from content."""
        import hashlib
        return cls(hashlib.sha256(content.encode()).hexdigest())

@dataclass(frozen=True)
class HighlightText:
    """Validated highlight text with constraints."""
    value: str

    MAX_LENGTH = 10000

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Highlight text cannot be empty")
        if len(self.value) > self.MAX_LENGTH:
            raise ValueError(f"Highlight text exceeds {self.MAX_LENGTH} characters")

@dataclass(frozen=True)
class TimeRange:
    """Time range for reading sessions."""
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("End time must be after start time")

    @property
    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

@dataclass(frozen=True)
class PageRange:
    """Page range for reading sessions."""
    start_page: int
    end_page: int

    @property
    def pages_read(self) -> int:
        return max(0, self.end_page - self.start_page)
```

### 4.4 Domain Entities

Domain entities are rich objects with behavior:

```python
@dataclass
class Highlight:
    """
    Highlight aggregate root.

    Encapsulates all business rules for highlight management.
    """
    id: HighlightId
    user_id: UserId
    book_id: BookId
    chapter_id: ChapterId | None
    text: HighlightText
    xpoints: XPointRange | None
    page: int | None
    note: str | None
    content_hash: ContentHash
    created_at: datetime
    deleted_at: datetime | None
    tags: list[HighlightTag]

    def is_deleted(self) -> bool:
        """Check if highlight has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Soft delete this highlight."""
        if self.is_deleted():
            raise DomainError("Highlight already deleted")
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore a soft-deleted highlight."""
        if not self.is_deleted():
            raise DomainError("Highlight is not deleted")
        self.deleted_at = None

    def update_note(self, note: str | None) -> None:
        """Update the note attached to this highlight."""
        self.note = note

    def add_tag(self, tag: HighlightTag) -> None:
        """Add a tag to this highlight."""
        if tag in self.tags:
            raise DomainError(f"Tag {tag.name} already exists")
        self.tags.append(tag)

    def remove_tag(self, tag_id: HighlightTagId) -> None:
        """Remove a tag from this highlight."""
        self.tags = [t for t in self.tags if t.id != tag_id]

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        text: str,
        chapter_id: ChapterId | None = None,
        xpoints: XPointRange | None = None,
        page: int | None = None,
        note: str | None = None,
    ) -> "Highlight":
        """Factory method for creating new highlights."""
        highlight_text = HighlightText(text)
        content_hash = ContentHash.compute(text)

        return cls(
            id=HighlightId.generate(),
            user_id=user_id,
            book_id=book_id,
            chapter_id=chapter_id,
            text=highlight_text,
            xpoints=xpoints,
            page=page,
            note=note,
            content_hash=content_hash,
            created_at=datetime.now(UTC),
            deleted_at=None,
            tags=[],
        )
```

### 4.5 Domain Services

For operations that span multiple aggregates:

```python
class HighlightDeduplicationService:
    """
    Domain service for highlight deduplication logic.

    This is a pure domain service with no infrastructure dependencies.
    """

    def find_duplicates(
        self,
        new_highlights: list[Highlight],
        existing_hashes: set[ContentHash],
    ) -> tuple[list[Highlight], list[Highlight]]:
        """
        Separate new highlights from duplicates.

        Returns:
            Tuple of (unique_highlights, duplicate_highlights)
        """
        unique = []
        duplicates = []

        for highlight in new_highlights:
            if highlight.content_hash in existing_hashes:
                duplicates.append(highlight)
            else:
                unique.append(highlight)
                existing_hashes.add(highlight.content_hash)

        return unique, duplicates


class ReadingSessionAnalysisService:
    """Domain service for reading session analysis."""

    def calculate_reading_speed(
        self,
        session: ReadingSession,
        total_words: int,
    ) -> int:
        """Calculate words per minute for a session."""
        if session.time_range.duration_minutes == 0:
            return 0
        return total_words // session.time_range.duration_minutes

    def merge_overlapping_sessions(
        self,
        sessions: list[ReadingSession],
    ) -> list[ReadingSession]:
        """Merge sessions that overlap in time."""
        ...
```

---

## 5. Ports and Adapters

### 5.1 Port Interfaces (Application Layer)

Ports are interfaces that define how the application interacts with the outside world.

#### Repository Ports (Driven)

```python
from abc import ABC, abstractmethod
from typing import Protocol

class HighlightRepository(Protocol):
    """Port for highlight persistence."""

    def save(self, highlight: Highlight) -> None:
        """Persist a highlight."""
        ...

    def save_all(self, highlights: list[Highlight]) -> None:
        """Persist multiple highlights."""
        ...

    def find_by_id(self, id: HighlightId, user_id: UserId) -> Highlight | None:
        """Find highlight by ID."""
        ...

    def find_by_book(
        self,
        book_id: BookId,
        user_id: UserId,
        include_deleted: bool = False,
    ) -> list[Highlight]:
        """Find all highlights for a book."""
        ...

    def find_existing_hashes(
        self,
        book_id: BookId,
        user_id: UserId,
    ) -> set[ContentHash]:
        """Get all content hashes for deduplication."""
        ...

    def delete(self, id: HighlightId, user_id: UserId) -> bool:
        """Hard delete a highlight."""
        ...


class BookRepository(Protocol):
    """Port for book persistence."""

    def save(self, book: Book) -> None:
        ...

    def find_by_id(self, id: BookId, user_id: UserId) -> Book | None:
        ...

    def find_by_client_id(
        self,
        client_book_id: str,
        user_id: UserId,
    ) -> Book | None:
        ...

    def find_all(
        self,
        user_id: UserId,
        pagination: Pagination,
        filters: BookFilters,
    ) -> PaginatedResult[Book]:
        ...

    def delete(self, id: BookId, user_id: UserId) -> bool:
        ...
```

#### External Service Ports (Driven)

```python
class FileStoragePort(Protocol):
    """Port for file storage operations."""

    def store_ebook(self, book_id: BookId, content: bytes, filename: str) -> str:
        """Store ebook file, return path."""
        ...

    def store_cover(self, book_id: BookId, content: bytes) -> str:
        """Store cover image, return path."""
        ...

    def retrieve_ebook(self, path: str) -> bytes:
        """Retrieve ebook content."""
        ...

    def delete_book_files(self, book_id: BookId) -> None:
        """Delete all files for a book."""
        ...


class EbookParserPort(Protocol):
    """Port for ebook parsing operations."""

    def parse_epub(self, content: bytes) -> EbookMetadata:
        """Parse EPUB and extract metadata."""
        ...

    def extract_text(
        self,
        content: bytes,
        xpoint_range: XPointRange,
    ) -> str:
        """Extract text from EPUB at given range."""
        ...

    def get_table_of_contents(self, content: bytes) -> list[ChapterInfo]:
        """Extract table of contents."""
        ...


class AIServicePort(Protocol):
    """Port for AI-powered features."""

    def generate_summary(
        self,
        session: ReadingSession,
        highlights: list[Highlight],
    ) -> str:
        """Generate AI summary for reading session."""
        ...

    def generate_flashcards(
        self,
        highlight: Highlight,
    ) -> list[FlashcardSuggestion]:
        """Generate flashcard suggestions from highlight."""
        ...


class SearchIndexPort(Protocol):
    """Port for full-text search operations."""

    def index_highlight(self, highlight: Highlight) -> None:
        """Index a highlight for full-text search."""
        ...

    def search(
        self,
        query: str,
        user_id: UserId,
        book_id: BookId | None = None,
    ) -> list[SearchResult]:
        """Search highlights."""
        ...
```

### 5.2 Adapter Implementations (Infrastructure Layer)

#### Driven Adapters

```python
# PostgreSQL implementation of HighlightRepository
class PostgresHighlightRepository:
    """SQLAlchemy-based implementation of HighlightRepository port."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._mapper = HighlightMapper()

    def save(self, highlight: Highlight) -> None:
        orm_model = self._mapper.to_orm(highlight)
        self._session.merge(orm_model)

    def find_by_id(
        self,
        id: HighlightId,
        user_id: UserId,
    ) -> Highlight | None:
        stmt = (
            select(HighlightORM)
            .where(HighlightORM.id == id.value)
            .where(HighlightORM.user_id == user_id.value)
        )
        result = self._session.execute(stmt).scalar_one_or_none()
        return self._mapper.to_domain(result) if result else None


# Local filesystem implementation of FileStoragePort
class LocalFileStorage:
    """Local filesystem implementation of FileStoragePort."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path

    def store_ebook(
        self,
        book_id: BookId,
        content: bytes,
        filename: str,
    ) -> str:
        path = self._base_path / str(book_id.value) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)


# S3 implementation (alternative)
class S3FileStorage:
    """AWS S3 implementation of FileStoragePort."""

    def __init__(self, bucket: str, client: S3Client) -> None:
        self._bucket = bucket
        self._client = client

    def store_ebook(
        self,
        book_id: BookId,
        content: bytes,
        filename: str,
    ) -> str:
        key = f"books/{book_id.value}/{filename}"
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content)
        return f"s3://{self._bucket}/{key}"
```

#### Driving Adapters

```python
# FastAPI HTTP adapter (controller)
class HighlightHTTPAdapter:
    """FastAPI router as driving adapter."""

    def __init__(self, upload_highlights: UploadHighlightsUseCase) -> None:
        self._upload_highlights = upload_highlights
        self.router = APIRouter(prefix="/api/v1/highlights")
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.router.post("/upload")
        async def upload(
            request: HighlightUploadRequest,
            user: CurrentUser,
        ) -> HighlightUploadResponse:
            # Convert HTTP request to use case input
            command = UploadHighlightsCommand(
                user_id=UserId(user.id),
                book_id=BookId(request.book_id),
                highlights=[
                    HighlightData(
                        text=h.text,
                        page=h.page,
                        xpoints=h.xpoints,
                        note=h.note,
                    )
                    for h in request.highlights
                ],
            )

            # Execute use case
            result = self._upload_highlights.execute(command)

            # Convert result to HTTP response
            return HighlightUploadResponse(
                created=result.created_count,
                duplicates=result.duplicate_count,
            )
```

### 5.3 Ports and Adapters Diagram

```
                        DRIVING ADAPTERS
                    (Primary/Input Adapters)
    ┌──────────────────────────────────────────────────────┐
    │                                                       │
    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
    │   │ FastAPI  │  │   CLI    │  │  Message Queue   │   │
    │   │ HTTP API │  │ Commands │  │    Consumer      │   │
    │   └────┬─────┘  └────┬─────┘  └────────┬─────────┘   │
    │        │             │                  │             │
    └────────┼─────────────┼──────────────────┼─────────────┘
             │             │                  │
             ▼             ▼                  ▼
    ┌──────────────────────────────────────────────────────┐
    │                   INPUT PORTS                         │
    │         (Use Case Interfaces/Commands)               │
    │   ┌─────────────────────────────────────────────┐    │
    │   │  UploadHighlightsUseCase                    │    │
    │   │  CreateBookUseCase                          │    │
    │   │  RecordReadingSessionUseCase                │    │
    │   │  GenerateFlashcardsUseCase                  │    │
    │   │  SearchHighlightsQuery                      │    │
    │   └─────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────┐
    │                 APPLICATION LAYER                     │
    │              (Use Case Implementations)              │
    │   ┌─────────────────────────────────────────────┐    │
    │   │  Use cases orchestrate domain objects and   │    │
    │   │  coordinate with ports for external needs   │    │
    │   └─────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────┐
    │                    DOMAIN LAYER                       │
    │                (Pure Business Logic)                 │
    │   ┌─────────────────────────────────────────────┐    │
    │   │  Entities: Book, Highlight, ReadingSession  │    │
    │   │  Value Objects: XPoint, ContentHash, etc.   │    │
    │   │  Domain Services: DeduplicationService      │    │
    │   │  Domain Events: HighlightCreated, etc.      │    │
    │   └─────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌──────────────────────────────────────────────────────┐
    │                   OUTPUT PORTS                        │
    │            (Repository/Service Interfaces)           │
    │   ┌─────────────────────────────────────────────┐    │
    │   │  HighlightRepository (Protocol)             │    │
    │   │  BookRepository (Protocol)                  │    │
    │   │  FileStoragePort (Protocol)                 │    │
    │   │  EbookParserPort (Protocol)                 │    │
    │   │  AIServicePort (Protocol)                   │    │
    │   │  SearchIndexPort (Protocol)                 │    │
    │   └─────────────────────────────────────────────┘    │
    └──────────────────────────────────────────────────────┘
             │             │                  │
             ▼             ▼                  ▼
    ┌──────────────────────────────────────────────────────┐
    │                                                       │
    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
    │   │PostgreSQL│  │  Local   │  │   OpenAI/        │   │
    │   │Repository│  │  Files   │  │   Anthropic      │   │
    │   └──────────┘  └──────────┘  └──────────────────┘   │
    │                                                       │
    │   ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
    │   │  Redis   │  │   S3     │  │   Elasticsearch  │   │
    │   │  Cache   │  │ Storage  │  │     Search       │   │
    │   └──────────┘  └──────────┘  └──────────────────┘   │
    │                                                       │
    │                    DRIVEN ADAPTERS                   │
    │               (Secondary/Output Adapters)            │
    └──────────────────────────────────────────────────────┘
```

---

## 6. Directory Structure

### 6.1 Proposed Structure

```
backend/
├── src/
│   ├── __init__.py
│   │
│   ├── domain/                          # DOMAIN LAYER
│   │   ├── __init__.py
│   │   │
│   │   ├── common/                      # Shared domain concepts
│   │   │   ├── __init__.py
│   │   │   ├── entity.py                # Base entity class
│   │   │   ├── value_object.py          # Base value object
│   │   │   ├── aggregate_root.py        # Aggregate root base
│   │   │   ├── domain_event.py          # Domain event base
│   │   │   └── exceptions.py            # Domain exceptions
│   │   │
│   │   ├── library/                     # Library bounded context
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── book.py              # Book aggregate root
│   │   │   │   ├── chapter.py           # Chapter entity
│   │   │   │   └── book_tag.py          # BookTag entity
│   │   │   ├── value_objects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── book_id.py
│   │   │   │   ├── book_metadata.py
│   │   │   │   ├── ebook_file.py
│   │   │   │   └── isbn.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── book_validation_service.py
│   │   │   ├── events/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── book_created.py
│   │   │   │   └── book_deleted.py
│   │   │   └── repositories.py          # Repository interfaces (Protocols)
│   │   │
│   │   ├── reading/                     # Reading bounded context
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── highlight.py         # Highlight aggregate root
│   │   │   │   ├── highlight_tag.py
│   │   │   │   ├── reading_session.py   # ReadingSession aggregate root
│   │   │   │   └── bookmark.py          # Bookmark aggregate root
│   │   │   ├── value_objects/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── highlight_id.py
│   │   │   │   ├── highlight_text.py
│   │   │   │   ├── xpoint.py
│   │   │   │   ├── xpoint_range.py
│   │   │   │   ├── content_hash.py
│   │   │   │   ├── time_range.py
│   │   │   │   └── page_range.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deduplication_service.py
│   │   │   │   └── session_analysis_service.py
│   │   │   ├── events/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── highlight_created.py
│   │   │   │   └── session_recorded.py
│   │   │   └── repositories.py          # Repository interfaces
│   │   │
│   │   ├── learning/                    # Learning bounded context
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   └── flashcard.py         # Flashcard aggregate root
│   │   │   ├── value_objects/
│   │   │   │   ├── __init__.py
│   │   │   │   └── flashcard_id.py
│   │   │   ├── events/
│   │   │   │   └── __init__.py
│   │   │   └── repositories.py
│   │   │
│   │   └── identity/                    # Identity bounded context
│   │       ├── __init__.py
│   │       ├── entities/
│   │       │   ├── __init__.py
│   │       │   └── user.py
│   │       ├── value_objects/
│   │       │   ├── __init__.py
│   │       │   ├── user_id.py
│   │       │   ├── email.py
│   │       │   └── password.py
│   │       └── repositories.py
│   │
│   ├── application/                     # APPLICATION LAYER
│   │   ├── __init__.py
│   │   │
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   ├── use_case.py              # Base use case class
│   │   │   ├── unit_of_work.py          # UoW interface
│   │   │   ├── pagination.py            # Pagination DTOs
│   │   │   └── result.py                # Result type for use cases
│   │   │
│   │   ├── ports/                       # Output port interfaces
│   │   │   ├── __init__.py
│   │   │   ├── file_storage.py          # FileStoragePort
│   │   │   ├── ebook_parser.py          # EbookParserPort
│   │   │   ├── ai_service.py            # AIServicePort
│   │   │   ├── search_index.py          # SearchIndexPort
│   │   │   └── email_service.py         # EmailServicePort
│   │   │
│   │   ├── library/                     # Library use cases
│   │   │   ├── __init__.py
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_book.py       # CreateBookCommand + Handler
│   │   │   │   ├── upload_ebook.py      # UploadEbookCommand + Handler
│   │   │   │   ├── update_book.py
│   │   │   │   └── delete_book.py
│   │   │   ├── queries/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── get_book.py          # GetBookQuery + Handler
│   │   │   │   ├── list_books.py
│   │   │   │   └── get_book_details.py
│   │   │   └── dtos/
│   │   │       ├── __init__.py
│   │   │       └── book_dtos.py         # Input/Output DTOs
│   │   │
│   │   ├── reading/                     # Reading use cases
│   │   │   ├── __init__.py
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── upload_highlights.py
│   │   │   │   ├── update_highlight_note.py
│   │   │   │   ├── delete_highlight.py
│   │   │   │   ├── record_reading_session.py
│   │   │   │   └── create_bookmark.py
│   │   │   ├── queries/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── search_highlights.py
│   │   │   │   ├── get_book_highlights.py
│   │   │   │   └── get_reading_sessions.py
│   │   │   └── dtos/
│   │   │       ├── __init__.py
│   │   │       ├── highlight_dtos.py
│   │   │       └── session_dtos.py
│   │   │
│   │   ├── learning/                    # Learning use cases
│   │   │   ├── __init__.py
│   │   │   ├── commands/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── create_flashcard.py
│   │   │   │   ├── generate_flashcards.py  # AI-powered
│   │   │   │   └── update_flashcard.py
│   │   │   └── queries/
│   │   │       ├── __init__.py
│   │   │       └── get_flashcards.py
│   │   │
│   │   └── identity/                    # Identity use cases
│   │       ├── __init__.py
│   │       ├── commands/
│   │       │   ├── __init__.py
│   │       │   ├── register_user.py
│   │       │   └── update_profile.py
│   │       └── queries/
│   │           ├── __init__.py
│   │           └── authenticate.py
│   │
│   └── infrastructure/                  # INFRASTRUCTURE LAYER
│       ├── __init__.py
│       │
│       ├── persistence/                 # Database adapters
│       │   ├── __init__.py
│       │   ├── database.py              # Session management
│       │   ├── unit_of_work.py          # SQLAlchemy UoW
│       │   │
│       │   ├── models/                  # ORM models (separate from domain!)
│       │   │   ├── __init__.py
│       │   │   ├── base.py              # SQLAlchemy base
│       │   │   ├── book_orm.py
│       │   │   ├── chapter_orm.py
│       │   │   ├── highlight_orm.py
│       │   │   ├── reading_session_orm.py
│       │   │   ├── flashcard_orm.py
│       │   │   ├── user_orm.py
│       │   │   └── associations.py      # Many-to-many tables
│       │   │
│       │   ├── mappers/                 # Domain <-> ORM mapping
│       │   │   ├── __init__.py
│       │   │   ├── book_mapper.py
│       │   │   ├── highlight_mapper.py
│       │   │   ├── session_mapper.py
│       │   │   └── user_mapper.py
│       │   │
│       │   └── repositories/            # Repository implementations
│       │       ├── __init__.py
│       │       ├── postgres_book_repository.py
│       │       ├── postgres_highlight_repository.py
│       │       ├── postgres_session_repository.py
│       │       ├── postgres_flashcard_repository.py
│       │       └── postgres_user_repository.py
│       │
│       ├── storage/                     # File storage adapters
│       │   ├── __init__.py
│       │   ├── local_file_storage.py
│       │   └── s3_file_storage.py
│       │
│       ├── ebook/                       # Ebook parsing adapters
│       │   ├── __init__.py
│       │   ├── epub_parser.py
│       │   ├── pdf_parser.py
│       │   └── xpoint_utils.py
│       │
│       ├── ai/                          # AI service adapters
│       │   ├── __init__.py
│       │   ├── openai_adapter.py
│       │   └── anthropic_adapter.py
│       │
│       ├── search/                      # Search adapters
│       │   ├── __init__.py
│       │   └── postgres_fts_adapter.py
│       │
│       └── api/                         # HTTP/API adapters (driving)
│           ├── __init__.py
│           ├── main.py                  # FastAPI app setup
│           ├── dependencies.py          # DI setup
│           ├── middleware/
│           │   ├── __init__.py
│           │   ├── auth.py
│           │   ├── error_handling.py
│           │   └── request_id.py
│           ├── schemas/                 # API request/response schemas
│           │   ├── __init__.py
│           │   ├── book_schemas.py
│           │   ├── highlight_schemas.py
│           │   └── ...
│           └── routers/                 # FastAPI routers
│               ├── __init__.py
│               ├── books.py
│               ├── highlights.py
│               ├── reading_sessions.py
│               └── ...
│
├── alembic/                             # Migrations (unchanged)
├── tests/
│   ├── unit/
│   │   ├── domain/                      # Domain unit tests
│   │   └── application/                 # Use case unit tests
│   ├── integration/
│   │   └── infrastructure/              # Adapter integration tests
│   └── e2e/                             # End-to-end API tests
│
├── pyproject.toml
└── alembic.ini
```

### 6.2 Import Rules

To enforce the dependency direction, establish these import rules:

```
┌─────────────────────────────────────────────────────────────────┐
│  ALLOWED IMPORTS                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  domain/         → (nothing external, only stdlib + domain/)    │
│                                                                  │
│  application/    → domain/                                      │
│                  → application/                                 │
│                                                                  │
│  infrastructure/ → domain/                                      │
│                  → application/                                 │
│                  → infrastructure/                              │
│                  → external packages (FastAPI, SQLAlchemy, etc) │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  FORBIDDEN IMPORTS                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  domain/         ✗→ application/                                │
│                  ✗→ infrastructure/                             │
│                  ✗→ FastAPI, SQLAlchemy, Pydantic              │
│                                                                  │
│  application/    ✗→ infrastructure/                             │
│                  ✗→ FastAPI, SQLAlchemy                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Component Diagrams

### 7.1 System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL ACTORS                                │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Web App  │      │ KOReader │      │  Mobile  │      │   CLI    │
    │ (React)  │      │  Plugin  │      │   App    │      │  Tools   │
    └────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
         │                 │                 │                 │
         └─────────────────┴─────────────────┴─────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CROSSBILL BACKEND                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                        API Gateway                                 │  │
│  │                    (FastAPI + Auth)                               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION SERVICES                           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │  │
│  │  │ Library │ │ Reading │ │Learning │ │Identity │ │   AI    │     │  │
│  │  │Use Cases│ │Use Cases│ │Use Cases│ │Use Cases│ │Use Cases│     │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                   │                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      DOMAIN MODEL                                 │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                 │  │
│  │  │  Book   │ │Highlight│ │Flashcard│ │  User   │                 │  │
│  │  │Aggregate│ │Aggregate│ │Aggregate│ │Aggregate│                 │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
         │                 │                 │                 │
         ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL SYSTEMS                                  │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
    │PostgreSQL│      │  File    │      │ OpenAI / │      │  Redis   │
    │ Database │      │ Storage  │      │ Anthropic│      │  Cache   │
    └──────────┘      └──────────┘      └──────────┘      └──────────┘
```

### 7.2 Highlight Upload Flow (Sequence)

```
┌─────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────┐
│ KOReader│     │ HTTP    │     │ Upload       │     │ Highlight    │     │ Postgres │
│ Plugin  │     │ Adapter │     │ UseCase      │     │ Repository   │     │ Adapter  │
└────┬────┘     └────┬────┘     └──────┬───────┘     └──────┬───────┘     └────┬─────┘
     │               │                 │                    │                  │
     │ POST /highlights/upload         │                    │                  │
     │──────────────>│                 │                    │                  │
     │               │                 │                    │                  │
     │               │ UploadHighlights│                    │                  │
     │               │ Command         │                    │                  │
     │               │────────────────>│                    │                  │
     │               │                 │                    │                  │
     │               │                 │ find_existing_     │                  │
     │               │                 │ hashes()           │                  │
     │               │                 │───────────────────>│                  │
     │               │                 │                    │                  │
     │               │                 │                    │ SELECT hashes   │
     │               │                 │                    │─────────────────>│
     │               │                 │                    │                  │
     │               │                 │                    │<─────────────────│
     │               │                 │<───────────────────│                  │
     │               │                 │                    │                  │
     │               │                 │ [Domain Logic]     │                  │
     │               │                 │ Deduplicate using  │                  │
     │               │                 │ DeduplicationSvc   │                  │
     │               │                 │                    │                  │
     │               │                 │ save_all(new)      │                  │
     │               │                 │───────────────────>│                  │
     │               │                 │                    │                  │
     │               │                 │                    │ INSERT highlights│
     │               │                 │                    │─────────────────>│
     │               │                 │                    │                  │
     │               │                 │                    │<─────────────────│
     │               │                 │<───────────────────│                  │
     │               │                 │                    │                  │
     │               │ UploadResult    │                    │                  │
     │               │<────────────────│                    │                  │
     │               │                 │                    │                  │
     │ 200 OK        │                 │                    │                  │
     │ {created: N}  │                 │                    │                  │
     │<──────────────│                 │                    │                  │
     │               │                 │                    │                  │
```

### 7.3 Dependency Inversion Diagram

```
                    BEFORE (Current)
                    ================

┌───────────────┐         ┌───────────────┐
│    Router     │────────>│    Service    │
│  (FastAPI)    │         │ (BookService) │
└───────────────┘         └───────┬───────┘
                                  │
                                  │ depends on
                                  ▼
                          ┌───────────────┐
                          │  Repository   │
                          │ (SQLAlchemy)  │
                          └───────────────┘

    Problem: Service depends directly on concrete Repository
    (infrastructure concern)


                    AFTER (Hexagonal)
                    ==================

┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│    Router     │────────>│   Use Case    │<────────│   Domain      │
│  (Adapter)    │         │ (Application) │         │   Entities    │
└───────────────┘         └───────┬───────┘         └───────────────┘
                                  │
                                  │ depends on
                                  ▼
                          ┌───────────────┐
                          │     Port      │
                          │  (Interface)  │
                          └───────────────┘
                                  ▲
                                  │ implements
                                  │
                          ┌───────────────┐
                          │   Adapter     │
                          │ (PostgreSQL)  │
                          └───────────────┘

    Solution: Use Case depends on Port (interface),
    Adapter implements Port (dependency inversion)
```

### 7.4 Bounded Context Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CROSSBILL DOMAIN                                  │
└─────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐              ┌─────────────────────────┐
    │     LIBRARY CONTEXT     │              │    READING CONTEXT      │
    │                         │              │                         │
    │  ┌─────────────────┐    │   BookId     │  ┌─────────────────┐    │
    │  │      Book       │────┼──────────────┼─>│    Highlight    │    │
    │  │  (Aggregate)    │    │              │  │   (Aggregate)   │    │
    │  └────────┬────────┘    │              │  └────────┬────────┘    │
    │           │             │              │           │             │
    │  ┌────────▼────────┐    │              │  ┌────────▼────────┐    │
    │  │     Chapter     │    │              │  │  HighlightTag   │    │
    │  └─────────────────┘    │              │  └─────────────────┘    │
    │           │             │              │                         │
    │  ┌────────▼────────┐    │              │  ┌─────────────────┐    │
    │  │     BookTag     │    │   BookId     │  │ ReadingSession  │    │
    │  └─────────────────┘    │<─────────────┼──│   (Aggregate)   │    │
    │                         │              │  └─────────────────┘    │
    └─────────────────────────┘              │                         │
              ▲                              │  ┌─────────────────┐    │
              │                              │  │    Bookmark     │    │
              │ BookId                       │  │   (Aggregate)   │    │
              │                              │  └─────────────────┘    │
    ┌─────────┴───────────────┐              └─────────────────────────┘
    │    LEARNING CONTEXT     │                          │
    │                         │                          │
    │  ┌─────────────────┐    │      HighlightId         │
    │  │    Flashcard    │<───┼──────────────────────────┘
    │  │   (Aggregate)   │    │
    │  └─────────────────┘    │
    │                         │
    └─────────────────────────┘


    ┌─────────────────────────┐
    │   IDENTITY CONTEXT      │
    │                         │
    │  ┌─────────────────┐    │         Provides UserId to all contexts
    │  │      User       │────┼────────────────────────────────────────>
    │  │   (Aggregate)   │    │
    │  └─────────────────┘    │
    │                         │
    └─────────────────────────┘


    RELATIONSHIP TYPES:
    ─────────────────────
    ────────────> : Shared Kernel (same ID type)
    - - - - - -> : Customer/Supplier (downstream uses upstream's ID)
```

---

## 8. Migration Roadmap

### Phase 0: Preparation (Foundation)

**Goal:** Set up infrastructure for gradual migration without breaking existing code.

| Step | Task | Effort |
|------|------|--------|
| 0.1 | Create new directory structure alongside existing code | Small |
| 0.2 | Set up import linting rules (e.g., `import-linter`) | Small |
| 0.3 | Create base classes for domain (Entity, ValueObject, AggregateRoot) | Small |
| 0.4 | Create base use case and result types | Small |
| 0.5 | Set up dependency injection container (e.g., `punq` or manual) | Medium |

**Deliverable:** Parallel directory structure ready for migration.

---

### Phase 1: Domain Layer - Value Objects

**Goal:** Extract and encapsulate core business concepts as Value Objects.

| Step | Task | Priority |
|------|------|----------|
| 1.1 | Create `BookId`, `HighlightId`, `UserId`, etc. (typed IDs) | High |
| 1.2 | Create `ContentHash` value object with compute logic | High |
| 1.3 | Create `XPoint` and `XPointRange` value objects | High |
| 1.4 | Create `TimeRange` and `PageRange` value objects | Medium |
| 1.5 | Create `HighlightText` with validation | Medium |
| 1.6 | Create `Email` and `Password` value objects | Medium |

**Deliverable:** Reusable, validated value objects in `domain/*/value_objects/`.

---

### Phase 2: Domain Layer - Entities & Aggregates

**Goal:** Create rich domain entities with behavior.

| Step | Task | Priority |
|------|------|----------|
| 2.1 | Create `Highlight` aggregate root with domain logic | High |
| 2.2 | Create `Book` aggregate root with chapters | High |
| 2.3 | Create `ReadingSession` aggregate root | High |
| 2.4 | Create `Flashcard` aggregate root | Medium |
| 2.5 | Create `User` aggregate root | Medium |
| 2.6 | Create domain services (DeduplicationService, etc.) | Medium |
| 2.7 | Define repository interfaces (Protocols) in domain layer | High |

**Deliverable:** Rich domain model with encapsulated business logic.

---

### Phase 3: Infrastructure Layer - Persistence

**Goal:** Separate ORM models from domain and create mappers.

| Step | Task | Priority |
|------|------|----------|
| 3.1 | Split `models.py` into separate ORM model files | High |
| 3.2 | Rename ORM models (e.g., `Book` → `BookORM`) | High |
| 3.3 | Create mappers (`BookMapper.to_domain()`, `.to_orm()`) | High |
| 3.4 | Implement `PostgresHighlightRepository` | High |
| 3.5 | Implement `PostgresBookRepository` | High |
| 3.6 | Implement remaining repositories | Medium |
| 3.7 | Implement Unit of Work pattern | Medium |

**Deliverable:** Clean separation between domain entities and ORM models.

---

### Phase 4: Application Layer - Use Cases

**Goal:** Create use cases that orchestrate domain logic.

| Step | Task | Priority |
|------|------|----------|
| 4.1 | Create `UploadHighlightsUseCase` (command) | High |
| 4.2 | Create `CreateBookUseCase` (command) | High |
| 4.3 | Create `GetBookHighlightsQuery` (query) | High |
| 4.4 | Create `SearchHighlightsQuery` (query) | High |
| 4.5 | Create `RecordReadingSessionUseCase` | Medium |
| 4.6 | Create remaining use cases | Medium |
| 4.7 | Create application DTOs | Medium |

**Deliverable:** Framework-agnostic use cases with clear input/output contracts.

---

### Phase 5: Infrastructure Layer - External Ports

**Goal:** Abstract external dependencies behind ports.

| Step | Task | Priority |
|------|------|----------|
| 5.1 | Define `FileStoragePort` interface | High |
| 5.2 | Implement `LocalFileStorage` adapter | High |
| 5.3 | Define `EbookParserPort` interface | High |
| 5.4 | Implement `EpubParser` adapter | High |
| 5.5 | Define `AIServicePort` interface | Medium |
| 5.6 | Implement AI adapters (OpenAI, Anthropic) | Medium |
| 5.7 | Define `SearchIndexPort` interface | Medium |
| 5.8 | Implement PostgreSQL FTS adapter | Medium |

**Deliverable:** All external dependencies abstracted behind ports.

---

### Phase 6: Infrastructure Layer - HTTP Adapters

**Goal:** Refactor routers to use use cases instead of services.

| Step | Task | Priority |
|------|------|----------|
| 6.1 | Refactor highlights router to use `UploadHighlightsUseCase` | High |
| 6.2 | Refactor books router to use book use cases | High |
| 6.3 | Refactor reading sessions router | Medium |
| 6.4 | Refactor remaining routers | Medium |
| 6.5 | Update dependency injection in `main.py` | High |
| 6.6 | Update error handling middleware | Medium |

**Deliverable:** All HTTP endpoints using use cases.

---

### Phase 7: Cleanup & Testing

**Goal:** Remove old code and ensure comprehensive test coverage.

| Step | Task | Priority |
|------|------|----------|
| 7.1 | Remove old service classes | High |
| 7.2 | Remove old repository implementations | High |
| 7.3 | Archive original `models.py` (then delete) | High |
| 7.4 | Write unit tests for value objects | High |
| 7.5 | Write unit tests for domain entities | High |
| 7.6 | Write unit tests for use cases (with mocked ports) | High |
| 7.7 | Write integration tests for adapters | Medium |
| 7.8 | Update e2e tests | Medium |

**Deliverable:** Clean codebase with comprehensive test coverage.

---

### Phase 8: Advanced Features (Optional)

**Goal:** Add advanced DDD patterns for future scalability.

| Step | Task | Priority |
|------|------|----------|
| 8.1 | Implement domain events | Low |
| 8.2 | Add event handlers for cross-context communication | Low |
| 8.3 | Consider CQRS for read-heavy operations | Low |
| 8.4 | Add caching layer via ports | Low |
| 8.5 | Consider event sourcing for audit trails | Low |

---

### Migration Timeline Visualization

```
Phase 0 ─────────┐
(Preparation)    │
                 ▼
Phase 1 ─────────┐
(Value Objects)  │
                 ▼
Phase 2 ─────────┬─────────────────────────────────────────────────────┐
(Domain Model)   │                                                      │
                 ▼                                                      │
Phase 3 ─────────┐                                                      │
(Persistence)    │  These phases can be done                           │
                 │  incrementally, one aggregate at a time             │
Phase 4 ─────────┤                                                      │
(Use Cases)      │                                                      │
                 ▼                                                      │
Phase 5 ─────────┐                                                      │
(External Ports) │                                                      │
                 ▼                                                      │
Phase 6 ─────────┘◄─────────────────────────────────────────────────────┘
(HTTP Adapters)
                 │
                 ▼
Phase 7 ─────────┐
(Cleanup/Tests)  │
                 ▼
Phase 8 ─────────┐
(Advanced)       │
                 ▼
              COMPLETE
```

---

## 9. Implementation Guidelines

### 9.1 Domain Entity Best Practices

```python
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Self

@dataclass
class Highlight:
    """
    Highlight aggregate root.

    Rules:
    - All state changes go through methods (not direct assignment)
    - Validation happens in factory methods and setters
    - No infrastructure dependencies
    """
    id: HighlightId
    user_id: UserId
    book_id: BookId
    text: HighlightText
    content_hash: ContentHash
    created_at: datetime
    _deleted_at: datetime | None = field(default=None, repr=False)
    _tags: list[HighlightTag] = field(default_factory=list)

    # Expose read-only properties
    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def tags(self) -> list[HighlightTag]:
        return self._tags.copy()  # Return copy to prevent external mutation

    # All mutations through methods
    def soft_delete(self) -> None:
        if self._deleted_at is not None:
            raise HighlightAlreadyDeleted(self.id)
        self._deleted_at = datetime.now(UTC)

    # Factory method for creation
    @classmethod
    def create(cls, user_id: UserId, book_id: BookId, text: str) -> Self:
        return cls(
            id=HighlightId.generate(),
            user_id=user_id,
            book_id=book_id,
            text=HighlightText(text),
            content_hash=ContentHash.compute(text),
            created_at=datetime.now(UTC),
        )
```

### 9.2 Use Case Pattern

```python
from dataclasses import dataclass
from typing import Protocol

# Input DTO (Command)
@dataclass(frozen=True)
class UploadHighlightsCommand:
    user_id: int
    book_id: int
    highlights: list[HighlightData]

# Output DTO
@dataclass(frozen=True)
class UploadHighlightsResult:
    created_count: int
    duplicate_count: int
    created_ids: list[int]

# Use Case Interface (Port)
class UploadHighlightsUseCase(Protocol):
    def execute(self, command: UploadHighlightsCommand) -> UploadHighlightsResult:
        ...

# Use Case Implementation
class UploadHighlightsHandler:
    """
    Application service that orchestrates highlight upload.

    Dependencies are injected via constructor (ports).
    """
    def __init__(
        self,
        highlight_repo: HighlightRepository,
        book_repo: BookRepository,
        dedup_service: HighlightDeduplicationService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._highlight_repo = highlight_repo
        self._book_repo = book_repo
        self._dedup_service = dedup_service
        self._uow = unit_of_work

    def execute(self, command: UploadHighlightsCommand) -> UploadHighlightsResult:
        user_id = UserId(command.user_id)
        book_id = BookId(command.book_id)

        # Verify book exists
        book = self._book_repo.find_by_id(book_id, user_id)
        if book is None:
            raise BookNotFound(book_id)

        # Get existing hashes for deduplication
        existing_hashes = self._highlight_repo.find_existing_hashes(
            book_id, user_id
        )

        # Create domain entities
        highlights = [
            Highlight.create(user_id, book_id, h.text)
            for h in command.highlights
        ]

        # Apply domain logic (deduplication)
        unique, duplicates = self._dedup_service.find_duplicates(
            highlights, existing_hashes
        )

        # Persist through repository
        with self._uow:
            self._highlight_repo.save_all(unique)
            self._uow.commit()

        return UploadHighlightsResult(
            created_count=len(unique),
            duplicate_count=len(duplicates),
            created_ids=[h.id.value for h in unique],
        )
```

### 9.3 Mapper Pattern

```python
class HighlightMapper:
    """
    Maps between domain Highlight and ORM HighlightORM.

    Keeps domain model decoupled from persistence.
    """

    def to_domain(self, orm: HighlightORM) -> Highlight:
        """Convert ORM model to domain entity."""
        return Highlight(
            id=HighlightId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            text=HighlightText(orm.text),
            content_hash=ContentHash(orm.content_hash),
            created_at=orm.created_at,
            _deleted_at=orm.deleted_at,
            _tags=[
                HighlightTag(
                    id=HighlightTagId(t.id),
                    name=TagName(t.name),
                )
                for t in orm.tags
            ],
        )

    def to_orm(self, entity: Highlight) -> HighlightORM:
        """Convert domain entity to ORM model."""
        return HighlightORM(
            id=entity.id.value,
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            text=entity.text.value,
            content_hash=entity.content_hash.value,
            created_at=entity.created_at,
            deleted_at=entity.deleted_at,
            # Tags handled separately via association
        )
```

### 9.4 Dependency Injection Setup

```python
# infrastructure/api/dependencies.py

from functools import lru_cache
from sqlalchemy.orm import Session

def get_highlight_repository(session: Session) -> HighlightRepository:
    """Factory for highlight repository."""
    return PostgresHighlightRepository(session)

def get_upload_highlights_use_case(
    session: Session = Depends(get_db_session),
) -> UploadHighlightsHandler:
    """Factory for upload highlights use case."""
    return UploadHighlightsHandler(
        highlight_repo=PostgresHighlightRepository(session),
        book_repo=PostgresBookRepository(session),
        dedup_service=HighlightDeduplicationService(),
        unit_of_work=SQLAlchemyUnitOfWork(session),
    )

# In router:
@router.post("/upload")
async def upload_highlights(
    request: HighlightUploadRequest,
    user: CurrentUser,
    use_case: UploadHighlightsHandler = Depends(get_upload_highlights_use_case),
) -> HighlightUploadResponse:
    result = use_case.execute(
        UploadHighlightsCommand(
            user_id=user.id,
            book_id=request.book_id,
            highlights=request.highlights,
        )
    )
    return HighlightUploadResponse(
        created=result.created_count,
        duplicates=result.duplicate_count,
    )
```

### 9.5 Testing Strategy

```python
# Unit test for domain entity (no mocks needed)
def test_highlight_soft_delete():
    highlight = Highlight.create(
        user_id=UserId(1),
        book_id=BookId(1),
        text="Test highlight",
    )

    assert highlight.deleted_at is None
    highlight.soft_delete()
    assert highlight.deleted_at is not None

# Unit test for use case (with mocked ports)
def test_upload_highlights_deduplicates():
    # Arrange
    mock_highlight_repo = Mock(spec=HighlightRepository)
    mock_highlight_repo.find_existing_hashes.return_value = {
        ContentHash("existing_hash")
    }

    handler = UploadHighlightsHandler(
        highlight_repo=mock_highlight_repo,
        book_repo=Mock(spec=BookRepository),
        dedup_service=HighlightDeduplicationService(),
        unit_of_work=Mock(spec=UnitOfWork),
    )

    # Act
    result = handler.execute(UploadHighlightsCommand(...))

    # Assert
    assert result.duplicate_count == 1
```

---

## Summary

This migration plan transforms the Crossbill backend from a traditional layered architecture to a Domain-Driven Design approach using Hexagonal Architecture. The key benefits are:

1. **Testability:** Domain logic can be tested without infrastructure
2. **Flexibility:** External dependencies can be swapped via ports
3. **Maintainability:** Clear boundaries between contexts
4. **Evolvability:** New features are easier to add in isolation
5. **Business Focus:** Domain logic is explicit and centralized

The migration is designed to be incremental, allowing the team to migrate one aggregate at a time while maintaining a working system throughout the process.

---

## References

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Implementing Domain-Driven Design by Vaughn Vernon](https://vaughnvernon.com/books/)
- [Hexagonal Architecture by Alistair Cockburn](https://alistair.cockburn.us/hexagonal-architecture/)
- [Clean Architecture by Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Cosmic Python (Architecture Patterns with Python)](https://www.cosmicpython.com/)
