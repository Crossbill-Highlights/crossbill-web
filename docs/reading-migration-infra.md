# DETAILED MIGRATION GUIDE: Reading Module Phase 3 - Infrastructure Layer

This guide provides step-by-step instructions for implementing the infrastructure layer (repositories, mappers, Unit of Work) for the Reading module using ports & adapters (hexagonal) architecture within a modular monolith.

## Architecture Overview

### Ports & Adapters in a Modular Monolith

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP Layer (FastAPI)                    │
│                    routers/highlights.py                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                     Application Layer                        │
│         use_cases/upload_highlights_use_case.py             │
│              (Depends on Repository Ports)                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
┌───────────────▼──────────┐  ┌─────────▼──────────────────┐
│     Domain Layer         │  │  Application Ports         │
│  entities/highlight.py   │  │  IHighlightRepository      │
│  entities/reading_session│  │  IUnitOfWork               │
│  services/deduplication  │  │  (Interfaces only)         │
└──────────────────────────┘  └────────┬───────────────────┘
                                       │
                         ┌─────────────▼──────────────────┐
                         │   Infrastructure Layer         │
                         │   (Adapters - Implementations) │
                         │                                │
                         │  PostgresHighlightRepository   │
                         │  SqlAlchemyUnitOfWork          │
                         │  HighlightMapper               │
                         │                                │
                         │  ORM Models (models.py)        │
                         └────────────────────────────────┘
```

### Key Principles

1. **Shared Database**: All modules use the same SQLAlchemy `Base` and database connection
2. **Separate Repositories**: Each module has its own repository implementations but shares ORM models
3. **One Migration Chain**: Database schema changes go through a single Alembic migration chain
4. **Port Interfaces**: Application layer depends on interfaces, not implementations
5. **Domain Independence**: Domain layer has zero infrastructure dependencies

---

## Prerequisites

- ✅ Phase 1 complete: Value objects (HighlightId, XPoint, ContentHash, etc.)
- ✅ Phase 2 complete: Domain entities (Highlight, ReadingSession, HighlightTag)
- ✅ Existing SQLAlchemy models in `backend/src/models.py`
- ✅ Existing database setup in `backend/src/database.py`

---

## PHASE 3: Infrastructure Layer (10-15 hours)

### Goal

Create infrastructure adapters that implement repository ports, handle ORM mapping, and manage transactions while maintaining compatibility with existing code.

---

## Step 3.1: Create Repository Port Interfaces

Repository ports define what the application layer needs from persistence without coupling to implementation details.

### File: `backend/src/application/ports/persistence.py`

```python
"""
Persistence port interfaces for the application layer.

These are abstract interfaces that define what the application needs
from the infrastructure layer without depending on specific implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Set
from datetime import datetime

from src.domain.common.value_objects import (
    HighlightId,
    BookId,
    UserId,
    ContentHash,
    ReadingSessionId,
    HighlightTagId,
)
from src.domain.reading.entities import Highlight, ReadingSession, HighlightTag


class IHighlightRepository(ABC):
    """
    Port for highlight persistence operations.

    The application layer depends on this interface.
    The infrastructure layer provides implementations.
    """

    @abstractmethod
    def add(self, highlight: Highlight) -> Highlight:
        """
        Add a new highlight to the repository.

        Args:
            highlight: Domain entity to persist

        Returns:
            Highlight with database-assigned ID
        """
        pass

    @abstractmethod
    def add_many(self, highlights: List[Highlight]) -> List[Highlight]:
        """
        Bulk add multiple highlights efficiently.

        Args:
            highlights: List of domain services to persist

        Returns:
            Highlights with database-assigned IDs
        """
        pass

    @abstractmethod
    def get_by_id(self, highlight_id: HighlightId) -> Optional[Highlight]:
        """
        Retrieve highlight by ID.

        Args:
            highlight_id: Highlight identifier

        Returns:
            Highlight entity or None if not found
        """
        pass

    @abstractmethod
    def get_by_book(
        self,
        user_id: UserId,
        book_id: BookId,
        include_deleted: bool = False,
    ) -> List[Highlight]:
        """
        Get all highlights for a book.

        Args:
            user_id: User who owns the highlights
            book_id: Book identifier
            include_deleted: Whether to include soft-deleted highlights

        Returns:
            List of highlight services
        """
        pass

    @abstractmethod
    def get_existing_hashes(
        self,
        user_id: UserId,
        book_id: BookId,
    ) -> Set[ContentHash]:
        """
        Get all existing content hashes for a user's book.

        Used for deduplication before bulk insert.

        Args:
            user_id: User identifier
            book_id: Book identifier

        Returns:
            Set of content hashes that already exist
        """
        pass

    @abstractmethod
    def update(self, highlight: Highlight) -> Highlight:
        """
        Update an existing highlight.

        Args:
            highlight: Domain entity with changes

        Returns:
            Updated highlight
        """
        pass

    @abstractmethod
    def delete(self, highlight_id: HighlightId) -> None:
        """
        Hard delete a highlight.

        Args:
            highlight_id: Highlight to delete
        """
        pass

    @abstractmethod
    def search_by_text(
        self,
        user_id: UserId,
        query: str,
        book_id: Optional[BookId] = None,
        limit: int = 50,
    ) -> List[Highlight]:
        """
        Full-text search across highlight text.

        Args:
            user_id: User performing search
            query: Search query string
            book_id: Optional filter by book
            limit: Maximum results

        Returns:
            List of matching highlights
        """
        pass


class IReadingSessionRepository(ABC):
    """Port for reading session persistence operations."""

    @abstractmethod
    def add(self, session: ReadingSession) -> ReadingSession:
        """Add a new reading session."""
        pass

    @abstractmethod
    def add_many(self, sessions: List[ReadingSession]) -> List[ReadingSession]:
        """Bulk add multiple reading sessions."""
        pass

    @abstractmethod
    def get_by_id(self, session_id: ReadingSessionId) -> Optional[ReadingSession]:
        """Retrieve session by ID."""
        pass

    @abstractmethod
    def get_by_book(
        self,
        user_id: UserId,
        book_id: BookId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ReadingSession]:
        """
        Get reading sessions for a book within optional date range.

        Args:
            user_id: User who owns the sessions
            book_id: Book identifier
            start_date: Optional filter sessions after this date
            end_date: Optional filter sessions before this date

        Returns:
            List of reading session services
        """
        pass

    @abstractmethod
    def get_existing_hashes(
        self,
        user_id: UserId,
        book_id: BookId,
    ) -> Set[ContentHash]:
        """Get existing content hashes for deduplication."""
        pass

    @abstractmethod
    def update(self, session: ReadingSession) -> ReadingSession:
        """Update an existing reading session."""
        pass


class IHighlightTagRepository(ABC):
    """Port for highlight tag persistence operations."""

    @abstractmethod
    def add(self, tag: HighlightTag) -> HighlightTag:
        """Add a new highlight tag."""
        pass

    @abstractmethod
    def get_by_id(self, tag_id: HighlightTagId) -> Optional[HighlightTag]:
        """Retrieve tag by ID."""
        pass

    @abstractmethod
    def get_by_book(self, user_id: UserId, book_id: BookId) -> List[HighlightTag]:
        """Get all tags for a book."""
        pass

    @abstractmethod
    def get_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        name: str,
        group_name: Optional[str] = None,
    ) -> HighlightTag:
        """
        Get existing tag by name or create if doesn't exist.

        Args:
            user_id: User who owns the tag
            book_id: Book the tag belongs to
            name: Tag name
            group_name: Optional group name

        Returns:
            Existing or newly created tag
        """
        pass

    @abstractmethod
    def delete(self, tag_id: HighlightTagId) -> None:
        """Delete a tag."""
        pass
```

**File: `backend/src/application/ports/__init__.py`**

```python
"""Application layer ports (interfaces for external dependencies)."""
from .persistence import (
    IHighlightRepository,
    IReadingSessionRepository,
    IHighlightTagRepository,
)

__all__ = [
    "IHighlightRepository",
    "IReadingSessionRepository",
    "IHighlightTagRepository",
]
```

**Action:**

1. Create directory: `mkdir -p backend/src/application/ports`
2. Create the persistence port interfaces
3. Verify imports: `python -c "from backend.src.application.ports import IHighlightRepository"`

---

## Step 3.2: Create Unit of Work Port and Implementation

The Unit of Work pattern manages transactions and ensures all repository operations within a use case either succeed or fail together.

### File: `backend/src/application/ports/unit_of_work.py`

```python
"""
Unit of Work port for transaction management.

Updated from the existing stub to be more specific to our needs.
"""
from abc import ABC, abstractmethod
from typing import Protocol

from .persistence import (
    IHighlightRepository,
    IReadingSessionRepository,
    IHighlightTagRepository,
)


class IUnitOfWork(ABC):
    """
    Unit of Work port for managing database transactions.

    This interface ensures that all repository operations within
    a use case are committed or rolled back together.

    Usage:
        with uow:
            highlight = uow.highlights.add(highlight)
            uow.commit()
    """

    # Repository instances (lazy-loaded)
    highlights: IHighlightRepository
    reading_sessions: IReadingSessionRepository
    highlight_tags: IHighlightTagRepository

    @abstractmethod
    def __enter__(self) -> "IUnitOfWork":
        """Start a transaction context."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End transaction context, rollback on exception."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
```

### File: `backend/src/infrastructure/persistence/unit_of_work.py`

```python
"""
SQLAlchemy Unit of Work implementation.

Manages database transactions and provides access to repositories.
"""
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from src.application.ports.unit_of_work import IUnitOfWork
from .repositories import (
    PostgresHighlightRepository,
    PostgresReadingSessionRepository,
    PostgresHighlightTagRepository,
)

if TYPE_CHECKING:
    from src.application.ports.persistence import (
        IHighlightRepository,
        IReadingSessionRepository,
        IHighlightTagRepository,
    )


class SqlAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work.

    Manages a database session and provides access to repositories.
    All repository operations share the same session and transaction.
    """

    def __init__(self, session_factory) -> None:
        """
        Initialize Unit of Work with a session factory.

        Args:
            session_factory: SQLAlchemy sessionmaker
        """
        self.session_factory = session_factory
        self._session: Session | None = None

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        """Start a new database session."""
        self._session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close session, rollback if exception occurred."""
        if exc_type is not None:
            self.rollback()

        if self._session:
            self._session.close()

    @property
    def highlights(self) -> "IHighlightRepository":
        """Get highlight repository for this unit of work."""
        if self._session is None:
            raise RuntimeError("Unit of Work not started. Use 'with uow:' context.")
        return PostgresHighlightRepository(self._session)

    @property
    def reading_sessions(self) -> "IReadingSessionRepository":
        """Get reading session repository for this unit of work."""
        if self._session is None:
            raise RuntimeError("Unit of Work not started. Use 'with uow:' context.")
        return PostgresReadingSessionRepository(self._session)

    @property
    def highlight_tags(self) -> "IHighlightTagRepository":
        """Get highlight tag repository for this unit of work."""
        if self._session is None:
            raise RuntimeError("Unit of Work not started. Use 'with uow:' context.")
        return PostgresHighlightTagRepository(self._session)

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._session is None:
            raise RuntimeError("Unit of Work not started.")
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session is None:
            raise RuntimeError("Unit of Work not started.")
        self._session.rollback()
```

**Action:**

1. Update `backend/src/application/ports/unit_of_work.py` (or create if doesn't exist)
2. Create directory: `mkdir -p backend/src/infrastructure/persistence`
3. Create `backend/src/infrastructure/persistence/unit_of_work.py`

---

## Step 3.3: Create Domain-to-ORM Mappers

Mappers translate between domain entities (rich objects with behavior) and ORM models (database representations).

### File: `backend/src/infrastructure/persistence/mappers/highlight_mapper.py`

```python
"""
Mapper for converting between Highlight domain services and ORM models.

This adapter layer translates domain objects to/from database representations.
"""
from typing import Optional

from src.domain.reading.entities import Highlight
from src.domain.common.value_objects import (
    HighlightId,
    UserId,
    BookId,
    ChapterId,
    ContentHash,
    XPoint,
    XPointRange,
)
from src.domain.reading.value_objects import HighlightText
from src.models import Highlight as HighlightORM
from datetime import datetime


class HighlightMapper:
    """
    Maps between Highlight domain entity and HighlightORM model.

    Responsibilities:
    - Convert domain services to ORM models for persistence
    - Reconstitute domain services from ORM models
    - Handle value object serialization/deserialization
    """

    @staticmethod
    def to_domain(orm: HighlightORM) -> Highlight:
        """
        Convert ORM model to domain entity.

        Args:
            orm: SQLAlchemy model instance

        Returns:
            Domain entity with reconstructed value objects
        """
        # Parse XPoint range if present
        xpoints: Optional[XPointRange] = None
        if orm.start_xpoint and orm.end_xpoint:
            try:
                xpoints = XPointRange.parse(orm.start_xpoint, orm.end_xpoint)
            except Exception:
                # Invalid xpoint data - ignore
                xpoints = None

        # Reconstruct domain entity using factory method
        return Highlight.create_with_id(
            id=HighlightId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            text=orm.text,
            content_hash=ContentHash(orm.content_hash),
            created_at=orm.created_at,
            chapter_id=ChapterId(orm.chapter_id) if orm.chapter_id else None,
            xpoints=xpoints,
            page=orm.page,
            note=orm.note,
            deleted_at=orm.deleted_at,
        )

    @staticmethod
    def to_orm(entity: Highlight) -> HighlightORM:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Domain entity

        Returns:
            SQLAlchemy model ready for persistence

        Note:
            If entity.id.value is 0, the ORM model will get a new ID from database.
        """
        # Serialize XPoint range
        start_xpoint: Optional[str] = None
        end_xpoint: Optional[str] = None
        if entity.xpoints:
            start_xpoint = entity.xpoints.start.to_string()
            end_xpoint = entity.xpoints.end.to_string()

        # Create ORM model
        orm = HighlightORM(
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            text=str(entity.text),
            content_hash=entity.content_hash.value,
            chapter_id=entity.chapter_id.value if entity.chapter_id else None,
            page=entity.page,
            note=entity.note,
            start_xpoint=start_xpoint,
            end_xpoint=end_xpoint,
            datetime=entity.created_at.isoformat(),  # KOReader format
            created_at=entity.created_at,
            deleted_at=entity.deleted_at,
        )

        # Set ID if entity has been persisted (not generated placeholder)
        if entity.id.value != 0:
            orm.id = entity.id.value

        return orm

    @staticmethod
    def update_orm_from_entity(orm: HighlightORM, entity: Highlight) -> None:
        """
        Update existing ORM model with values from domain entity.

        Used for updating persisted services.

        Args:
            orm: Existing ORM model to update
            entity: Domain entity with new values
        """
        orm.note = entity.note
        orm.deleted_at = entity.deleted_at
        orm.page = entity.page

        # Update xpoints if changed
        if entity.xpoints:
            orm.start_xpoint = entity.xpoints.start.to_string()
            orm.end_xpoint = entity.xpoints.end.to_string()
        else:
            orm.start_xpoint = None
            orm.end_xpoint = None

        # Update chapter association
        orm.chapter_id = entity.chapter_id.value if entity.chapter_id else None
```

### File: `backend/src/infrastructure/persistence/mappers/reading_session_mapper.py`

```python
"""
Mapper for ReadingSession domain entity and ORM model.
"""
from typing import Optional

from src.domain.reading.entities import ReadingSession
from src.domain.common.value_objects import (
    ReadingSessionId,
    UserId,
    BookId,
    ContentHash,
    XPoint,
    XPointRange,
)
from src.models import ReadingSession as ReadingSessionORM


class ReadingSessionMapper:
    """Maps between ReadingSession domain entity and ReadingSessionORM."""

    @staticmethod
    def to_domain(orm: ReadingSessionORM) -> ReadingSession:
        """Convert ORM model to domain entity."""
        # Parse start XPoint if present
        start_xpoint: Optional[XPointRange] = None
        if orm.start_xpoint and orm.end_xpoint:
            try:
                start_xpoint = XPointRange.parse(orm.start_xpoint, orm.end_xpoint)
            except Exception:
                start_xpoint = None

        return ReadingSession.create_with_id(
            id=ReadingSessionId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            start_time=orm.start_time,
            end_time=orm.end_time,
            content_hash=ContentHash(orm.content_hash),
            start_xpoint=start_xpoint,
            start_page=orm.start_page,
            end_page=orm.end_page,
            device_id=orm.device_id,
            ai_summary=orm.ai_summary,
        )

    @staticmethod
    def to_orm(entity: ReadingSession) -> ReadingSessionORM:
        """Convert domain entity to ORM model."""
        # Serialize start XPoint
        start_xpoint: Optional[str] = None
        end_xpoint: Optional[str] = None
        if entity.start_xpoint:
            start_xpoint = entity.start_xpoint.start.to_string()
            end_xpoint = entity.start_xpoint.end.to_string()

        orm = ReadingSessionORM(
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            start_time=entity.start_time,
            end_time=entity.end_time,
            content_hash=entity.content_hash.value,
            start_xpoint=start_xpoint,
            end_xpoint=end_xpoint,
            start_page=entity.start_page,
            end_page=entity.end_page,
            device_id=entity.device_id,
            ai_summary=entity.ai_summary,
        )

        if entity.id.value != 0:
            orm.id = entity.id.value

        return orm

    @staticmethod
    def update_orm_from_entity(orm: ReadingSessionORM, entity: ReadingSession) -> None:
        """Update existing ORM model from domain entity."""
        orm.ai_summary = entity.ai_summary

        # Update xpoints if changed
        if entity.start_xpoint:
            orm.start_xpoint = entity.start_xpoint.start.to_string()
            orm.end_xpoint = entity.start_xpoint.end.to_string()
```

### File: `backend/src/infrastructure/persistence/mappers/highlight_tag_mapper.py`

```python
"""
Mapper for HighlightTag domain entity and ORM model.
"""
from typing import Optional

from src.domain.reading.entities import HighlightTag
from src.domain.common.value_objects import (
    HighlightTagId,
    UserId,
    BookId,
)
from src.models import HighlightTag as HighlightTagORM


class HighlightTagMapper:
    """Maps between HighlightTag domain entity and HighlightTagORM."""

    @staticmethod
    def to_domain(orm: HighlightTagORM) -> HighlightTag:
        """Convert ORM model to domain entity."""
        # Note: group_name comes from tag_group relationship
        group_name: Optional[str] = None
        if orm.tag_group:
            group_name = orm.tag_group.name

        return HighlightTag(
            id=HighlightTagId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            name=orm.name,
            group_name=group_name,
        )

    @staticmethod
    def to_orm(entity: HighlightTag) -> HighlightTagORM:
        """Convert domain entity to ORM model."""
        orm = HighlightTagORM(
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            name=entity.name,
            # Note: tag_group_id must be set separately via repository
        )

        if entity.id.value != 0:
            orm.id = entity.id.value

        return orm
```

### File: `backend/src/infrastructure/persistence/mappers/__init__.py`

```python
"""ORM-to-Domain mappers."""
from .highlight_mapper import HighlightMapper
from .reading_session_mapper import ReadingSessionMapper
from .highlight_tag_mapper import HighlightTagMapper

__all__ = [
    "HighlightMapper",
    "ReadingSessionMapper",
    "HighlightTagMapper",
]
```

**Action:**

1. Create directory: `mkdir -p backend/src/infrastructure/persistence/mappers`
2. Create all mapper files
3. Test basic mapping: Create unit tests for each mapper

---

## Step 3.4: Implement Repository Adapters

Repository adapters implement the port interfaces using SQLAlchemy ORM and mappers.

### File: `backend/src/infrastructure/persistence/repositories/highlight_repository.py`

```python
"""
PostgreSQL implementation of Highlight repository.

This adapter implements the IHighlightRepository port using SQLAlchemy.
"""
from typing import List, Optional, Set

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload

from src.application.ports.persistence import IHighlightRepository
from src.domain.reading.entities import Highlight
from src.domain.common.value_objects import (
    HighlightId,
    BookId,
    UserId,
    ContentHash,
)
from src.models import Highlight as HighlightORM
from ..mappers import HighlightMapper


class PostgresHighlightRepository(IHighlightRepository):
    """
    SQLAlchemy-based implementation of highlight repository.

    Responsibilities:
    - Translate domain operations to SQL queries
    - Use mapper to convert between domain and ORM models
    - Handle database-specific concerns (pagination, full-text search)
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session (from Unit of Work)
        """
        self.session = session
        self.mapper = HighlightMapper()

    def add(self, highlight: Highlight) -> Highlight:
        """
        Add a single highlight.

        Args:
            highlight: Domain entity to persist

        Returns:
            Highlight with database-assigned ID
        """
        orm = self.mapper.to_orm(highlight)
        self.session.add(orm)
        self.session.flush()  # Get ID without committing

        # Update domain entity with new ID
        return self.mapper.to_domain(orm)

    def add_many(self, highlights: List[Highlight]) -> List[Highlight]:
        """
        Bulk insert highlights efficiently.

        Args:
            highlights: List of domain services

        Returns:
            Highlights with database-assigned IDs
        """
        orms = [self.mapper.to_orm(h) for h in highlights]
        self.session.add_all(orms)
        self.session.flush()  # Assign IDs

        return [self.mapper.to_domain(orm) for orm in orms]

    def get_by_id(self, highlight_id: HighlightId) -> Optional[Highlight]:
        """
        Retrieve highlight by ID.

        Args:
            highlight_id: Highlight identifier

        Returns:
            Domain entity or None
        """
        stmt = select(HighlightORM).where(HighlightORM.id == highlight_id.value)
        orm = self.session.execute(stmt).scalar_one_or_none()

        if orm is None:
            return None

        return self.mapper.to_domain(orm)

    def get_by_book(
        self,
        user_id: UserId,
        book_id: BookId,
        include_deleted: bool = False,
    ) -> List[Highlight]:
        """
        Get all highlights for a book.

        Args:
            user_id: User who owns highlights
            book_id: Book identifier
            include_deleted: Whether to include soft-deleted highlights

        Returns:
            List of domain services
        """
        stmt = (
            select(HighlightORM)
            .where(HighlightORM.user_id == user_id.value)
            .where(HighlightORM.book_id == book_id.value)
        )

        if not include_deleted:
            stmt = stmt.where(HighlightORM.deleted_at.is_(None))

        # Order by creation time
        stmt = stmt.order_by(HighlightORM.created_at)

        orms = self.session.execute(stmt).scalars().all()

        return [self.mapper.to_domain(orm) for orm in orms]

    def get_existing_hashes(
        self,
        user_id: UserId,
        book_id: BookId,
    ) -> Set[ContentHash]:
        """
        Get all existing content hashes for deduplication.

        Args:
            user_id: User identifier
            book_id: Book identifier

        Returns:
            Set of content hashes
        """
        stmt = (
            select(HighlightORM.content_hash)
            .where(HighlightORM.user_id == user_id.value)
            .where(HighlightORM.book_id == book_id.value)
            .where(HighlightORM.deleted_at.is_(None))  # Don't count deleted
        )

        hashes = self.session.execute(stmt).scalars().all()

        return {ContentHash(h) for h in hashes}

    def update(self, highlight: Highlight) -> Highlight:
        """
        Update existing highlight.

        Args:
            highlight: Domain entity with changes

        Returns:
            Updated highlight
        """
        # Load existing ORM object
        orm = self.session.get(HighlightORM, highlight.id.value)

        if orm is None:
            raise ValueError(f"Highlight {highlight.id.value} not found")

        # Update ORM from domain entity
        self.mapper.update_orm_from_entity(orm, highlight)
        self.session.flush()

        return self.mapper.to_domain(orm)

    def delete(self, highlight_id: HighlightId) -> None:
        """
        Hard delete a highlight.

        Args:
            highlight_id: Highlight to delete
        """
        stmt = select(HighlightORM).where(HighlightORM.id == highlight_id.value)
        orm = self.session.execute(stmt).scalar_one_or_none()

        if orm:
            self.session.delete(orm)
            self.session.flush()

    def search_by_text(
        self,
        user_id: UserId,
        query: str,
        book_id: Optional[BookId] = None,
        limit: int = 50,
    ) -> List[Highlight]:
        """
        Full-text search across highlight text.

        Uses PostgreSQL's TSVECTOR for production, falls back to LIKE for SQLite.

        Args:
            user_id: User performing search
            query: Search query
            book_id: Optional book filter
            limit: Maximum results

        Returns:
            List of matching highlights
        """
        stmt = (
            select(HighlightORM)
            .where(HighlightORM.user_id == user_id.value)
            .where(HighlightORM.deleted_at.is_(None))
        )

        if book_id:
            stmt = stmt.where(HighlightORM.book_id == book_id.value)

        # Try PostgreSQL full-text search first
        if self.session.bind.dialect.name == "postgresql":
            # Use ts_vector column if available
            stmt = stmt.where(
                func.to_tsvector("english", HighlightORM.text).match(query)
            )
        else:
            # Fallback to LIKE for SQLite
            stmt = stmt.where(HighlightORM.text.ilike(f"%{query}%"))

        stmt = stmt.limit(limit)

        orms = self.session.execute(stmt).scalars().all()

        return [self.mapper.to_domain(orm) for orm in orms]
```

### File: `backend/src/infrastructure/persistence/repositories/reading_session_repository.py`

```python
"""
PostgreSQL implementation of ReadingSession repository.
"""
from typing import List, Optional, Set
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.application.ports.persistence import IReadingSessionRepository
from src.domain.reading.entities import ReadingSession
from src.domain.common.value_objects import (
    ReadingSessionId,
    BookId,
    UserId,
    ContentHash,
)
from src.models import ReadingSession as ReadingSessionORM
from ..mappers import ReadingSessionMapper


class PostgresReadingSessionRepository(IReadingSessionRepository):
    """SQLAlchemy-based implementation of reading session repository."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapper = ReadingSessionMapper()

    def add(self, session_entity: ReadingSession) -> ReadingSession:
        """Add a single reading session."""
        orm = self.mapper.to_orm(session_entity)
        self.session.add(orm)
        self.session.flush()

        return self.mapper.to_domain(orm)

    def add_many(self, sessions: List[ReadingSession]) -> List[ReadingSession]:
        """Bulk insert reading sessions."""
        orms = [self.mapper.to_orm(s) for s in sessions]
        self.session.add_all(orms)
        self.session.flush()

        return [self.mapper.to_domain(orm) for orm in orms]

    def get_by_id(self, session_id: ReadingSessionId) -> Optional[ReadingSession]:
        """Retrieve session by ID."""
        orm = self.session.get(ReadingSessionORM, session_id.value)

        if orm is None:
            return None

        return self.mapper.to_domain(orm)

    def get_by_book(
        self,
        user_id: UserId,
        book_id: BookId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[ReadingSession]:
        """
        Get reading sessions for a book with optional date filters.

        Args:
            user_id: User who owns sessions
            book_id: Book identifier
            start_date: Filter sessions after this date
            end_date: Filter sessions before this date

        Returns:
            List of reading session services
        """
        stmt = (
            select(ReadingSessionORM)
            .where(ReadingSessionORM.user_id == user_id.value)
            .where(ReadingSessionORM.book_id == book_id.value)
        )

        if start_date:
            stmt = stmt.where(ReadingSessionORM.start_time >= start_date)

        if end_date:
            stmt = stmt.where(ReadingSessionORM.end_time <= end_date)

        stmt = stmt.order_by(ReadingSessionORM.start_time)

        orms = self.session.execute(stmt).scalars().all()

        return [self.mapper.to_domain(orm) for orm in orms]

    def get_existing_hashes(
        self,
        user_id: UserId,
        book_id: BookId,
    ) -> Set[ContentHash]:
        """Get existing content hashes for deduplication."""
        stmt = (
            select(ReadingSessionORM.content_hash)
            .where(ReadingSessionORM.user_id == user_id.value)
            .where(ReadingSessionORM.book_id == book_id.value)
        )

        hashes = self.session.execute(stmt).scalars().all()

        return {ContentHash(h) for h in hashes}

    def update(self, session_entity: ReadingSession) -> ReadingSession:
        """Update existing reading session."""
        orm = self.session.get(ReadingSessionORM, session_entity.id.value)

        if orm is None:
            raise ValueError(f"ReadingSession {session_entity.id.value} not found")

        self.mapper.update_orm_from_entity(orm, session_entity)
        self.session.flush()

        return self.mapper.to_domain(orm)
```

### File: `backend/src/infrastructure/persistence/repositories/highlight_tag_repository.py`

```python
"""
PostgreSQL implementation of HighlightTag repository.
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.application.ports.persistence import IHighlightTagRepository
from src.domain.reading.entities import HighlightTag
from src.domain.common.value_objects import (
    HighlightTagId,
    BookId,
    UserId,
)
from src.models import HighlightTag as HighlightTagORM, HighlightTagGroup as HighlightTagGroupORM
from ..mappers import HighlightTagMapper


class PostgresHighlightTagRepository(IHighlightTagRepository):
    """SQLAlchemy-based implementation of highlight tag repository."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.mapper = HighlightTagMapper()

    def add(self, tag: HighlightTag) -> HighlightTag:
        """Add a new highlight tag."""
        orm = self.mapper.to_orm(tag)

        # Look up tag group if specified
        if tag.group_name:
            group = self._get_or_create_tag_group(
                tag.user_id,
                tag.book_id,
                tag.group_name
            )
            orm.tag_group_id = group.id

        self.session.add(orm)
        self.session.flush()

        return self.mapper.to_domain(orm)

    def get_by_id(self, tag_id: HighlightTagId) -> Optional[HighlightTag]:
        """Retrieve tag by ID."""
        stmt = (
            select(HighlightTagORM)
            .options(selectinload(HighlightTagORM.tag_group))
            .where(HighlightTagORM.id == tag_id.value)
        )
        orm = self.session.execute(stmt).scalar_one_or_none()

        if orm is None:
            return None

        return self.mapper.to_domain(orm)

    def get_by_book(self, user_id: UserId, book_id: BookId) -> List[HighlightTag]:
        """Get all tags for a book."""
        stmt = (
            select(HighlightTagORM)
            .options(selectinload(HighlightTagORM.tag_group))
            .where(HighlightTagORM.user_id == user_id.value)
            .where(HighlightTagORM.book_id == book_id.value)
            .order_by(HighlightTagORM.name)
        )

        orms = self.session.execute(stmt).scalars().all()

        return [self.mapper.to_domain(orm) for orm in orms]

    def get_or_create(
        self,
        user_id: UserId,
        book_id: BookId,
        name: str,
        group_name: Optional[str] = None,
    ) -> HighlightTag:
        """
        Get existing tag or create if doesn't exist.

        Args:
            user_id: User who owns the tag
            book_id: Book the tag belongs to
            name: Tag name
            group_name: Optional group name

        Returns:
            Existing or newly created tag
        """
        # Try to find existing tag
        stmt = (
            select(HighlightTagORM)
            .options(selectinload(HighlightTagORM.tag_group))
            .where(HighlightTagORM.user_id == user_id.value)
            .where(HighlightTagORM.book_id == book_id.value)
            .where(HighlightTagORM.name == name)
        )

        orm = self.session.execute(stmt).scalar_one_or_none()

        if orm:
            return self.mapper.to_domain(orm)

        # Create new tag
        tag = HighlightTag(
            id=HighlightTagId.generate(),
            user_id=user_id,
            book_id=book_id,
            name=name,
            group_name=group_name,
        )

        return self.add(tag)

    def delete(self, tag_id: HighlightTagId) -> None:
        """Delete a tag."""
        orm = self.session.get(HighlightTagORM, tag_id.value)

        if orm:
            self.session.delete(orm)
            self.session.flush()

    def _get_or_create_tag_group(
        self,
        user_id: UserId,
        book_id: BookId,
        group_name: str,
    ) -> HighlightTagGroupORM:
        """Get or create a tag group (internal helper)."""
        stmt = (
            select(HighlightTagGroupORM)
            .where(HighlightTagGroupORM.book_id == book_id.value)
            .where(HighlightTagGroupORM.name == group_name)
        )

        group = self.session.execute(stmt).scalar_one_or_none()

        if not group:
            group = HighlightTagGroupORM(
                book_id=book_id.value,
                name=group_name,
            )
            self.session.add(group)
            self.session.flush()

        return group
```

### File: `backend/src/infrastructure/persistence/repositories/__init__.py`

```python
"""Repository adapter implementations."""
from .highlight_repository import PostgresHighlightRepository
from .reading_session_repository import PostgresReadingSessionRepository
from .highlight_tag_repository import PostgresHighlightTagRepository

__all__ = [
    "PostgresHighlightRepository",
    "PostgresReadingSessionRepository",
    "PostgresHighlightTagRepository",
]
```

**Action:**

1. Create directory: `mkdir -p backend/src/infrastructure/persistence/repositories`
2. Create all repository implementation files
3. Verify imports work

---

## Step 3.5: Create Infrastructure Module Init Files

### File: `backend/src/infrastructure/__init__.py`

```python
"""Infrastructure layer - adapters and external integrations."""
from .persistence.unit_of_work import SqlAlchemyUnitOfWork

__all__ = ["SqlAlchemyUnitOfWork"]
```

### File: `backend/src/infrastructure/persistence/__init__.py`

```python
"""Persistence infrastructure (repositories, mappers, UoW)."""
from .unit_of_work import SqlAlchemyUnitOfWork
from .repositories import (
    PostgresHighlightRepository,
    PostgresReadingSessionRepository,
    PostgresHighlightTagRepository,
)
from .mappers import (
    HighlightMapper,
    ReadingSessionMapper,
    HighlightTagMapper,
)

__all__ = [
    "SqlAlchemyUnitOfWork",
    "PostgresHighlightRepository",
    "PostgresReadingSessionRepository",
    "PostgresHighlightTagRepository",
    "HighlightMapper",
    "ReadingSessionMapper",
    "HighlightTagMapper",
]
```

**Action:**

1. Create both `__init__.py` files
2. Verify full import chain: `python -c "from backend.src.infrastructure import SqlAlchemyUnitOfWork"`

---

## Step 3.6: Write Infrastructure Tests

### File: `backend/tests/integration/infrastructure/persistence/test_highlight_repository.py`

```python
"""
Integration tests for HighlightRepository.

These tests use a real database (in-memory SQLite) to verify
repository implementation correctness.
"""
import pytest
from sqlalchemy.orm import Session

from backend.src.domain.reading.entities import Highlight
from backend.src.domain.common.value_objects import UserId, BookId, HighlightId, ContentHash
from backend.src.infrastructure.persistence.repositories import PostgresHighlightRepository


class TestHighlightRepositoryAdd:
    """Tests for adding highlights."""

    def test_add_single_highlight(self, db_session: Session):
        """Can add a single highlight and retrieve it."""
        repo = PostgresHighlightRepository(db_session)

        # Create domain entity
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(1),
            text="Test highlight text",
            page=42,
            note="Important note",
        )

        # Add to repository
        saved = repo.add(highlight)

        # Should have database-assigned ID
        assert saved.id.value > 0
        assert saved.text.value == "Test highlight text"
        assert saved.page == 42
        assert saved.note == "Important note"

        # Should be retrievable
        retrieved = repo.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.id == saved.id
        assert retrieved.text.value == "Test highlight text"

    def test_add_many_highlights(self, db_session: Session):
        """Can bulk add multiple highlights."""
        repo = PostgresHighlightRepository(db_session)

        highlights = [
            Highlight.create(
                user_id=UserId(1),
                book_id=BookId(1),
                text=f"Highlight {i}",
            )
            for i in range(5)
        ]

        saved = repo.add_many(highlights)

        # All should have IDs
        assert len(saved) == 5
        assert all(h.id.value > 0 for h in saved)

        # All should be retrievable
        book_highlights = repo.get_by_book(UserId(1), BookId(1))
        assert len(book_highlights) == 5


class TestHighlightRepositoryQuery:
    """Tests for querying highlights."""

    def test_get_by_book(self, db_session: Session):
        """Can get all highlights for a book."""
        repo = PostgresHighlightRepository(db_session)

        # Add highlights for two books
        repo.add_many([
            Highlight.create(UserId(1), BookId(1), f"Book 1 highlight {i}")
            for i in range(3)
        ])
        repo.add_many([
            Highlight.create(UserId(1), BookId(2), f"Book 2 highlight {i}")
            for i in range(2)
        ])

        # Get book 1 highlights
        book1_highlights = repo.get_by_book(UserId(1), BookId(1))
        assert len(book1_highlights) == 3
        assert all(h.book_id == BookId(1) for h in book1_highlights)

        # Get book 2 highlights
        book2_highlights = repo.get_by_book(UserId(1), BookId(2))
        assert len(book2_highlights) == 2

    def test_get_existing_hashes(self, db_session: Session):
        """Can get existing content hashes for deduplication."""
        repo = PostgresHighlightRepository(db_session)

        # Add some highlights
        h1 = repo.add(Highlight.create(UserId(1), BookId(1), "Text 1"))
        h2 = repo.add(Highlight.create(UserId(1), BookId(1), "Text 2"))

        # Get hashes
        hashes = repo.get_existing_hashes(UserId(1), BookId(1))

        assert len(hashes) == 2
        assert h1.content_hash in hashes
        assert h2.content_hash in hashes

    def test_exclude_deleted_by_default(self, db_session: Session):
        """Deleted highlights are excluded by default."""
        repo = PostgresHighlightRepository(db_session)

        # Add highlight and soft delete it
        highlight = repo.add(Highlight.create(UserId(1), BookId(1), "To delete"))
        highlight.soft_delete()
        repo.update(highlight)

        # Should not appear in default query
        highlights = repo.get_by_book(UserId(1), BookId(1))
        assert len(highlights) == 0

        # Should appear when including deleted
        highlights = repo.get_by_book(UserId(1), BookId(1), include_deleted=True)
        assert len(highlights) == 1


class TestHighlightRepositoryUpdate:
    """Tests for updating highlights."""

    def test_update_highlight_note(self, db_session: Session):
        """Can update highlight note."""
        repo = PostgresHighlightRepository(db_session)

        # Create and save highlight
        highlight = repo.add(Highlight.create(
            UserId(1),
            BookId(1),
            "Test text",
            note="Original note",
        ))

        # Update note
        highlight.update_note("Updated note")
        updated = repo.update(highlight)

        # Verify update persisted
        retrieved = repo.get_by_id(highlight.id)
        assert retrieved.note == "Updated note"

    def test_soft_delete_highlight(self, db_session: Session):
        """Can soft delete a highlight."""
        repo = PostgresHighlightRepository(db_session)

        highlight = repo.add(Highlight.create(UserId(1), BookId(1), "To delete"))

        # Soft delete
        highlight.soft_delete()
        repo.update(highlight)

        # Should still exist in database
        retrieved = repo.get_by_id(highlight.id)
        assert retrieved is not None
        assert retrieved.is_deleted()


class TestHighlightRepositoryDelete:
    """Tests for hard deletion."""

    def test_delete_highlight(self, db_session: Session):
        """Can hard delete a highlight."""
        repo = PostgresHighlightRepository(db_session)

        highlight = repo.add(Highlight.create(UserId(1), BookId(1), "To delete"))

        # Hard delete
        repo.delete(highlight.id)

        # Should not exist
        assert repo.get_by_id(highlight.id) is None
```

### File: `backend/tests/integration/infrastructure/persistence/test_unit_of_work.py`

```python
"""
Integration tests for Unit of Work.

Tests transaction management and repository coordination.
"""
import pytest

from backend.src.domain.reading.entities import Highlight
from backend.src.domain.common.value_objects import UserId, BookId
from backend.src.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork


def test_uow_commits_transaction(session_factory):
    """Unit of Work commits changes when commit() is called."""
    uow = SqlAlchemyUnitOfWork(session_factory)

    with uow:
        highlight = Highlight.create(
            user_id=UserId(1),
            book_id=BookId(1),
            text="Test highlight",
        )

        saved = uow.highlights.add(highlight)
        uow.commit()

    # Verify in new UoW that highlight was persisted
    with SqlAlchemyUnitOfWork(session_factory) as uow2:
        retrieved = uow2.highlights.get_by_id(saved.id)
        assert retrieved is not None
        assert retrieved.text.value == "Test highlight"


def test_uow_rollback_on_exception(session_factory):
    """Unit of Work automatically rolls back on exception."""
    uow = SqlAlchemyUnitOfWork(session_factory)

    try:
        with uow:
            highlight = Highlight.create(
                UserId(1),
                BookId(1),
                "Should not persist",
            )

            saved = uow.highlights.add(highlight)
            saved_id = saved.id

            # Simulate error before commit
            raise ValueError("Oops!")
    except ValueError:
        pass

    # Verify highlight was NOT persisted
    with SqlAlchemyUnitOfWork(session_factory) as uow2:
        retrieved = uow2.highlights.get_by_id(saved_id)
        assert retrieved is None


def test_uow_repositories_share_session(session_factory):
    """All repositories in UoW share the same database session."""
    uow = SqlAlchemyUnitOfWork(session_factory)

    with uow:
        # Add highlight
        highlight = Highlight.create(UserId(1), BookId(1), "Test")
        saved_highlight = uow.highlights.add(highlight)

        # Get hashes - should see uncommitted highlight
        hashes = uow.highlights.get_existing_hashes(UserId(1), BookId(1))

        # Should include the highlight we just added (even though not committed)
        assert saved_highlight.content_hash in hashes

        uow.commit()
```

**Action:**

1. Create directory: `mkdir -p backend/tests/integration/infrastructure/persistence`
2. Create test files
3. Run tests: `pytest backend/tests/integration/infrastructure/persistence/ -v`

---

## Step 3.7: Update Domain Entity Factory Methods

We need to add a `create_with_id` factory method to ReadingSession for reconstitution from database.

### File: `backend/src/domain/reading/entities/reading_session.py`

Add this method to the `ReadingSession` class:

```python
@classmethod
def create_with_id(
    cls,
    id: ReadingSessionId,
    user_id: UserId,
    book_id: BookId,
    start_time: datetime,
    end_time: datetime,
    content_hash: ContentHash,
    start_xpoint: Optional[XPointRange] = None,
    start_page: Optional[int] = None,
    end_page: Optional[int] = None,
    device_id: Optional[str] = None,
    ai_summary: Optional[str] = None,
) -> "ReadingSession":
    """
    Factory method for reconstituting reading session from persistence.

    Used by repositories when loading from database.
    """
    return cls(
        id=id,
        user_id=user_id,
        book_id=book_id,
        start_time=start_time,
        end_time=end_time,
        content_hash=content_hash,
        start_xpoint=start_xpoint,
        start_page=start_page,
        end_page=end_page,
        device_id=device_id,
        ai_summary=ai_summary,
        _highlight_ids=[],
    )
```

**Action:**

1. Edit `backend/src/domain/reading/entities/reading_session.py`
2. Add the `create_with_id` classmethod

---

## Phase 3 Checklist

After completing all steps, verify:

- [x] Repository port interfaces defined in `application/ports/persistence.py`
- [x] Unit of Work port updated and implementation created
- [x] Mappers created for Highlight, ReadingSession, HighlightTag
- [x] Repository adapters implemented (PostgresHighlightRepository, etc.)
- [x] All `__init__.py` files created with proper exports
- [x] Integration tests pass for repositories
- [x] Integration tests pass for Unit of Work
- [x] Domain entities have both `create()` and `create_with_id()` factory methods
- [x] No circular dependencies between layers
- [x] Domain layer still has zero infrastructure imports

**Verification:**

```bash
# Run all infrastructure tests
pytest backend/tests/integration/infrastructure/ -v

# Verify imports work
python -c "from backend.src.infrastructure import SqlAlchemyUnitOfWork"
python -c "from backend.src.application.ports import IHighlightRepository"

# Check for circular imports
python -m backend.src.infrastructure.persistence.unit_of_work
```

---

## Summary of Phase 3

### What You've Built

After completing Phase 3, you have:

1. **Repository Port Interfaces** (`IHighlightRepository`, `IReadingSessionRepository`, `IHighlightTagRepository`)
   - Abstract interfaces that application layer depends on
   - No infrastructure dependencies

2. **Unit of Work Pattern**
   - Transaction management across multiple repositories
   - Ensures atomicity of use case operations
   - Context manager for clean resource handling

3. **ORM-to-Domain Mappers**
   - Translate between SQLAlchemy models and domain entities
   - Handle value object serialization/deserialization
   - Maintain separation of concerns

4. **Repository Implementations**
   - PostgreSQL-specific implementations of repository ports
   - Efficient bulk operations
   - Full-text search support
   - Deduplication support via content hashes

5. **Integration Tests**
   - Verify repository behavior with real database
   - Test transaction boundaries
   - Ensure mapper correctness

### What's Next

**Phase 4**: Application Layer

- Create use cases (UploadHighlightsUseCase, GetHighlightsByBookUseCase)
- Create DTOs for input/output
- Wire up dependency injection
- Handle application-level concerns (validation, authorization)

**Phase 5**: HTTP Layer (API Routes)

- Refactor existing routers to use use cases
- Update FastAPI dependencies
- Migrate from service layer to application layer
- Maintain backward compatibility during transition

**Phase 6**: Migration Strategy

- Gradual migration of existing code
- Feature flags for rollback capability
- Performance benchmarking
- Monitoring and observability

---

## Key Architectural Decisions

### 1. Shared ORM Models (Not Duplicated)

**Decision**: Reuse existing `models.py` ORM models instead of creating reading-specific ORM models.

**Rationale**:
- Single database schema (modular monolith requirement)
- One migration chain for all modules
- Avoid duplication and drift between module schemas
- Mappers provide abstraction layer between domain and ORM

### 2. Repository Implementations Live in Infrastructure

**Decision**: Repository implementations (`PostgresHighlightRepository`) are in `infrastructure/` layer.

**Rationale**:
- Repositories are adapters - they adapt infrastructure to domain needs
- Application layer only knows about `IHighlightRepository` interface
- Enables testing with mock repositories
- Future-proof for switching databases (e.g., add `MongoHighlightRepository`)

### 3. Unit of Work Manages Session Lifecycle

**Decision**: Unit of Work creates and manages SQLAlchemy session, repositories receive session from UoW.

**Rationale**:
- Ensures all repositories in a use case share same transaction
- Clean separation: UoW = transaction boundary, Repository = data access
- Simplified testing (mock UoW or use test database)
- Prevents session leaks

### 4. Mappers Handle XPoint Serialization

**Decision**: XPoint value objects are serialized to strings in database, mappers handle conversion.

**Rationale**:
- Domain layer works with rich XPoint objects
- Database stores strings (compatible with existing schema)
- Mappers encapsulate conversion logic
- No leakage of serialization concerns into domain

### 5. Repository Methods Return Domain Entities

**Decision**: Repository methods always return domain entities, never ORM models.

**Rationale**:
- Application layer only sees domain objects
- Infrastructure details hidden behind abstraction
- Prevents business logic from depending on SQLAlchemy
- Easier to test use cases with domain entities

---

## Common Pitfalls to Avoid

1. ❌ **Don't** import domain entities into `models.py`
2. ❌ **Don't** import ORM models into domain layer
3. ❌ **Don't** bypass Unit of Work and create repositories directly with sessions
4. ❌ **Don't** put business logic in repositories (keep them focused on data access)
5. ❌ **Don't** commit inside repositories - let UoW manage transactions
6. ✅ **Do** use mappers for all ORM ↔ domain conversions
7. ✅ **Do** flush (not commit) inside repositories to get IDs
8. ✅ **Do** test repositories with integration tests (real database)
9. ✅ **Do** use type hints everywhere for clarity
10. ✅ **Do** handle None cases gracefully (optional fields)

---

## Performance Considerations

### Bulk Operations

The repositories support bulk operations (`add_many`) which are significantly faster than adding one at a time:

```python
# Good: Bulk insert (single INSERT with multiple VALUES)
highlights = [Highlight.create(...) for _ in range(100)]
saved = repo.add_many(highlights)

# Bad: Loop with individual inserts (100 separate INSERT statements)
for h in highlights:
    repo.add(h)
```

### Eager Loading

For queries that need related entities, use SQLAlchemy's eager loading:

```python
# In repository implementation
stmt = (
    select(HighlightORM)
    .options(selectinload(HighlightORM.highlight_tags))  # Avoid N+1
    .where(...)
)
```

### Connection Pooling

The existing `database.py` setup handles connection pooling. In production, tune pool size based on load.

---

## Testing Strategy

### Unit Tests (Domain Layer)
- Test domain entities and value objects in isolation
- No database dependencies
- Fast, deterministic

### Integration Tests (Infrastructure Layer)
- Test repositories with real database (in-memory SQLite)
- Verify mappers correctly convert between domain and ORM
- Test transaction boundaries with Unit of Work

### End-to-End Tests (Application Layer - Phase 4)
- Test use cases with real repositories
- Verify business workflows
- Use test database or mocks

---

Good luck with Phase 3! Take it step by step, test each component as you build it, and you'll have a solid, clean infrastructure layer that supports the domain model beautifully.
