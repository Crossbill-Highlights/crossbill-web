# Book Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In-app notes (title + markdown body + optional kind) per book, many-to-many linked to chapters, highlights, and highlight tags, creatable from the notes tab, chapter dialog, highlight modal, and AI chat.

**Architecture:** New `notes` bounded context following the existing DDD layout: domain entity → ORM + Alembic migration → repository (protocol in application layer, impl + mapper in infrastructure) → use cases → DI container → FastAPI router. The `Note` is user-scoped and links to books via a `note_books` association table (spec: `docs/superpowers/specs/2026-07-08-book-notes-design.md`). Frontend: orval-generated hooks + MUI components mirroring the Flashcards feature.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Alembic, dependency-injector, pytest (in-memory SQLite), pyright, ruff. Frontend: React, TanStack Router/Query, MUI v7, orval, react-markdown.

## Global Constraints

- Type checking: `cd backend && uv run pyright <file>` — pyright only, never mypy. Frontend: `cd frontend && npm run type-check`.
- Linting: `cd backend && uv run ruff check <file>`; frontend `cd frontend && npm run lint`.
- ORM models ONLY in `backend/src/models.py` / infrastructure layer. Domain and application layers never import them.
- Use cases return domain entities, never Pydantic schemas. Routers convert entities → schemas, converting value objects to primitives (`.value`).
- Raise specific NotFound subclasses (`NoteNotFoundError`), never `EntityNotFoundError("Note", id)` directly.
- SQLAlchemy queries with `joinedload()` on collections need `.unique()`. (This plan uses `lazy="selectin"` relationships instead, which do not.)
- Full test suite must pass before declaring done: `cd backend && uv run pytest`.
- All work on a feature branch (no worktrees): `git checkout -b feature/book-notes` before Task 1.
- All backend commands run from `backend/`, all frontend commands from `frontend/`.

---

### Task 1: Domain layer — `NoteId`, `NoteKind`, `Note` entity, exceptions

**Files:**
- Modify: `backend/src/domain/common/value_objects/ids.py` (add `NoteId` after `FlashcardId`)
- Modify: `backend/src/domain/common/value_objects/__init__.py` (export `NoteId`)
- Create: `backend/src/domain/notes/__init__.py`
- Create: `backend/src/domain/notes/entities/__init__.py`
- Create: `backend/src/domain/notes/entities/note.py`
- Create: `backend/src/domain/notes/exceptions.py`
- Test: `backend/tests/unit/domain/notes/entities/test_note.py` (plus empty `__init__.py` files in new test dirs if siblings have them — check `tests/unit/domain/library/`; mirror whatever convention exists)

**Interfaces:**
- Consumes: `Entity`/`AggregateRoot` bases, `EntityId`, `UserId` from `src.domain.common`.
- Produces (later tasks rely on these exact signatures):
  - `NoteId(EntityId)` with `.generate() -> NoteId` returning `NoteId(0)`
  - `NoteKind(str, Enum)` with values `CHARACTER="character"`, `TERM="term"`, `CONCEPT="concept"`, `OTHER="other"`
  - `Note.create(user_id: UserId, title: str, book_ids: list[int], body: str = "", kind: NoteKind | None = None, chapter_ids: list[int] | None = None, highlight_ids: list[int] | None = None, highlight_tag_ids: list[int] | None = None) -> Note`
  - `Note.create_with_id(id: NoteId, user_id: UserId, title: str, body: str, kind: NoteKind | None, created_at: datetime, updated_at: datetime, book_ids: list[int], chapter_ids: list[int], highlight_ids: list[int], highlight_tag_ids: list[int]) -> Note`
  - `note.update_content(title: str, body: str, kind: NoteKind | None) -> None`
  - `note.replace_links(book_ids: list[int], chapter_ids: list[int], highlight_ids: list[int], highlight_tag_ids: list[int]) -> None`
  - `NoteNotFoundError(note_id: int)`, `NoteLinkBookMismatchError(entity_type: str, entity_id: int)`

- [ ] **Step 1: Write the failing entity tests**

`backend/tests/unit/domain/notes/entities/test_note.py`:

```python
"""Tests for Note domain entity."""

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import UserId
from src.domain.notes.entities.note import Note, NoteKind


def make_note(**overrides: object) -> Note:
    defaults: dict = {
        "user_id": UserId(1),
        "title": "Stoicism",
        "book_ids": [1],
    }
    defaults.update(overrides)
    return Note.create(**defaults)


class TestNoteInvariants:
    def test_create_sets_fields_and_strips_title(self) -> None:
        note = make_note(title="  Raskolnikov  ", body="Main character", kind=NoteKind.CHARACTER)
        assert note.title == "Raskolnikov"
        assert note.body == "Main character"
        assert note.kind == NoteKind.CHARACTER
        assert note.book_ids == [1]
        assert note.id.value == 0

    def test_empty_title_raises(self) -> None:
        with pytest.raises(DomainError, match="title"):
            make_note(title="")

    def test_whitespace_title_raises(self) -> None:
        with pytest.raises(DomainError, match="title"):
            make_note(title="   ")

    def test_no_linked_books_raises(self) -> None:
        with pytest.raises(DomainError, match="at least one book"):
            make_note(book_ids=[])


class TestNoteUpdate:
    def test_update_content(self) -> None:
        note = make_note()
        note.update_content(title="  New title ", body="New body", kind=NoteKind.TERM)
        assert note.title == "New title"
        assert note.body == "New body"
        assert note.kind == NoteKind.TERM

    def test_update_content_empty_title_raises(self) -> None:
        note = make_note()
        with pytest.raises(DomainError, match="title"):
            note.update_content(title="", body="x", kind=None)

    def test_replace_links(self) -> None:
        note = make_note(chapter_ids=[10], highlight_ids=[20])
        note.replace_links(
            book_ids=[1], chapter_ids=[11, 12], highlight_ids=[], highlight_tag_ids=[30]
        )
        assert note.chapter_ids == [11, 12]
        assert note.highlight_ids == []
        assert note.highlight_tag_ids == [30]

    def test_replace_links_requires_book(self) -> None:
        note = make_note()
        with pytest.raises(DomainError, match="at least one book"):
            note.replace_links(book_ids=[], chapter_ids=[], highlight_ids=[], highlight_tag_ids=[])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/domain/notes/ -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.domain.notes'`

- [ ] **Step 3: Add `NoteId` to `backend/src/domain/common/value_objects/ids.py`**

Insert after the `FlashcardId` class, matching its style exactly:

```python
@dataclass(frozen=True)
class NoteId(EntityId):
    """Strongly-typed note identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("NoteId must be non-negative")

    @classmethod
    def generate(cls) -> "NoteId":
        return cls(0)  # Database assigns real ID
```

Then add `NoteId` to the import list and `__all__` in `backend/src/domain/common/value_objects/__init__.py` (alphabetical position, matching existing entries).

- [ ] **Step 4: Create the entity and exceptions**

`backend/src/domain/notes/__init__.py`:

```python
"""Notes domain context."""
```

`backend/src/domain/notes/entities/__init__.py`:

```python
"""Notes domain entities."""

from src.domain.notes.entities.note import Note, NoteKind

__all__ = ["Note", "NoteKind"]
```

`backend/src/domain/notes/entities/note.py`:

```python
"""Note entity for user-authored book notes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from src.domain.common.aggregate_root import AggregateRoot
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import NoteId, UserId


class NoteKind(str, Enum):
    """Optional classification of a note."""

    CHARACTER = "character"
    TERM = "term"
    CONCEPT = "concept"
    OTHER = "other"


@dataclass
class Note(AggregateRoot[NoteId]):
    """
    User-authored note about a term, character, or concept.

    Business Rules:
    - Title cannot be empty
    - A note must be linked to at least one book
    - Body may be empty (a bare title is a valid note)

    Cross-aggregate validation (linked chapters/highlights/tags must belong
    to a linked book) is performed in the application layer, which can load
    the referenced aggregates.
    """

    id: NoteId
    user_id: UserId
    title: str
    body: str = ""
    kind: NoteKind | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Link-id collections (association rows persisted by infrastructure)
    book_ids: list[int] = field(default_factory=list)
    chapter_ids: list[int] = field(default_factory=list)
    highlight_ids: list[int] = field(default_factory=list)
    highlight_tag_ids: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate invariants."""
        self._validate_title(self.title)
        self._validate_books(self.book_ids)

    def update_content(self, title: str, body: str, kind: NoteKind | None) -> None:
        """Update title, body and kind."""
        self._validate_title(title)
        self.title = title.strip()
        self.body = body
        self.kind = kind

    def replace_links(
        self,
        book_ids: list[int],
        chapter_ids: list[int],
        highlight_ids: list[int],
        highlight_tag_ids: list[int],
    ) -> None:
        """Replace all link sets."""
        self._validate_books(book_ids)
        self.book_ids = list(book_ids)
        self.chapter_ids = list(chapter_ids)
        self.highlight_ids = list(highlight_ids)
        self.highlight_tag_ids = list(highlight_tag_ids)

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise DomainError("Note title cannot be empty")

    @staticmethod
    def _validate_books(book_ids: list[int]) -> None:
        if not book_ids:
            raise DomainError("Note must be linked to at least one book")

    @classmethod
    def create(
        cls,
        user_id: UserId,
        title: str,
        book_ids: list[int],
        body: str = "",
        kind: NoteKind | None = None,
        chapter_ids: list[int] | None = None,
        highlight_ids: list[int] | None = None,
        highlight_tag_ids: list[int] | None = None,
    ) -> Note:
        """Create a new note (ID will be 0 until persisted)."""
        return cls(
            id=NoteId.generate(),
            user_id=user_id,
            title=title.strip() if title else title,
            body=body,
            kind=kind,
            book_ids=list(book_ids),
            chapter_ids=list(chapter_ids or []),
            highlight_ids=list(highlight_ids or []),
            highlight_tag_ids=list(highlight_tag_ids or []),
        )

    @classmethod
    def create_with_id(
        cls,
        id: NoteId,
        user_id: UserId,
        title: str,
        body: str,
        kind: NoteKind | None,
        created_at: datetime,
        updated_at: datetime,
        book_ids: list[int],
        chapter_ids: list[int],
        highlight_ids: list[int],
        highlight_tag_ids: list[int],
    ) -> Note:
        """Reconstitute a note from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            title=title,
            body=body,
            kind=kind,
            created_at=created_at,
            updated_at=updated_at,
            book_ids=book_ids,
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
        )
```

`backend/src/domain/notes/exceptions.py`:

```python
"""Notes domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError, ValidationError


class NoteNotFoundError(EntityNotFoundError):
    """Raised when a note cannot be found."""

    def __init__(self, note_id: int) -> None:
        super().__init__("Note", note_id)
        self.note_id = note_id


class NoteLinkBookMismatchError(ValidationError):
    """Raised when a linked chapter/highlight/tag does not belong to a linked book."""

    def __init__(self, entity_type: str, entity_id: int) -> None:
        super().__init__(
            f"{entity_type} {entity_id} does not belong to a book linked to this note"
        )
```

Note: if `AggregateRoot` requires explicit handling of `_events` or similar in dataclass ordering (check how `Highlight` in `src/domain/reading/entities/highlight.py` handles it), mirror `Highlight` exactly.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/domain/notes/ -v`
Expected: all PASS

- [ ] **Step 6: Type-check and lint**

Run: `cd backend && uv run pyright src/domain/notes/ src/domain/common/value_objects/ids.py && uv run ruff check src/domain/notes/ tests/unit/domain/notes/`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain backend/tests/unit/domain/notes
git commit -m "feat: add Note domain entity with kind and link collections"
```

---

### Task 2: ORM models + Alembic migration

**Files:**
- Modify: `backend/src/models.py` (4 association tables after `reading_session_highlights` around line 72; `Note` model at end of file)
- Create: `backend/alembic/versions/053_create_notes_tables.py`

**Interfaces:**
- Produces: ORM class `Note` (import as `from src.models import Note as NoteORM`) with `id, user_id, title, body, kind, created_at, updated_at` columns and `books`, `chapters`, `highlights`, `highlight_tags` relationship collections (all `lazy="selectin"`, no `back_populates`). Association tables `note_books`, `note_chapters`, `note_highlights`, `note_highlight_tags`.

- [ ] **Step 1: Add association tables to `backend/src/models.py`**

Insert after the existing `reading_session_highlights` table definition:

```python
# Association tables for many-to-many relationships between notes and other entities
note_books = Table(
    "note_books",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "book_id", Integer, ForeignKey("books.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)

note_chapters = Table(
    "note_chapters",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "chapter_id",
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)

note_highlights = Table(
    "note_highlights",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "highlight_id",
        Integer,
        ForeignKey("highlights.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)

note_highlight_tags = Table(
    "note_highlight_tags",
    Base.metadata,
    Column(
        "note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True
    ),
    Column(
        "highlight_tag_id",
        Integer,
        ForeignKey("highlight_tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
)
```

- [ ] **Step 2: Add the `Note` model at the end of `backend/src/models.py`**

```python
class Note(Base):
    """User-authored note about terms, characters, or concepts in books."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    kind: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (one-directional; notes are always queried from the note side)
    books: Mapped[list["Book"]] = relationship(secondary=note_books, lazy="selectin")
    chapters: Mapped[list["Chapter"]] = relationship(secondary=note_chapters, lazy="selectin")
    highlights: Mapped[list["Highlight"]] = relationship(
        secondary=note_highlights, lazy="selectin"
    )
    highlight_tags: Mapped[list["HighlightTag"]] = relationship(
        secondary=note_highlight_tags, lazy="selectin"
    )

    def __repr__(self) -> str:
        """String representation of Note."""
        return f"<Note(id={self.id}, title='{self.title}', kind={self.kind})>"
```

- [ ] **Step 3: Create migration `backend/alembic/versions/053_create_notes_tables.py`**

```python
"""Create notes and note association tables.

Revision ID: 053
Revises: 052
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "053"
down_revision: str | Sequence[str] | None = "052"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=True, index=True),
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
    op.create_table(
        "note_books",
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "note_chapters",
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "chapter_id",
            sa.Integer(),
            sa.ForeignKey("chapters.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "note_highlights",
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "highlight_id",
            sa.Integer(),
            sa.ForeignKey("highlights.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "note_highlight_tags",
        sa.Column(
            "note_id",
            sa.Integer(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "highlight_tag_id",
            sa.Integer(),
            sa.ForeignKey("highlight_tags.id", ondelete="CASCADE"),
            primary_key=True,
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("note_highlight_tags")
    op.drop_table("note_highlights")
    op.drop_table("note_chapters")
    op.drop_table("note_books")
    op.drop_table("notes")
```

- [ ] **Step 4: Verify migration round-trips**

Requires the dev Postgres running (`docker compose up -d db` from repo root if it isn't).

Run: `cd backend && uv run alembic upgrade head && uv run alembic downgrade 052 && uv run alembic upgrade head`
Expected: `Running upgrade 052 -> 053`, then downgrade, then upgrade again — no errors.

- [ ] **Step 5: Verify existing tests still pass and types check**

Run: `cd backend && uv run pytest -q && uv run pyright src/models.py`
Expected: all PASS, no type errors

- [ ] **Step 6: Commit**

```bash
git add backend/src/models.py backend/alembic/versions/053_create_notes_tables.py
git commit -m "feat: add notes tables and ORM model"
```

---

### Task 3: Note repository — protocol, mapper, implementation

**Files:**
- Create: `backend/src/application/notes/__init__.py`
- Create: `backend/src/application/notes/protocols/__init__.py`
- Create: `backend/src/application/notes/protocols/note_repository.py`
- Create: `backend/src/infrastructure/notes/__init__.py`
- Create: `backend/src/infrastructure/notes/mappers/__init__.py`
- Create: `backend/src/infrastructure/notes/mappers/note_mapper.py`
- Create: `backend/src/infrastructure/notes/repositories/__init__.py`
- Create: `backend/src/infrastructure/notes/repositories/note_repository.py`
- Test: `backend/tests/test_note_repository.py`

**Interfaces:**
- Consumes: `Note`, `NoteKind` from Task 1; `NoteORM` from Task 2.
- Produces:
  - `NoteRepositoryProtocol` with:
    - `find_by_id(note_id: NoteId, user_id: UserId) -> Note | None`
    - `find_by_book(book_id: BookId, user_id: UserId, kind: NoteKind | None = None, chapter_id: ChapterId | None = None, highlight_id: HighlightId | None = None, highlight_tag_id: HighlightTagId | None = None) -> list[Note]`
    - `save(note: Note) -> Note`
    - `delete(note_id: NoteId, user_id: UserId) -> bool`
  - `NoteRepository(db: AsyncSession)` implementing the protocol.

- [ ] **Step 1: Write the failing repository tests**

Follow the writing-tests skill: short tests, shared setup in fixtures. Uses existing conftest fixtures `db_session`, `test_user`, `test_book`, `test_chapter`, `test_highlight`, `test_highlight_tag` (see `backend/tests/conftest.py`; check `test_highlight_tag`'s exact dependencies around line 303 and include them if it needs e.g. `test_tag_group`).

`backend/tests/test_note_repository.py`:

```python
"""Tests for NoteRepository."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models
from src.domain.common.value_objects import BookId, ChapterId, NoteId, UserId
from src.domain.notes.entities.note import Note, NoteKind
from src.infrastructure.notes.repositories.note_repository import NoteRepository


@pytest.fixture
def note_repository(db_session: AsyncSession) -> NoteRepository:
    return NoteRepository(db_session)


@pytest.fixture
async def saved_note(
    note_repository: NoteRepository,
    test_user: models.User,
    test_book: models.Book,
    test_chapter: models.Chapter,
) -> Note:
    note = Note.create(
        user_id=UserId(test_user.id),
        title="Raskolnikov",
        body="Main character of Crime and Punishment",
        kind=NoteKind.CHARACTER,
        book_ids=[test_book.id],
        chapter_ids=[test_chapter.id],
    )
    return await note_repository.save(note)


class TestNoteRepositorySave:
    async def test_create_persists_note_with_links(
        self,
        saved_note: Note,
        db_session: AsyncSession,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> None:
        assert saved_note.id.value > 0
        assert saved_note.book_ids == [test_book.id]
        assert saved_note.chapter_ids == [test_chapter.id]
        result = await db_session.execute(select(models.Note).filter_by(id=saved_note.id.value))
        orm_note = result.scalar_one()
        assert orm_note.title == "Raskolnikov"
        assert orm_note.kind == "character"

    async def test_save_with_highlight_and_tag_links(
        self,
        note_repository: NoteRepository,
        test_user: models.User,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_highlight_tag: models.HighlightTag,
    ) -> None:
        note = Note.create(
            user_id=UserId(test_user.id),
            title="Stoicism",
            book_ids=[test_book.id],
            highlight_ids=[test_highlight.id],
            highlight_tag_ids=[test_highlight_tag.id],
        )
        saved = await note_repository.save(note)
        assert saved.highlight_ids == [test_highlight.id]
        assert saved.highlight_tag_ids == [test_highlight_tag.id]

    async def test_update_replaces_links_and_content(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_highlight: models.Highlight,
    ) -> None:
        saved_note.update_content(title="Rodion", body="Updated", kind=NoteKind.CHARACTER)
        saved_note.replace_links(
            book_ids=saved_note.book_ids,
            chapter_ids=[],
            highlight_ids=[test_highlight.id],
            highlight_tag_ids=[],
        )
        updated = await note_repository.save(saved_note)
        assert updated.title == "Rodion"
        assert updated.chapter_ids == []
        assert updated.highlight_ids == [test_highlight.id]


class TestNoteRepositoryFind:
    async def test_find_by_id(
        self, note_repository: NoteRepository, saved_note: Note, test_user: models.User
    ) -> None:
        found = await note_repository.find_by_id(saved_note.id, UserId(test_user.id))
        assert found is not None
        assert found.title == "Raskolnikov"

    async def test_find_by_id_wrong_user_returns_none(
        self, note_repository: NoteRepository, saved_note: Note
    ) -> None:
        found = await note_repository.find_by_id(saved_note.id, UserId(999))
        assert found is None

    async def test_find_by_book(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        notes = await note_repository.find_by_book(BookId(test_book.id), UserId(test_user.id))
        assert [n.id for n in notes] == [saved_note.id]

    async def test_find_by_book_filters_by_kind(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        matching = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), kind=NoteKind.CHARACTER
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), kind=NoteKind.TERM
        )
        assert len(matching) == 1
        assert empty == []

    async def test_find_by_book_filters_by_chapter(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_book: models.Book,
        test_chapter: models.Chapter,
        test_user: models.User,
    ) -> None:
        matching = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), chapter_id=ChapterId(test_chapter.id)
        )
        empty = await note_repository.find_by_book(
            BookId(test_book.id), UserId(test_user.id), chapter_id=ChapterId(99999)
        )
        assert len(matching) == 1
        assert empty == []


class TestNoteRepositoryDelete:
    async def test_delete(
        self,
        note_repository: NoteRepository,
        saved_note: Note,
        test_user: models.User,
        db_session: AsyncSession,
    ) -> None:
        deleted = await note_repository.delete(saved_note.id, UserId(test_user.id))
        assert deleted is True
        result = await db_session.execute(select(models.Note).filter_by(id=saved_note.id.value))
        assert result.scalar_one_or_none() is None

    async def test_delete_wrong_user_returns_false(
        self, note_repository: NoteRepository, saved_note: Note
    ) -> None:
        deleted = await note_repository.delete(saved_note.id, UserId(999))
        assert deleted is False

    async def test_delete_missing_returns_false(
        self, note_repository: NoteRepository, test_user: models.User
    ) -> None:
        deleted = await note_repository.delete(NoteId(99999), UserId(test_user.id))
        assert deleted is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_note_repository.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.infrastructure.notes'`

- [ ] **Step 3: Create protocol, mapper, and repository**

`backend/src/application/notes/__init__.py`:

```python
"""Notes application context."""
```

`backend/src/application/notes/protocols/__init__.py`:

```python
"""Notes application protocols."""

from src.application.notes.protocols.note_repository import NoteRepositoryProtocol

__all__ = ["NoteRepositoryProtocol"]
```

`backend/src/application/notes/protocols/note_repository.py`:

```python
"""Protocol for Note repository."""

from typing import Protocol

from src.domain.common.value_objects import (
    BookId,
    ChapterId,
    HighlightId,
    HighlightTagId,
    NoteId,
    UserId,
)
from src.domain.notes.entities.note import Note, NoteKind


class NoteRepositoryProtocol(Protocol):
    """Protocol for Note repository operations."""

    async def find_by_id(self, note_id: NoteId, user_id: UserId) -> Note | None:
        """Find a note by id, scoped to the user."""
        ...

    async def find_by_book(
        self,
        book_id: BookId,
        user_id: UserId,
        kind: NoteKind | None = None,
        chapter_id: ChapterId | None = None,
        highlight_id: HighlightId | None = None,
        highlight_tag_id: HighlightTagId | None = None,
    ) -> list[Note]:
        """Find notes linked to a book, with optional filters."""
        ...

    async def save(self, note: Note) -> Note:
        """Create or update a note, replacing association rows."""
        ...

    async def delete(self, note_id: NoteId, user_id: UserId) -> bool:
        """Delete a note. Returns False if not found."""
        ...
```

`backend/src/infrastructure/notes/__init__.py`:

```python
"""Notes infrastructure context."""
```

`backend/src/infrastructure/notes/mappers/__init__.py`:

```python
"""Notes mappers."""

from src.infrastructure.notes.mappers.note_mapper import NoteMapper

__all__ = ["NoteMapper"]
```

`backend/src/infrastructure/notes/mappers/note_mapper.py`:

```python
"""Mapper for Note ORM ↔ Domain conversion."""

from src.domain.common.value_objects import NoteId, UserId
from src.domain.notes.entities.note import Note, NoteKind
from src.models import Note as NoteORM


class NoteMapper:
    """Mapper for Note ORM ↔ Domain conversion."""

    def to_domain(self, orm_model: NoteORM) -> Note:
        """Convert ORM model to domain entity."""
        return Note.create_with_id(
            id=NoteId(orm_model.id),
            user_id=UserId(orm_model.user_id),
            title=orm_model.title,
            body=orm_model.body,
            kind=NoteKind(orm_model.kind) if orm_model.kind else None,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at,
            book_ids=[book.id for book in orm_model.books],
            chapter_ids=[chapter.id for chapter in orm_model.chapters],
            highlight_ids=[highlight.id for highlight in orm_model.highlights],
            highlight_tag_ids=[tag.id for tag in orm_model.highlight_tags],
        )

    def to_orm(self, domain_entity: Note, orm_model: NoteORM | None = None) -> NoteORM:
        """Convert domain entity scalar fields to ORM model.

        Association collections are synced separately by the repository,
        which loads the referenced ORM rows.
        """
        if orm_model:
            orm_model.user_id = domain_entity.user_id.value
            orm_model.title = domain_entity.title
            orm_model.body = domain_entity.body
            orm_model.kind = domain_entity.kind.value if domain_entity.kind else None
            return orm_model

        return NoteORM(
            id=domain_entity.id.value if domain_entity.id.value != 0 else None,
            user_id=domain_entity.user_id.value,
            title=domain_entity.title,
            body=domain_entity.body,
            kind=domain_entity.kind.value if domain_entity.kind else None,
        )
```

`backend/src/infrastructure/notes/repositories/__init__.py`:

```python
"""Notes repositories."""

from src.infrastructure.notes.repositories.note_repository import NoteRepository

__all__ = ["NoteRepository"]
```

`backend/src/infrastructure/notes/repositories/note_repository.py`:

```python
"""Repository for Note domain entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects import (
    BookId,
    ChapterId,
    HighlightId,
    HighlightTagId,
    NoteId,
    UserId,
)
from src.domain.notes.entities.note import Note, NoteKind
from src.infrastructure.notes.mappers.note_mapper import NoteMapper
from src.models import Book as BookORM
from src.models import Chapter as ChapterORM
from src.models import Highlight as HighlightORM
from src.models import HighlightTag as HighlightTagORM
from src.models import Note as NoteORM


class NoteRepository:
    """Repository for Note domain entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = NoteMapper()

    async def find_by_id(self, note_id: NoteId, user_id: UserId) -> Note | None:
        stmt = select(NoteORM).where(
            NoteORM.id == note_id.value,
            NoteORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        orm_model = result.scalar_one_or_none()
        return self.mapper.to_domain(orm_model) if orm_model else None

    async def find_by_book(
        self,
        book_id: BookId,
        user_id: UserId,
        kind: NoteKind | None = None,
        chapter_id: ChapterId | None = None,
        highlight_id: HighlightId | None = None,
        highlight_tag_id: HighlightTagId | None = None,
    ) -> list[Note]:
        stmt = (
            select(NoteORM)
            .where(
                NoteORM.user_id == user_id.value,
                NoteORM.books.any(BookORM.id == book_id.value),
            )
            .order_by(NoteORM.created_at.desc())
        )
        if kind is not None:
            stmt = stmt.where(NoteORM.kind == kind.value)
        if chapter_id is not None:
            stmt = stmt.where(NoteORM.chapters.any(ChapterORM.id == chapter_id.value))
        if highlight_id is not None:
            stmt = stmt.where(NoteORM.highlights.any(HighlightORM.id == highlight_id.value))
        if highlight_tag_id is not None:
            stmt = stmt.where(
                NoteORM.highlight_tags.any(HighlightTagORM.id == highlight_tag_id.value)
            )
        result = await self.db.execute(stmt)
        orm_models = result.scalars().all()
        return [self.mapper.to_domain(orm) for orm in orm_models]

    async def save(self, note: Note) -> Note:
        if note.id.value == 0:
            orm_model = self.mapper.to_orm(note)
            await self._sync_links(orm_model, note)
            self.db.add(orm_model)
            await self.db.flush()
        else:
            orm_model = await self.db.get(NoteORM, note.id.value)
            if not orm_model:
                raise ValueError(f"Note {note.id.value} not found")
            self.mapper.to_orm(note, orm_model)
            await self._sync_links(orm_model, note)
        note_id = orm_model.id
        await self.db.commit()

        # Re-select to get fresh timestamps and eagerly-loaded collections
        stmt = select(NoteORM).where(NoteORM.id == note_id)
        result = await self.db.execute(stmt)
        saved = result.scalar_one()
        return self.mapper.to_domain(saved)

    async def delete(self, note_id: NoteId, user_id: UserId) -> bool:
        stmt = select(NoteORM).where(
            NoteORM.id == note_id.value,
            NoteORM.user_id == user_id.value,
        )
        result = await self.db.execute(stmt)
        note_orm = result.scalar_one_or_none()
        if not note_orm:
            return False
        await self.db.delete(note_orm)
        await self.db.commit()
        return True

    async def _sync_links(self, orm_model: NoteORM, note: Note) -> None:
        """Replace association collections with rows matching the note's link ids."""
        orm_model.books = await self._load_all(BookORM, note.book_ids)
        orm_model.chapters = await self._load_all(ChapterORM, note.chapter_ids)
        orm_model.highlights = await self._load_all(HighlightORM, note.highlight_ids)
        orm_model.highlight_tags = await self._load_all(HighlightTagORM, note.highlight_tag_ids)

    async def _load_all(self, orm_class: type, ids: list[int]) -> list:
        if not ids:
            return []
        result = await self.db.execute(select(orm_class).where(orm_class.id.in_(ids)))
        return list(result.scalars().all())
```

Note on `_load_all` typing: if pyright complains about `orm_class: type` lacking an `id` attribute, replace the generic helper with four small explicit queries in `_sync_links` (one per ORM class) — correctness over cleverness.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_note_repository.py -v`
Expected: all PASS

- [ ] **Step 5: Type-check, lint, full suite**

Run: `cd backend && uv run pyright src/application/notes src/infrastructure/notes && uv run ruff check src/application/notes src/infrastructure/notes tests/test_note_repository.py && uv run pytest -q`
Expected: no errors, all tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/notes backend/src/infrastructure/notes backend/tests/test_note_repository.py
git commit -m "feat: add note repository with link-table sync"
```

---

### Task 4: Create + Get endpoints (use cases, schemas, router, DI)

**Files:**
- Create: `backend/src/application/notes/use_cases/__init__.py`
- Create: `backend/src/application/notes/use_cases/helpers.py`
- Create: `backend/src/application/notes/use_cases/dtos.py`
- Create: `backend/src/application/notes/use_cases/create_note_use_case.py`
- Create: `backend/src/application/notes/use_cases/get_note_use_case.py`
- Create: `backend/src/infrastructure/notes/schemas/__init__.py`
- Create: `backend/src/infrastructure/notes/schemas/note_schemas.py`
- Create: `backend/src/infrastructure/notes/routers/__init__.py`
- Create: `backend/src/infrastructure/notes/routers/notes.py`
- Create: `backend/src/containers/notes.py`
- Modify: `backend/src/containers/shared.py` (add `note_repository` provider)
- Modify: `backend/src/containers/root.py` (add `notes` container)
- Modify: `backend/src/main.py` (register router)
- Modify: `backend/src/domain/reading/exceptions.py` (add `HighlightNotFoundError` / `HighlightTagNotFoundError` ONLY if missing — grep first)
- Test: `backend/tests/test_notes.py`

**Interfaces:**
- Consumes: `NoteRepositoryProtocol` (Task 3), existing protocols `BookRepositoryProtocol` (`find_by_id`), `ChapterRepositoryProtocol` (`find_by_id`), `HighlightRepositoryProtocol` (`find_by_id`), `HighlightTagRepositoryProtocol` (`find_by_id`).
- Produces (Tasks 5–6 rely on these):
  - `parse_note_kind(kind: str | None) -> NoteKind | None` and `validate_link_targets(user_id: UserId, allowed_book_ids: set[int], chapter_ids: list[int], highlight_ids: list[int], highlight_tag_ids: list[int], chapter_repository, highlight_repository, highlight_tag_repository) -> None` in `helpers.py`
  - `NoteWithLinkedEntities` DTO in `dtos.py`
  - `CreateNoteUseCase.create_note(user_id: int, title: str, body: str, kind: str | None, book_id: int, chapter_ids: list[int], highlight_ids: list[int], highlight_tag_ids: list[int]) -> Note`
  - `GetNoteUseCase.get_note(note_id: int, user_id: int) -> NoteWithLinkedEntities`
  - Schemas: `Note`, `NoteWithLinks`, `NoteCreateRequest`, `NoteCreateResponse`, `NoteLinkedChapter`, `NoteLinkedHighlight`, `NoteLinkedTag` (+ in Tasks 5/6: `NotesResponse`, `NoteUpdateRequest`, `NoteUpdateResponse`, `NoteDeleteResponse`)
  - Router registered so paths are `POST /api/v1/notes` and `GET /api/v1/notes/{note_id}`, tag `notes`
  - `container.notes.<use_case_name>` providers

- [ ] **Step 1: Write the failing API tests**

`backend/tests/test_notes.py`:

```python
"""Tests for notes API endpoints."""

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class TestCreateNote:
    """Test suite for POST /notes endpoint."""

    async def test_create_note_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_chapter: models.Chapter,
        test_user: models.User,
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "body": "Main character",
                "kind": "character",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        note = data["note"]
        assert note["title"] == "Raskolnikov"
        assert note["kind"] == "character"
        assert note["book_ids"] == [test_book.id]
        assert note["chapter_ids"] == [test_chapter.id]
        assert note["user_id"] == test_user.id
        result = await db_session.execute(select(models.Note).filter_by(id=note["id"]))
        assert result.scalar_one_or_none() is not None

    async def test_create_note_minimal(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "Stoicism", "book_id": test_book.id},
        )
        assert response.status_code == status.HTTP_201_CREATED
        note = response.json()["note"]
        assert note["body"] == ""
        assert note["kind"] is None
        assert note["chapter_ids"] == []

    async def test_create_note_book_not_found(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/notes", json={"title": "Orphan", "book_id": 99999}
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_note_empty_title(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes", json={"title": "", "book_id": test_book.id}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_note_invalid_kind(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "kind": "villain"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    async def test_create_note_chapter_not_found(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "chapter_ids": [99999]},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_note_chapter_from_other_book_rejected(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_user: models.User,
    ) -> None:
        other_book = models.Book(user_id=test_user.id, title="Other book")
        db_session.add(other_book)
        await db_session.commit()
        await db_session.refresh(other_book)
        other_chapter = models.Chapter(book_id=other_book.id, name="Other chapter")
        db_session.add(other_chapter)
        await db_session.commit()
        await db_session.refresh(other_chapter)

        response = await client.post(
            "/api/v1/notes",
            json={"title": "X", "book_id": test_book.id, "chapter_ids": [other_chapter.id]},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetNote:
    """Test suite for GET /notes/{note_id} endpoint."""

    async def test_get_note_with_links(
        self,
        client: AsyncClient,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> None:
        create = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        note_id = create.json()["note"]["id"]

        response = await client.get(f"/api/v1/notes/{note_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Raskolnikov"
        assert data["chapters"] == [{"id": test_chapter.id, "name": test_chapter.name}]
        assert data["highlights"] == []
        assert data["highlight_tags"] == []

    async def test_get_note_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/notes/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

Note: check the `models.Book` and `models.Chapter` constructor kwargs used by the existing `test_book`/`test_chapter` fixtures in `conftest.py` — if they require more fields (e.g. `client_book_id`), match the fixture style in `test_create_note_chapter_from_other_book_rejected`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_notes.py -v`
Expected: FAIL — 404s from missing routes (or import errors once files are partially added)

- [ ] **Step 3: Check for existing NotFound exceptions**

Run: `grep -n "HighlightNotFoundError\|HighlightTagNotFoundError" backend/src/domain/reading/exceptions.py`

If either is missing, add to `backend/src/domain/reading/exceptions.py` following the existing pattern:

```python
class HighlightNotFoundError(EntityNotFoundError):
    """Raised when a highlight cannot be found."""

    def __init__(self, highlight_id: int) -> None:
        super().__init__("Highlight", highlight_id)


class HighlightTagNotFoundError(EntityNotFoundError):
    """Raised when a highlight tag cannot be found."""

    def __init__(self, tag_id: int) -> None:
        super().__init__("HighlightTag", tag_id)
```

- [ ] **Step 4: Create use-case helpers and DTO**

`backend/src/application/notes/use_cases/__init__.py`:

```python
"""Notes use cases."""
```

`backend/src/application/notes/use_cases/helpers.py`:

```python
"""Shared helpers for note use cases."""

from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.exceptions import ValidationError
from src.domain.common.value_objects import ChapterId, HighlightId, HighlightTagId, UserId
from src.domain.notes.entities.note import NoteKind
from src.domain.notes.exceptions import NoteLinkBookMismatchError
from src.domain.reading.exceptions import (
    ChapterNotFoundError,
    HighlightNotFoundError,
    HighlightTagNotFoundError,
)


def parse_note_kind(kind: str | None) -> NoteKind | None:
    """Convert an API kind string to NoteKind, or raise ValidationError."""
    if kind is None:
        return None
    try:
        return NoteKind(kind)
    except ValueError as exc:
        raise ValidationError(f"Invalid note kind: {kind}") from exc


async def validate_link_targets(
    user_id: UserId,
    allowed_book_ids: set[int],
    chapter_ids: list[int],
    highlight_ids: list[int],
    highlight_tag_ids: list[int],
    chapter_repository: ChapterRepositoryProtocol,
    highlight_repository: HighlightRepositoryProtocol,
    highlight_tag_repository: HighlightTagRepositoryProtocol,
) -> None:
    """Validate that every linked entity exists and belongs to a linked book."""
    for chapter_id in chapter_ids:
        chapter = await chapter_repository.find_by_id(ChapterId(chapter_id), user_id)
        if not chapter:
            raise ChapterNotFoundError(chapter_id)
        if chapter.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("Chapter", chapter_id)

    for highlight_id in highlight_ids:
        highlight = await highlight_repository.find_by_id(HighlightId(highlight_id), user_id)
        if not highlight:
            raise HighlightNotFoundError(highlight_id)
        if highlight.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("Highlight", highlight_id)

    for tag_id in highlight_tag_ids:
        tag = await highlight_tag_repository.find_by_id(HighlightTagId(tag_id), user_id)
        if not tag:
            raise HighlightTagNotFoundError(tag_id)
        if tag.book_id.value not in allowed_book_ids:
            raise NoteLinkBookMismatchError("HighlightTag", tag_id)
```

Note: `Chapter.book_id` — verify whether the domain `Chapter` stores `book_id` as `BookId` or plain `int` (check `src/domain/library/entities/chapter.py`); use `.value` only if it's a value object. Same check for `Highlight.book_id` and `HighlightTag.book_id`. Adjust the comparisons accordingly.

`backend/src/application/notes/use_cases/dtos.py`:

```python
"""DTOs for note use cases."""

from dataclasses import dataclass

from src.domain.library.entities.chapter import Chapter
from src.domain.notes.entities.note import Note
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag


@dataclass
class NoteWithLinkedEntities:
    """A note together with the linked entities needed for display."""

    note: Note
    chapters: list[Chapter]
    highlights: list[Highlight]
    highlight_tags: list[HighlightTag]
```

- [ ] **Step 5: Create the use cases**

`backend/src/application/notes/use_cases/create_note_use_case.py`:

```python
"""Use case for creating notes."""

import structlog

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.helpers import parse_note_kind, validate_link_targets
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, UserId
from src.domain.notes.entities.note import Note
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class CreateNoteUseCase:
    """Use case for creating notes."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository

    async def create_note(
        self,
        user_id: int,
        title: str,
        body: str,
        kind: str | None,
        book_id: int,
        chapter_ids: list[int],
        highlight_ids: list[int],
        highlight_tag_ids: list[int],
    ) -> Note:
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        await validate_link_targets(
            user_id=user_id_vo,
            allowed_book_ids={book_id},
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
            chapter_repository=self.chapter_repository,
            highlight_repository=self.highlight_repository,
            highlight_tag_repository=self.highlight_tag_repository,
        )

        note = Note.create(
            user_id=user_id_vo,
            title=title,
            body=body,
            kind=parse_note_kind(kind),
            book_ids=[book_id],
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
        )
        note = await self.note_repository.save(note)

        logger.info("created_note", note_id=note.id.value, book_id=book_id)
        return note
```

`backend/src/application/notes/use_cases/get_note_use_case.py`:

```python
"""Use case for retrieving a single note with linked entities."""

from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import ChapterId, HighlightId, HighlightTagId, NoteId, UserId
from src.domain.notes.exceptions import NoteNotFoundError


class GetNoteUseCase:
    """Use case for retrieving a single note with linked entities."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository

    async def get_note(self, note_id: int, user_id: int) -> NoteWithLinkedEntities:
        user_id_vo = UserId(user_id)
        note = await self.note_repository.find_by_id(NoteId(note_id), user_id_vo)
        if not note:
            raise NoteNotFoundError(note_id)

        chapters = []
        for chapter_id in note.chapter_ids:
            chapter = await self.chapter_repository.find_by_id(ChapterId(chapter_id), user_id_vo)
            if chapter:
                chapters.append(chapter)

        highlights = []
        for highlight_id in note.highlight_ids:
            highlight = await self.highlight_repository.find_by_id(
                HighlightId(highlight_id), user_id_vo
            )
            # Soft-deleted highlights keep their link rows but are hidden from display
            if highlight and highlight.deleted_at is None:
                highlights.append(highlight)

        highlight_tags = []
        for tag_id in note.highlight_tag_ids:
            tag = await self.highlight_tag_repository.find_by_id(
                HighlightTagId(tag_id), user_id_vo
            )
            if tag:
                highlight_tags.append(tag)

        return NoteWithLinkedEntities(
            note=note,
            chapters=chapters,
            highlights=highlights,
            highlight_tags=highlight_tags,
        )
```

- [ ] **Step 6: Create the schemas**

`backend/src/infrastructure/notes/schemas/note_schemas.py`:

```python
"""Pydantic schemas for Note API request/response validation."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NoteKindLiteral = Literal["character", "term", "concept", "other"]


class NoteLinkedChapter(BaseModel):
    """Lightweight summary of a chapter linked to a note."""

    id: int
    name: str


class NoteLinkedHighlight(BaseModel):
    """Lightweight summary of a highlight linked to a note."""

    id: int
    text: str


class NoteLinkedTag(BaseModel):
    """Lightweight summary of a highlight tag linked to a note."""

    id: int
    name: str


class Note(BaseModel):
    """Schema for Note response."""

    id: int
    user_id: int
    title: str
    body: str
    kind: str | None
    book_ids: list[int]
    chapter_ids: list[int]
    highlight_ids: list[int]
    highlight_tag_ids: list[int]
    created_at: datetime
    updated_at: datetime


class NoteWithLinks(Note):
    """Note response with linked entity summaries."""

    chapters: list[NoteLinkedChapter] = Field(default_factory=list)
    highlights: list[NoteLinkedHighlight] = Field(default_factory=list)
    highlight_tags: list[NoteLinkedTag] = Field(default_factory=list)


class NoteCreateRequest(BaseModel):
    """Schema for creating a note."""

    title: str = Field(..., min_length=1, description="Note title")
    body: str = Field("", description="Markdown body")
    kind: NoteKindLiteral | None = Field(None, description="Optional note kind")
    book_id: int = Field(..., description="Book this note is created in")
    chapter_ids: list[int] = Field(default_factory=list)
    highlight_ids: list[int] = Field(default_factory=list)
    highlight_tag_ids: list[int] = Field(default_factory=list)


class NoteCreateResponse(BaseModel):
    """Schema for note creation response."""

    success: bool = Field(..., description="Whether the creation was successful")
    message: str = Field(..., description="Response message")
    note: Note = Field(..., description="Created note")


class NoteUpdateRequest(BaseModel):
    """Schema for updating a note (full replace of fields and links)."""

    title: str = Field(..., min_length=1, description="Note title")
    body: str = Field("", description="Markdown body")
    kind: NoteKindLiteral | None = Field(None, description="Optional note kind")
    chapter_ids: list[int] = Field(default_factory=list)
    highlight_ids: list[int] = Field(default_factory=list)
    highlight_tag_ids: list[int] = Field(default_factory=list)


class NoteUpdateResponse(BaseModel):
    """Schema for note update response."""

    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Response message")
    note: Note = Field(..., description="Updated note")


class NoteDeleteResponse(BaseModel):
    """Schema for note deletion response."""

    success: bool = Field(..., description="Whether the deletion was successful")
    message: str = Field(..., description="Response message")


class NotesResponse(BaseModel):
    """Schema for a list of notes with linked entity summaries."""

    notes: list[NoteWithLinks] = Field(..., description="Notes for the book")
```

`backend/src/infrastructure/notes/schemas/__init__.py`:

```python
"""Notes API schemas."""

from src.infrastructure.notes.schemas.note_schemas import (
    Note,
    NoteCreateRequest,
    NoteCreateResponse,
    NoteDeleteResponse,
    NoteLinkedChapter,
    NoteLinkedHighlight,
    NoteLinkedTag,
    NotesResponse,
    NoteUpdateRequest,
    NoteUpdateResponse,
    NoteWithLinks,
)

__all__ = [
    "Note",
    "NoteCreateRequest",
    "NoteCreateResponse",
    "NoteDeleteResponse",
    "NoteLinkedChapter",
    "NoteLinkedHighlight",
    "NoteLinkedTag",
    "NotesResponse",
    "NoteUpdateRequest",
    "NoteUpdateResponse",
    "NoteWithLinks",
]
```

(`NoteUpdateRequest`/`NoteUpdateResponse`/`NoteDeleteResponse`/`NotesResponse` are defined now but used in Tasks 5–6.)

- [ ] **Step 7: Create the router**

`backend/src/infrastructure/notes/routers/__init__.py`:

```python
"""Notes routers."""
```

`backend/src/infrastructure/notes/routers/notes.py`:

```python
"""API routes for note management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.application.notes.use_cases.create_note_use_case import CreateNoteUseCase
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.notes.use_cases.get_note_use_case import GetNoteUseCase
from src.core import container
from src.domain.identity import User
from src.domain.notes.entities.note import Note as NoteEntity
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.notes.schemas import (
    Note,
    NoteCreateRequest,
    NoteCreateResponse,
    NoteLinkedChapter,
    NoteLinkedHighlight,
    NoteLinkedTag,
    NoteWithLinks,
)

router = APIRouter(tags=["notes"])

HIGHLIGHT_SNIPPET_LENGTH = 200


def note_entity_to_schema(entity: NoteEntity) -> Note:
    """Convert a Note domain entity to its response schema."""
    return Note(
        id=entity.id.value,
        user_id=entity.user_id.value,
        title=entity.title,
        body=entity.body,
        kind=entity.kind.value if entity.kind else None,
        book_ids=entity.book_ids,
        chapter_ids=entity.chapter_ids,
        highlight_ids=entity.highlight_ids,
        highlight_tag_ids=entity.highlight_tag_ids,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def note_with_links_to_schema(dto: NoteWithLinkedEntities) -> NoteWithLinks:
    """Convert a NoteWithLinkedEntities DTO to its response schema."""
    base = note_entity_to_schema(dto.note)
    return NoteWithLinks(
        **base.model_dump(),
        chapters=[
            NoteLinkedChapter(id=chapter.id.value, name=chapter.name) for chapter in dto.chapters
        ],
        highlights=[
            NoteLinkedHighlight(
                id=highlight.id.value, text=highlight.text[:HIGHLIGHT_SNIPPET_LENGTH]
            )
            for highlight in dto.highlights
        ],
        highlight_tags=[
            NoteLinkedTag(id=tag.id.value, name=tag.name) for tag in dto.highlight_tags
        ],
    )


@router.post(
    "/notes",
    response_model=NoteCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    request: NoteCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CreateNoteUseCase = Depends(inject_use_case(container.notes.create_note_use_case)),
) -> NoteCreateResponse:
    note_entity = await use_case.create_note(
        user_id=current_user.id.value,
        title=request.title,
        body=request.body,
        kind=request.kind,
        book_id=request.book_id,
        chapter_ids=request.chapter_ids,
        highlight_ids=request.highlight_ids,
        highlight_tag_ids=request.highlight_tag_ids,
    )
    return NoteCreateResponse(
        success=True,
        message="Note created successfully",
        note=note_entity_to_schema(note_entity),
    )


@router.get(
    "/notes/{note_id}",
    response_model=NoteWithLinks,
    status_code=status.HTTP_200_OK,
)
async def get_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetNoteUseCase = Depends(inject_use_case(container.notes.get_note_use_case)),
) -> NoteWithLinks:
    dto = await use_case.get_note(note_id=note_id, user_id=current_user.id.value)
    return note_with_links_to_schema(dto)
```

Note: `Chapter.id`/`Highlight.id`/`HighlightTag.id` are value objects (`.value`); `chapter.name` and `tag.name` are plain strings. Verify `Chapter.chapter_number` isn't needed — spec only requires the name.

- [ ] **Step 8: Wire the DI container**

`backend/src/containers/notes.py`:

```python
from dependency_injector import containers, providers

from src.application.notes.use_cases.create_note_use_case import CreateNoteUseCase
from src.application.notes.use_cases.get_note_use_case import GetNoteUseCase


class NotesContainer(containers.DeclarativeContainer):
    """Notes module use cases."""

    # Dependencies from shared
    note_repository = providers.Dependency()
    book_repository = providers.Dependency()
    chapter_repository = providers.Dependency()
    highlight_repository = providers.Dependency()
    highlight_tag_repository = providers.Dependency()

    create_note_use_case = providers.Factory(
        CreateNoteUseCase,
        note_repository=note_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
    get_note_use_case = providers.Factory(
        GetNoteUseCase,
        note_repository=note_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
```

In `backend/src/containers/shared.py`, add next to the other repository providers (matching import style):

```python
from src.infrastructure.notes.repositories.note_repository import NoteRepository
# ... in the container class:
    note_repository = providers.Factory(NoteRepository, db=db)
```

In `backend/src/containers/root.py`, add (verify the exact shared provider names for book/chapter/highlight/highlight_tag repositories by reading the file — they are used by the existing `learning` container wiring):

```python
from src.containers.notes import NotesContainer
# ... in RootContainer:
    notes = providers.Container(
        NotesContainer,
        note_repository=shared.note_repository,
        book_repository=shared.book_repository,
        chapter_repository=shared.chapter_repository,
        highlight_repository=shared.highlight_repository,
        highlight_tag_repository=shared.highlight_tag_repository,
    )
```

In `backend/src/main.py`, add to the router imports and registrations:

```python
from src.infrastructure.notes.routers import notes as notes_router
# ... with the other include_router calls:
app.include_router(notes_router.router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 9: Run the Task 4 tests**

Run: `cd backend && uv run pytest tests/test_notes.py -v`
Expected: all PASS

- [ ] **Step 10: Type-check, lint, full suite**

Run: `cd backend && uv run pyright src/ && uv run ruff check src/ tests/test_notes.py && uv run pytest -q`
Expected: no errors, all tests pass

- [ ] **Step 11: Commit**

```bash
git add backend/src backend/tests/test_notes.py
git commit -m "feat: add note create and get endpoints"
```

---

### Task 5: List-by-book endpoint with filters

**Files:**
- Create: `backend/src/application/notes/use_cases/get_notes_by_book_use_case.py`
- Modify: `backend/src/containers/notes.py`
- Modify: `backend/src/infrastructure/notes/routers/notes.py`
- Test: `backend/tests/test_notes.py` (append)

**Interfaces:**
- Consumes: `NoteWithLinkedEntities`, `parse_note_kind` (Task 4); repository protocols `chapter_repository.find_all_by_book(book_id, user_id)`, `highlight_repository.find_by_book_id(book_id, user_id)`, `highlight_tag_repository.find_by_book(book_id, user_id)`.
- Produces: `GetNotesByBookUseCase.get_notes(book_id: int, user_id: int, kind: str | None = None, chapter_id: int | None = None, highlight_id: int | None = None, highlight_tag_id: int | None = None) -> list[NoteWithLinkedEntities]`; endpoint `GET /api/v1/books/{book_id}/notes?kind=&chapter_id=&highlight_id=&highlight_tag_id=` (operation `get_notes_for_book`, tag `notes`).

- [ ] **Step 1: Write the failing tests (append to `backend/tests/test_notes.py`)**

```python
class TestGetNotesForBook:
    """Test suite for GET /books/{book_id}/notes endpoint."""

    @pytest.fixture
    async def two_notes(
        self,
        client: AsyncClient,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> tuple[int, int]:
        """Create a character note (linked to chapter) and a concept note."""
        first = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "kind": "character",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        second = await client.post(
            "/api/v1/notes",
            json={"title": "Nihilism", "kind": "concept", "book_id": test_book.id},
        )
        return first.json()["note"]["id"], second.json()["note"]["id"]

    async def test_list_notes(
        self, client: AsyncClient, test_book: models.Book, two_notes: tuple[int, int]
    ) -> None:
        response = await client.get(f"/api/v1/books/{test_book.id}/notes")
        assert response.status_code == status.HTTP_200_OK
        notes = response.json()["notes"]
        assert len(notes) == 2

    async def test_list_notes_includes_link_summaries(
        self,
        client: AsyncClient,
        test_book: models.Book,
        test_chapter: models.Chapter,
        two_notes: tuple[int, int],
    ) -> None:
        response = await client.get(f"/api/v1/books/{test_book.id}/notes")
        notes = response.json()["notes"]
        raskolnikov = next(n for n in notes if n["title"] == "Raskolnikov")
        assert raskolnikov["chapters"] == [{"id": test_chapter.id, "name": test_chapter.name}]

    async def test_list_notes_filter_by_kind(
        self, client: AsyncClient, test_book: models.Book, two_notes: tuple[int, int]
    ) -> None:
        response = await client.get(f"/api/v1/books/{test_book.id}/notes?kind=character")
        notes = response.json()["notes"]
        assert len(notes) == 1
        assert notes[0]["title"] == "Raskolnikov"

    async def test_list_notes_filter_by_chapter(
        self,
        client: AsyncClient,
        test_book: models.Book,
        test_chapter: models.Chapter,
        two_notes: tuple[int, int],
    ) -> None:
        response = await client.get(
            f"/api/v1/books/{test_book.id}/notes?chapter_id={test_chapter.id}"
        )
        notes = response.json()["notes"]
        assert len(notes) == 1
        assert notes[0]["title"] == "Raskolnikov"

    async def test_list_notes_empty(self, client: AsyncClient, test_book: models.Book) -> None:
        response = await client.get(f"/api/v1/books/{test_book.id}/notes")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["notes"] == []

    async def test_list_notes_book_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/books/99999/notes")
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

Add `import pytest` to the imports of `tests/test_notes.py`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_notes.py -v -k TestGetNotesForBook`
Expected: FAIL with 404 (route doesn't exist)

- [ ] **Step 3: Create the use case**

`backend/src/application/notes/use_cases/get_notes_by_book_use_case.py`:

```python
"""Use case for retrieving notes for a book with linked entities."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.dtos import NoteWithLinkedEntities
from src.application.notes.use_cases.helpers import parse_note_kind
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import BookId, ChapterId, HighlightId, HighlightTagId, UserId
from src.domain.reading.exceptions import BookNotFoundError


class GetNotesByBookUseCase:
    """Use case for retrieving notes for a book with linked entities."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository

    async def get_notes(
        self,
        book_id: int,
        user_id: int,
        kind: str | None = None,
        chapter_id: int | None = None,
        highlight_id: int | None = None,
        highlight_tag_id: int | None = None,
    ) -> list[NoteWithLinkedEntities]:
        user_id_vo = UserId(user_id)
        book_id_vo = BookId(book_id)

        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        notes = await self.note_repository.find_by_book(
            book_id_vo,
            user_id_vo,
            kind=parse_note_kind(kind),
            chapter_id=ChapterId(chapter_id) if chapter_id is not None else None,
            highlight_id=HighlightId(highlight_id) if highlight_id is not None else None,
            highlight_tag_id=(
                HighlightTagId(highlight_tag_id) if highlight_tag_id is not None else None
            ),
        )
        if not notes:
            return []

        # Batch-load the book's entities once and resolve links from maps.
        # Soft-deleted highlights are excluded by find_by_book_id, so linked
        # deleted highlights silently drop out of the summaries.
        chapters_by_id = {
            chapter.id.value: chapter
            for chapter in await self.chapter_repository.find_all_by_book(book_id_vo, user_id_vo)
        }
        highlights_by_id = {
            highlight.id.value: highlight
            for highlight in await self.highlight_repository.find_by_book_id(
                book_id_vo, user_id_vo
            )
        }
        tags_by_id = {
            tag.id.value: tag
            for tag in await self.highlight_tag_repository.find_by_book(book_id_vo, user_id_vo)
        }

        return [
            NoteWithLinkedEntities(
                note=note,
                chapters=[
                    chapters_by_id[cid] for cid in note.chapter_ids if cid in chapters_by_id
                ],
                highlights=[
                    highlights_by_id[hid] for hid in note.highlight_ids if hid in highlights_by_id
                ],
                highlight_tags=[
                    tags_by_id[tid] for tid in note.highlight_tag_ids if tid in tags_by_id
                ],
            )
            for note in notes
        ]
```

- [ ] **Step 4: Wire and expose the endpoint**

Add to `backend/src/containers/notes.py`:

```python
from src.application.notes.use_cases.get_notes_by_book_use_case import GetNotesByBookUseCase
# ... in NotesContainer:
    get_notes_by_book_use_case = providers.Factory(
        GetNotesByBookUseCase,
        note_repository=note_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
```

Add to `backend/src/infrastructure/notes/routers/notes.py` (import `GetNotesByBookUseCase`, `NotesResponse`, and `NoteKindLiteral` from the schemas module; add `Query` to fastapi imports):

```python
@router.get(
    "/books/{book_id}/notes",
    response_model=NotesResponse,
    status_code=status.HTTP_200_OK,
)
async def get_notes_for_book(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    kind: Annotated[NoteKindLiteral | None, Query()] = None,
    chapter_id: Annotated[int | None, Query()] = None,
    highlight_id: Annotated[int | None, Query()] = None,
    highlight_tag_id: Annotated[int | None, Query()] = None,
    use_case: GetNotesByBookUseCase = Depends(
        inject_use_case(container.notes.get_notes_by_book_use_case)
    ),
) -> NotesResponse:
    dtos = await use_case.get_notes(
        book_id=book_id,
        user_id=current_user.id.value,
        kind=kind,
        chapter_id=chapter_id,
        highlight_id=highlight_id,
        highlight_tag_id=highlight_tag_id,
    )
    return NotesResponse(notes=[note_with_links_to_schema(dto) for dto in dtos])
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_notes.py -v`
Expected: all PASS

- [ ] **Step 6: Type-check, lint, full suite**

Run: `cd backend && uv run pyright src/application/notes src/infrastructure/notes src/containers && uv run ruff check src/ tests/test_notes.py && uv run pytest -q`
Expected: no errors

- [ ] **Step 7: Commit**

```bash
git add backend/src backend/tests/test_notes.py
git commit -m "feat: add list notes by book endpoint with filters"
```

---

### Task 6: Update + Delete endpoints

**Files:**
- Create: `backend/src/application/notes/use_cases/update_note_use_case.py`
- Create: `backend/src/application/notes/use_cases/delete_note_use_case.py`
- Modify: `backend/src/containers/notes.py`
- Modify: `backend/src/infrastructure/notes/routers/notes.py`
- Test: `backend/tests/test_notes.py` (append)

**Interfaces:**
- Consumes: `validate_link_targets`, `parse_note_kind` (Task 4).
- Produces: `UpdateNoteUseCase.update_note(note_id: int, user_id: int, title: str, body: str, kind: str | None, chapter_ids: list[int], highlight_ids: list[int], highlight_tag_ids: list[int]) -> Note`; `DeleteNoteUseCase.delete_note(note_id: int, user_id: int) -> None`; endpoints `PUT /api/v1/notes/{note_id}` (operation `update_note`) and `DELETE /api/v1/notes/{note_id}` (operation `delete_note`).

- [ ] **Step 1: Write the failing tests (append to `backend/tests/test_notes.py`)**

```python
class TestUpdateNote:
    """Test suite for PUT /notes/{note_id} endpoint."""

    @pytest.fixture
    async def note_id(
        self, client: AsyncClient, test_book: models.Book, test_chapter: models.Chapter
    ) -> int:
        response = await client.post(
            "/api/v1/notes",
            json={
                "title": "Raskolnikov",
                "kind": "character",
                "book_id": test_book.id,
                "chapter_ids": [test_chapter.id],
            },
        )
        return response.json()["note"]["id"]

    async def test_update_note_fields_and_links(
        self,
        client: AsyncClient,
        note_id: int,
        test_highlight: models.Highlight,
    ) -> None:
        response = await client.put(
            f"/api/v1/notes/{note_id}",
            json={
                "title": "Rodion Raskolnikov",
                "body": "Updated body",
                "kind": "character",
                "chapter_ids": [],
                "highlight_ids": [test_highlight.id],
                "highlight_tag_ids": [],
            },
        )
        assert response.status_code == status.HTTP_200_OK
        note = response.json()["note"]
        assert note["title"] == "Rodion Raskolnikov"
        assert note["body"] == "Updated body"
        assert note["chapter_ids"] == []
        assert note["highlight_ids"] == [test_highlight.id]

    async def test_update_note_not_found(self, client: AsyncClient) -> None:
        response = await client.put(
            "/api/v1/notes/99999",
            json={"title": "X", "body": "", "kind": None},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_update_note_invalid_chapter(
        self, client: AsyncClient, note_id: int
    ) -> None:
        response = await client.put(
            f"/api/v1/notes/{note_id}",
            json={"title": "X", "body": "", "kind": None, "chapter_ids": [99999]},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteNote:
    """Test suite for DELETE /notes/{note_id} endpoint."""

    async def test_delete_note(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
    ) -> None:
        create = await client.post(
            "/api/v1/notes", json={"title": "Doomed", "book_id": test_book.id}
        )
        note_id = create.json()["note"]["id"]

        response = await client.delete(f"/api/v1/notes/{note_id}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["success"] is True
        result = await db_session.execute(select(models.Note).filter_by(id=note_id))
        assert result.scalar_one_or_none() is None

    async def test_delete_note_not_found(self, client: AsyncClient) -> None:
        response = await client.delete("/api/v1/notes/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_note_deleted_when_book_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
    ) -> None:
        create = await client.post(
            "/api/v1/notes", json={"title": "Cascade", "book_id": test_book.id}
        )
        note_id = create.json()["note"]["id"]

        response = await client.delete(f"/api/v1/books/{test_book.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # The note_books link row is gone; the note itself remains (user-scoped)
        # but is no longer reachable via any book listing.
        result = await db_session.execute(
            select(models.note_books).filter_by(note_id=note_id)
        )
        assert result.first() is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_notes.py -v -k "TestUpdateNote or TestDeleteNote"`
Expected: FAIL with 405/404 (routes don't exist)

- [ ] **Step 3: Create the use cases**

`backend/src/application/notes/use_cases/update_note_use_case.py`:

```python
"""Use case for updating notes."""

import structlog

from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.application.notes.use_cases.helpers import parse_note_kind, validate_link_targets
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects import NoteId, UserId
from src.domain.notes.entities.note import Note
from src.domain.notes.exceptions import NoteNotFoundError

logger = structlog.get_logger(__name__)


class UpdateNoteUseCase:
    """Use case for updating notes (full replace of content and links)."""

    def __init__(
        self,
        note_repository: NoteRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        highlight_tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.note_repository = note_repository
        self.chapter_repository = chapter_repository
        self.highlight_repository = highlight_repository
        self.highlight_tag_repository = highlight_tag_repository

    async def update_note(
        self,
        note_id: int,
        user_id: int,
        title: str,
        body: str,
        kind: str | None,
        chapter_ids: list[int],
        highlight_ids: list[int],
        highlight_tag_ids: list[int],
    ) -> Note:
        user_id_vo = UserId(user_id)
        note = await self.note_repository.find_by_id(NoteId(note_id), user_id_vo)
        if not note:
            raise NoteNotFoundError(note_id)

        await validate_link_targets(
            user_id=user_id_vo,
            allowed_book_ids=set(note.book_ids),
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
            chapter_repository=self.chapter_repository,
            highlight_repository=self.highlight_repository,
            highlight_tag_repository=self.highlight_tag_repository,
        )

        note.update_content(title=title, body=body, kind=parse_note_kind(kind))
        note.replace_links(
            book_ids=note.book_ids,  # book links unchanged in v1
            chapter_ids=chapter_ids,
            highlight_ids=highlight_ids,
            highlight_tag_ids=highlight_tag_ids,
        )
        note = await self.note_repository.save(note)

        logger.info("updated_note", note_id=note_id)
        return note
```

`backend/src/application/notes/use_cases/delete_note_use_case.py`:

```python
"""Use case for deleting notes."""

import structlog

from src.application.notes.protocols.note_repository import NoteRepositoryProtocol
from src.domain.common.value_objects import NoteId, UserId
from src.domain.notes.exceptions import NoteNotFoundError

logger = structlog.get_logger(__name__)


class DeleteNoteUseCase:
    """Use case for deleting notes."""

    def __init__(self, note_repository: NoteRepositoryProtocol) -> None:
        self.note_repository = note_repository

    async def delete_note(self, note_id: int, user_id: int) -> None:
        deleted = await self.note_repository.delete(NoteId(note_id), UserId(user_id))
        if not deleted:
            raise NoteNotFoundError(note_id)
        logger.info("deleted_note", note_id=note_id)
```

- [ ] **Step 4: Wire and expose the endpoints**

Add to `backend/src/containers/notes.py`:

```python
from src.application.notes.use_cases.delete_note_use_case import DeleteNoteUseCase
from src.application.notes.use_cases.update_note_use_case import UpdateNoteUseCase
# ... in NotesContainer:
    update_note_use_case = providers.Factory(
        UpdateNoteUseCase,
        note_repository=note_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
    delete_note_use_case = providers.Factory(
        DeleteNoteUseCase,
        note_repository=note_repository,
    )
```

Add to `backend/src/infrastructure/notes/routers/notes.py` (import `UpdateNoteUseCase`, `DeleteNoteUseCase`, `NoteUpdateRequest`, `NoteUpdateResponse`, `NoteDeleteResponse`):

```python
@router.put(
    "/notes/{note_id}",
    response_model=NoteUpdateResponse,
    status_code=status.HTTP_200_OK,
)
async def update_note(
    note_id: int,
    request: NoteUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: UpdateNoteUseCase = Depends(inject_use_case(container.notes.update_note_use_case)),
) -> NoteUpdateResponse:
    note_entity = await use_case.update_note(
        note_id=note_id,
        user_id=current_user.id.value,
        title=request.title,
        body=request.body,
        kind=request.kind,
        chapter_ids=request.chapter_ids,
        highlight_ids=request.highlight_ids,
        highlight_tag_ids=request.highlight_tag_ids,
    )
    return NoteUpdateResponse(
        success=True,
        message="Note updated successfully",
        note=note_entity_to_schema(note_entity),
    )


@router.delete(
    "/notes/{note_id}",
    response_model=NoteDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_note(
    note_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: DeleteNoteUseCase = Depends(inject_use_case(container.notes.delete_note_use_case)),
) -> NoteDeleteResponse:
    await use_case.delete_note(note_id=note_id, user_id=current_user.id.value)
    return NoteDeleteResponse(success=True, message="Note deleted successfully")
```

- [ ] **Step 5: Run tests, type-check, lint, full suite**

Run: `cd backend && uv run pytest tests/test_notes.py -v && uv run pyright src/ && uv run ruff check src/ tests/ && uv run pytest -q`
Expected: all PASS, no errors

- [ ] **Step 6: Commit**

```bash
git add backend/src backend/tests/test_notes.py
git commit -m "feat: add note update and delete endpoints"
```

---

### Task 7: Regenerate the frontend API client

**Files:**
- Modify (generated): `frontend/src/api/generated/**` (orval output — `notes/notes.ts` + model files appear)

**Interfaces:**
- Produces generated hooks used by Tasks 8–11 (names derive from the backend operation ids):
  - `useCreateNoteApiV1NotesPost`
  - `useGetNotesForBookApiV1BooksBookIdNotesGet` + `getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(bookId)`
  - `useGetNoteApiV1NotesNoteIdGet`
  - `useUpdateNoteApiV1NotesNoteIdPut`
  - `useDeleteNoteApiV1NotesNoteIdDelete`
  - Models: `NoteWithLinks`, `NoteCreateRequest`, `NoteUpdateRequest`, `GetNotesForBookApiV1BooksBookIdNotesGetParams`
  - After generating, verify the exact exported names with `grep -n "export const use" frontend/src/api/generated/notes/notes.ts` and use those in Tasks 8–11 if they differ.

- [ ] **Step 1: Ensure DB is migrated and start the backend**

```bash
cd backend && uv run alembic upgrade head
cd backend && uv run uvicorn src.main:app --port 8000 &
```

(orval reads the OpenAPI spec from the running backend at `http://localhost:8000/api/v1/openapi.json`.)

- [ ] **Step 2: Regenerate**

Run: `cd frontend && npm run api:generate`
Expected: orval completes; `frontend/src/api/generated/notes/notes.ts` exists.

- [ ] **Step 3: Verify frontend still type-checks, then stop the backend**

Run: `cd frontend && npm run type-check`
Expected: no errors. Stop the uvicorn process afterwards.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/generated
git commit -m "chore: regenerate API client with notes endpoints"
```

---

### Task 8: Notes tab — route, navigation, NotesPage, NoteCard, NoteEditorDialog

**Files:**
- Create: `frontend/src/routes/book.$bookId/notes.tsx`
- Modify: `frontend/src/pages/BookPage/navigation/bookPageRoutes.ts`
- Modify: `frontend/src/theme/Icons.tsx` (add `NoteAddIcon` if not present)
- Create: `frontend/src/pages/BookPage/Notes/NotesPage.tsx`
- Create: `frontend/src/pages/BookPage/Notes/NoteCard.tsx`
- Create: `frontend/src/pages/BookPage/Notes/NoteEditorDialog.tsx`
- Create: `frontend/src/pages/BookPage/Notes/noteKinds.ts`

**Interfaces:**
- Consumes: generated hooks from Task 7, `useBookPage()` context (`book: BookDetails`), `CommonDialog`, `ConfirmationDialog`, `IconButtonWithTooltip`, `markdownStyles`, `useSnackbar`.
- Produces (reused by Tasks 9–11 — exact props):
  - `NoteEditorDialog` props: `{ open: boolean; onClose: () => void; note?: NoteWithLinks | null; initialChapterIds?: number[]; initialHighlightIds?: number[]; initialBody?: string }` — create mode when `note` is null/undefined; reads `book` from `useBookPage()`; invalidates the notes list query on save.
  - `NoteCard` props: `{ note: NoteWithLinks; onEdit: () => void; onDelete: () => void }`
  - `NOTE_KINDS` const and `NoteKindValue` type from `noteKinds.ts`.

- [ ] **Step 1: Add the route file**

`frontend/src/routes/book.$bookId/notes.tsx`:

```tsx
import { NotesPage } from '@/pages/BookPage/Notes/NotesPage';
import { createFileRoute } from '@tanstack/react-router';

type NotesSearch = {
  kind?: string;
  chapterId?: number;
  tagId?: number;
};

export const Route = createFileRoute('/book/$bookId/notes')({
  component: NotesPage,
  validateSearch: (search: Record<string, unknown>): NotesSearch => ({
    kind: (search.kind as string | undefined) || undefined,
    chapterId: (search.chapterId as number | undefined) || undefined,
    tagId: (search.tagId as number | undefined) || undefined,
  }),
});
```

- [ ] **Step 2: Add the Notes tab to navigation**

In `frontend/src/pages/BookPage/navigation/bookPageRoutes.ts`:
- Add `| '/book/$bookId/notes'` to the `BookPageRoute` union.
- Import `NotesIcon` from `@/theme/Icons.tsx` (already exported there).
- Add to `BOOK_PAGE_ROUTES` after the flashcards entry:

```ts
  {
    to: '/book/$bookId/notes',
    segment: 'notes',
    label: 'Notes',
    icon: NotesIcon,
  },
```

`DesktopNavLinks` and `MobileBottomNav` iterate this array — no other nav changes needed. Route tree regenerates via `npm run dev` / `npm run routes:generate`.

- [ ] **Step 3: Add `NoteAddIcon` to `frontend/src/theme/Icons.tsx`**

Check first with `grep -n "NoteAdd" frontend/src/theme/Icons.tsx`. If absent, add an export following the file's existing re-export pattern, e.g.:

```tsx
export { default as NoteAddIcon } from '@mui/icons-material/NoteAdd';
```

(match the exact import/export style used by the other icons in that file).

- [ ] **Step 4: Create `noteKinds.ts`, `NoteCard`, `NoteEditorDialog`, `NotesPage`**

`frontend/src/pages/BookPage/Notes/noteKinds.ts`:

```ts
export const NOTE_KINDS = ['character', 'term', 'concept', 'other'] as const;

export type NoteKindValue = (typeof NOTE_KINDS)[number];

export const NOTE_KIND_LABELS: Record<NoteKindValue, string> = {
  character: 'Character',
  term: 'Term',
  concept: 'Concept',
  other: 'Other',
};
```

`frontend/src/pages/BookPage/Notes/NoteCard.tsx`:

```tsx
import type { NoteWithLinks } from '@/api/generated/model';
import { IconButtonWithTooltip } from '@/components/buttons/IconButtonWithTooltip.tsx';
import { DeleteIcon, EditIcon } from '@/theme/Icons.tsx';
import { markdownStyles } from '@/theme/theme';
import { Box, Card, CardContent, Chip, Stack, Typography, useTheme } from '@mui/material';
import ReactMarkdown from 'react-markdown';

import { NOTE_KIND_LABELS, type NoteKindValue } from './noteKinds';

interface NoteCardProps {
  note: NoteWithLinks;
  onEdit: () => void;
  onDelete: () => void;
}

export const NoteCard = ({ note, onEdit, onDelete }: NoteCardProps) => {
  const theme = useTheme();

  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.5 }}>
              <Typography variant="h6">{note.title}</Typography>
              {note.kind && (
                <Chip size="small" label={NOTE_KIND_LABELS[note.kind as NoteKindValue]} />
              )}
            </Stack>
            {note.body && (
              <Box sx={markdownStyles(theme)}>
                <ReactMarkdown>{note.body}</ReactMarkdown>
              </Box>
            )}
            {(note.chapters.length > 0 ||
              note.highlight_tags.length > 0 ||
              note.highlights.length > 0) && (
              <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
                {note.chapters.map((chapter) => (
                  <Chip key={`ch-${chapter.id}`} size="small" variant="outlined" label={chapter.name} />
                ))}
                {note.highlight_tags.map((tag) => (
                  <Chip key={`tag-${tag.id}`} size="small" variant="outlined" label={`#${tag.name}`} />
                ))}
                {note.highlights.length > 0 && (
                  <Chip
                    size="small"
                    variant="outlined"
                    label={`${note.highlights.length} highlight${note.highlights.length === 1 ? '' : 's'}`}
                  />
                )}
              </Stack>
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButtonWithTooltip title="Edit note" ariaLabel="Edit note" onClick={onEdit} icon={<EditIcon />} />
            <IconButtonWithTooltip
              title="Delete note"
              ariaLabel="Delete note"
              onClick={onDelete}
              icon={<DeleteIcon />}
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
```

(Check `IconButtonWithTooltip`'s exact prop names in `frontend/src/components/buttons/IconButtonWithTooltip.tsx` — the Toolbar usage shows `title`, `onClick`, `ariaLabel`, `icon`, `disabled`.)

`frontend/src/pages/BookPage/Notes/NoteEditorDialog.tsx`:

```tsx
import { getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey } from '@/api/generated/notes/notes.ts';
import {
  useCreateNoteApiV1NotesPost,
  useUpdateNoteApiV1NotesNoteIdPut,
} from '@/api/generated/notes/notes.ts';
import type { NoteWithLinks } from '@/api/generated/model';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import {
  Autocomplete,
  Box,
  Button,
  MenuItem,
  TextField,
} from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

interface NoteEditorDialogProps {
  open: boolean;
  onClose: () => void;
  /** Edit mode when set; create mode otherwise */
  note?: NoteWithLinks | null;
  initialChapterIds?: number[];
  initialHighlightIds?: number[];
  initialBody?: string;
}

interface ChapterOption {
  id: number;
  name: string;
}

interface TagOption {
  id: number;
  name: string;
}

export const NoteEditorDialog = ({
  open,
  onClose,
  note,
  initialChapterIds,
  initialHighlightIds,
  initialBody,
}: NoteEditorDialogProps) => {
  const { book } = useBookPage();
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();

  const chapterOptions: ChapterOption[] = book.chapters.map((chapter) => ({
    id: chapter.id,
    name: chapter.name,
  }));
  const tagOptions: TagOption[] = book.highlight_tags.map((tag) => ({
    id: tag.id,
    name: tag.name,
  }));

  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [kind, setKind] = useState<NoteKindValue | ''>('');
  const [chapters, setChapters] = useState<ChapterOption[]>([]);
  const [tags, setTags] = useState<TagOption[]>([]);
  const [highlightIds, setHighlightIds] = useState<number[]>([]);

  useEffect(() => {
    if (!open) return;
    if (note) {
      setTitle(note.title);
      setBody(note.body);
      setKind((note.kind as NoteKindValue | null) ?? '');
      setChapters(chapterOptions.filter((option) => note.chapter_ids.includes(option.id)));
      setTags(tagOptions.filter((option) => note.highlight_tag_ids.includes(option.id)));
      setHighlightIds(note.highlight_ids);
    } else {
      setTitle('');
      setBody(initialBody ?? '');
      setKind('');
      setChapters(chapterOptions.filter((option) => (initialChapterIds ?? []).includes(option.id)));
      setTags([]);
      setHighlightIds(initialHighlightIds ?? []);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, note]);

  const invalidateNotes = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
    });
  };

  const createMutation = useCreateNoteApiV1NotesPost({
    mutation: {
      onSuccess: () => {
        invalidateNotes();
        onClose();
      },
      onError: (error) => {
        console.error('Failed to create note:', error);
        showSnackbar('Failed to create note. Please try again.', 'error');
      },
    },
  });
  const updateMutation = useUpdateNoteApiV1NotesNoteIdPut({
    mutation: {
      onSuccess: () => {
        invalidateNotes();
        onClose();
      },
      onError: (error) => {
        console.error('Failed to update note:', error);
        showSnackbar('Failed to update note. Please try again.', 'error');
      },
    },
  });

  const isSaving = createMutation.isPending || updateMutation.isPending;
  const canSave = title.trim().length > 0 && !isSaving;

  const handleSave = async () => {
    const payload = {
      title: title.trim(),
      body,
      kind: kind === '' ? null : kind,
      chapter_ids: chapters.map((option) => option.id),
      highlight_ids: highlightIds,
      highlight_tag_ids: tags.map((option) => option.id),
    };
    if (note) {
      await updateMutation.mutateAsync({ noteId: note.id, data: payload });
    } else {
      await createMutation.mutateAsync({ data: { ...payload, book_id: book.id } });
    }
  };

  return (
    <CommonDialog
      open={open}
      onClose={onClose}
      title={note ? 'Edit Note' : 'New Note'}
      maxWidth="md"
      isLoading={isSaving}
      footerActions={
        <Box sx={{ display: 'flex', gap: 1, width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={() => void handleSave()} disabled={!canSave}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </Box>
      }
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
        <TextField
          label="Title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          fullWidth
          autoFocus
        />
        <TextField
          select
          label="Kind"
          value={kind}
          onChange={(event) => setKind(event.target.value as NoteKindValue | '')}
          fullWidth
        >
          <MenuItem value="">None</MenuItem>
          {NOTE_KINDS.map((value) => (
            <MenuItem key={value} value={value}>
              {NOTE_KIND_LABELS[value]}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          label="Note (markdown)"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          fullWidth
          multiline
          minRows={5}
        />
        <Autocomplete
          multiple
          options={chapterOptions}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          value={chapters}
          onChange={(_, value) => setChapters(value)}
          renderInput={(params) => <TextField {...params} label="Chapters" />}
        />
        <Autocomplete
          multiple
          options={tagOptions}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          value={tags}
          onChange={(_, value) => setTags(value)}
          renderInput={(params) => <TextField {...params} label="Tags" />}
        />
      </Box>
    </CommonDialog>
  );
};
```

Design decision (from spec discussion): the editor does NOT include a highlight browser — highlight links are added from the highlight modal (Task 9) and passed through unchanged on edit via the `highlightIds` state.

`frontend/src/pages/BookPage/Notes/NotesPage.tsx`:

```tsx
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
  useGetNotesForBookApiV1BooksBookIdNotesGet,
} from '@/api/generated/notes/notes.ts';
import type { GetNotesForBookApiV1BooksBookIdNotesGetParams, NoteWithLinks } from '@/api/generated/model';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { useBookPage } from '@/pages/BookPage/BookPageContext';
import { AddIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useState } from 'react';

import { NoteCard } from './NoteCard';
import { NoteEditorDialog } from './NoteEditorDialog';
import { NOTE_KIND_LABELS, NOTE_KINDS, type NoteKindValue } from './noteKinds';

export const NotesPage = () => {
  const { book } = useBookPage();
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const navigate = useNavigate({ from: '/book/$bookId/notes' });
  const { kind, chapterId, tagId } = useSearch({ from: '/book/$bookId/notes' });

  const params: GetNotesForBookApiV1BooksBookIdNotesGetParams = {
    kind: (kind as NoteKindValue | undefined) ?? undefined,
    chapter_id: chapterId,
    highlight_tag_id: tagId,
  };
  const { data, isLoading, isError } = useGetNotesForBookApiV1BooksBookIdNotesGet(book.id, params);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteWithLinks | null>(null);
  const [deletingNote, setDeletingNote] = useState<NoteWithLinks | null>(null);

  const deleteMutation = useDeleteNoteApiV1NotesNoteIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(book.id),
        });
        setDeletingNote(null);
      },
      onError: (error) => {
        console.error('Failed to delete note:', error);
        showSnackbar('Failed to delete note. Please try again.', 'error');
      },
    },
  });

  const handleKindFilter = (value: NoteKindValue | null) => {
    void navigate({ search: (prev) => ({ ...prev, kind: value ?? undefined }) });
  };

  const notes = data?.data?.notes ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={kind ?? null}
          onChange={(_, value: NoteKindValue | null) => handleKindFilter(value)}
        >
          {NOTE_KINDS.map((value) => (
            <ToggleButton key={value} value={value}>
              {NOTE_KIND_LABELS[value]}
            </ToggleButton>
          ))}
        </ToggleButtonGroup>
        <Box sx={{ flexGrow: 1 }} />
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingNote(null);
            setEditorOpen(true);
          }}
        >
          New note
        </Button>
      </Box>

      {isLoading && <Spinner />}
      {isError && <Typography color="error">Failed to load notes.</Typography>}
      {!isLoading && !isError && notes.length === 0 && (
        <Typography color="text.secondary">
          No notes yet. Create notes about characters, terms, and concepts as you read.
        </Typography>
      )}

      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard
              note={note}
              onEdit={() => {
                setEditingNote(note);
                setEditorOpen(true);
              }}
              onDelete={() => setDeletingNote(note)}
            />
          </li>
        ))}
      </Stack>

      <NoteEditorDialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        note={editingNote}
      />
      <ConfirmationDialog
        open={deletingNote !== null}
        title="Delete note"
        message={`Delete note "${deletingNote?.title ?? ''}"? This cannot be undone.`}
        onConfirm={() => {
          if (deletingNote) {
            void deleteMutation.mutateAsync({ noteId: deletingNote.id });
          }
        }}
        onCancel={() => setDeletingNote(null)}
      />
    </Box>
  );
};
```

Implementation notes:
- Verify `ConfirmationDialog`'s exact prop names in `frontend/src/components/dialogs/ConfirmationDialog.tsx` (it may use `onClose`/`description` instead of `onCancel`/`message`) and adjust.
- Verify the generated hook's response shape: orval + axios returns `AxiosResponse`, so the notes list may be `data?.data?.notes` or `data?.notes` depending on the mutator — check how `FlashcardsPage`/other pages consume generated GET hooks and match.
- The chapter/tag filters (`chapterId`, `tagId` search params) are set by navigation from other views; adding dedicated filter dropdowns on this page is optional — the kind toggle plus URL params satisfies v1. If chips for active chapter/tag filters are trivial to add, include a small `Chip ... onDelete` clearing the param.

- [ ] **Step 5: Verify**

Run: `cd frontend && npm run routes:generate && npm run type-check && npm run lint`
Expected: no errors

Then manually verify: `npm run dev` (backend running), open a book → Notes tab → create, edit, filter, delete a note.

- [ ] **Step 6: Commit**

```bash
git add frontend/src
git commit -m "feat: add notes tab with editor to book page"
```

---

### Task 9: NotesSection in ChapterDetailDialog

**Files:**
- Create: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/NotesSection.tsx`
- Modify: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/ChapterDetailDialog.tsx`

**Interfaces:**
- Consumes: `NoteCard`, `NoteEditorDialog` (Task 8), generated notes hooks, `ConfirmationDialog`.
- Produces: `NotesSection` props `{ chapterId: number; bookId: number }`.

- [ ] **Step 1: Create `NotesSection.tsx`**

```tsx
import {
  getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey,
  useDeleteNoteApiV1NotesNoteIdDelete,
  useGetNotesForBookApiV1BooksBookIdNotesGet,
} from '@/api/generated/notes/notes.ts';
import type { NoteWithLinks } from '@/api/generated/model';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { ConfirmationDialog } from '@/components/dialogs/ConfirmationDialog.tsx';
import { useSnackbar } from '@/context/SnackbarContext.tsx';
import { NoteCard } from '@/pages/BookPage/Notes/NoteCard';
import { NoteEditorDialog } from '@/pages/BookPage/Notes/NoteEditorDialog';
import { AddIcon } from '@/theme/Icons.tsx';
import { Box, Button, Stack, Typography } from '@mui/material';
import { useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface NotesSectionProps {
  chapterId: number;
  bookId: number;
}

export const NotesSection = ({ chapterId, bookId }: NotesSectionProps) => {
  const { showSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, {
    chapter_id: chapterId,
  });

  const [editorOpen, setEditorOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<NoteWithLinks | null>(null);
  const [deletingNote, setDeletingNote] = useState<NoteWithLinks | null>(null);

  const deleteMutation = useDeleteNoteApiV1NotesNoteIdDelete({
    mutation: {
      onSuccess: () => {
        void queryClient.invalidateQueries({
          queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(bookId),
        });
        setDeletingNote(null);
      },
      onError: (error) => {
        console.error('Failed to delete note:', error);
        showSnackbar('Failed to delete note. Please try again.', 'error');
      },
    },
  });

  const notes = data?.data?.notes ?? [];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button
          variant="outlined"
          size="small"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingNote(null);
            setEditorOpen(true);
          }}
        >
          Add note
        </Button>
      </Box>
      {isLoading && <Spinner />}
      {!isLoading && notes.length === 0 && (
        <Typography color="text.secondary">No notes linked to this chapter.</Typography>
      )}
      <Stack component="ul" sx={{ gap: 2, listStyle: 'none', p: 0, m: 0 }}>
        {notes.map((note) => (
          <li key={note.id}>
            <NoteCard
              note={note}
              onEdit={() => {
                setEditingNote(note);
                setEditorOpen(true);
              }}
              onDelete={() => setDeletingNote(note)}
            />
          </li>
        ))}
      </Stack>
      <NoteEditorDialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        note={editingNote}
        initialChapterIds={[chapterId]}
      />
      <ConfirmationDialog
        open={deletingNote !== null}
        title="Delete note"
        message={`Delete note "${deletingNote?.title ?? ''}"? This cannot be undone.`}
        onConfirm={() => {
          if (deletingNote) {
            void deleteMutation.mutateAsync({ noteId: deletingNote.id });
          }
        }}
        onCancel={() => setDeletingNote(null)}
      />
    </Box>
  );
};
```

(Same `ConfirmationDialog` prop-name caveat as Task 8. The delete UI duplicated between NotesPage and NotesSection is acceptable for v1; if it bothers you, extract a `useDeleteNoteWithConfirmation` hook — but don't block on it.)

- [ ] **Step 2: Add the Notes tab to `ChapterDetailDialog.tsx`**

In `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/ChapterDetailDialog.tsx`:
- Add `const TAB_NOTES = 3;` after `const TAB_FLASHCARDS = 2;`
- Add `<Tab label="Notes" />` after the Flashcards `<Tab>`.
- Add after the flashcards tab-panel block:

```tsx
{activeTab === TAB_NOTES && <NotesSection chapterId={chapter.id} bookId={bookId} />}
```

- Import: `import { NotesSection } from './NotesSection';`

(`chapter` and `bookId` are already in scope — match the exact prop names used by the `FlashcardsSection` invocation.)

- [ ] **Step 3: Verify**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: no errors. Manually: open a chapter dialog → Notes tab → add a note pre-linked to the chapter.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/BookPage/Structure/ChapterDetailDialog
git commit -m "feat: add notes section to chapter detail dialog"
```

---

### Task 10: "Add to note" from HighlightViewModal

**Files:**
- Create: `frontend/src/pages/BookPage/Highlights/HighlightViewModal/components/NotePickerDialog.tsx`
- Modify: `frontend/src/pages/BookPage/Highlights/HighlightViewModal/components/Toolbar.tsx`
- Modify: `frontend/src/pages/BookPage/Highlights/HighlightViewModal/HighlightViewModal.tsx`

**Interfaces:**
- Consumes: `NoteEditorDialog` (Task 8), generated notes hooks.
- Produces: `NotePickerDialog` props `{ open: boolean; onClose: () => void; bookId: number; onSelect: (note: NoteWithLinks) => void }`.

- [ ] **Step 1: Create `NotePickerDialog.tsx`**

```tsx
import { useGetNotesForBookApiV1BooksBookIdNotesGet } from '@/api/generated/notes/notes.ts';
import type { NoteWithLinks } from '@/api/generated/model';
import { CommonDialog } from '@/components/dialogs/CommonDialog.tsx';
import { Spinner } from '@/components/animations/Spinner.tsx';
import { List, ListItemButton, ListItemText, Typography } from '@mui/material';

interface NotePickerDialogProps {
  open: boolean;
  onClose: () => void;
  bookId: number;
  onSelect: (note: NoteWithLinks) => void;
}

export const NotePickerDialog = ({ open, onClose, bookId, onSelect }: NotePickerDialogProps) => {
  const { data, isLoading } = useGetNotesForBookApiV1BooksBookIdNotesGet(bookId, undefined, {
    query: { enabled: open },
  });
  const notes = data?.data?.notes ?? [];

  return (
    <CommonDialog open={open} onClose={onClose} title="Add highlight to note" maxWidth="sm">
      {isLoading && <Spinner />}
      {!isLoading && notes.length === 0 && (
        <Typography color="text.secondary">No notes in this book yet.</Typography>
      )}
      <List>
        {notes.map((note) => (
          <ListItemButton key={note.id} onClick={() => onSelect(note)}>
            <ListItemText primary={note.title} secondary={note.kind ?? undefined} />
          </ListItemButton>
        ))}
      </List>
    </CommonDialog>
  );
};
```

(Verify the generated hook's options signature — third argument for query options vs. second; check an existing GET hook usage with `enabled`.)

- [ ] **Step 2: Add the toolbar button**

In `frontend/src/pages/BookPage/Highlights/HighlightViewModal/components/Toolbar.tsx`, add a prop `onAddToNote: (anchorEl: HTMLElement) => void` (following the file's existing prop pattern) and a button next to the existing note toggle:

```tsx
<IconButtonWithTooltip
  title="Add to note"
  onClick={(event) => onAddToNote(event.currentTarget)}
  disabled={isDisabled}
  ariaLabel="Add to note"
  icon={<NoteAddIcon />}
/>
```

Import `NoteAddIcon` from `@/theme/Icons.tsx`. If `IconButtonWithTooltip`'s `onClick` doesn't pass the event, use a wrapping `Box` ref or plain MUI `IconButton` + `Tooltip` for this one button — check the component first.

- [ ] **Step 3: Wire the menu and dialogs in `HighlightViewModal.tsx`**

Add state and handlers (adapt names to the file's existing style; `highlight` and `bookId` are in scope there):

```tsx
const [noteMenuAnchor, setNoteMenuAnchor] = useState<HTMLElement | null>(null);
const [noteEditorOpen, setNoteEditorOpen] = useState(false);
const [notePickerOpen, setNotePickerOpen] = useState(false);
```

Pass `onAddToNote={(anchor) => setNoteMenuAnchor(anchor)}` to `Toolbar`. Render:

```tsx
<Menu
  anchorEl={noteMenuAnchor}
  open={noteMenuAnchor !== null}
  onClose={() => setNoteMenuAnchor(null)}
>
  <MenuItem
    onClick={() => {
      setNoteMenuAnchor(null);
      setNoteEditorOpen(true);
    }}
  >
    Create new note
  </MenuItem>
  <MenuItem
    onClick={() => {
      setNoteMenuAnchor(null);
      setNotePickerOpen(true);
    }}
  >
    Add to existing note
  </MenuItem>
</Menu>

<NoteEditorDialog
  open={noteEditorOpen}
  onClose={() => setNoteEditorOpen(false)}
  initialHighlightIds={[highlight.id]}
  initialChapterIds={highlight.chapter_id ? [highlight.chapter_id] : []}
/>

<NotePickerDialog
  open={notePickerOpen}
  onClose={() => setNotePickerOpen(false)}
  bookId={bookId}
  onSelect={(note) => void handleAddToExistingNote(note)}
/>
```

With the update mutation + handler:

```tsx
const queryClient = useQueryClient();
const { showSnackbar } = useSnackbar();
const updateNoteMutation = useUpdateNoteApiV1NotesNoteIdPut({
  mutation: {
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: getGetNotesForBookApiV1BooksBookIdNotesGetQueryKey(bookId),
      });
      setNotePickerOpen(false);
      showSnackbar('Highlight added to note.', 'success');
    },
    onError: (error) => {
      console.error('Failed to add highlight to note:', error);
      showSnackbar('Failed to add highlight to note. Please try again.', 'error');
    },
  },
});

const handleAddToExistingNote = async (note: NoteWithLinks) => {
  await updateNoteMutation.mutateAsync({
    noteId: note.id,
    data: {
      title: note.title,
      body: note.body,
      kind: note.kind as NoteUpdateRequest['kind'],
      chapter_ids: note.chapter_ids,
      highlight_ids: [...new Set([...note.highlight_ids, highlight.id])],
      highlight_tag_ids: note.highlight_tag_ids,
    },
  });
};
```

Caveat: `NoteEditorDialog` uses `useBookPage()`; `HighlightViewModal` renders inside the book page tree, so the context is available. Verify `highlight.chapter_id` is the field name on the highlight object this modal receives (check its props/types in the file).

- [ ] **Step 4: Verify**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: no errors. Manually: open a highlight → Add to note → both menu paths work.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/BookPage/Highlights frontend/src/theme/Icons.tsx
git commit -m "feat: add highlight-to-note linking from highlight modal"
```

---

### Task 11: "Save as note" from AI chat

**Files:**
- Modify: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/chat/ChatMessageList.tsx`
- Modify: `frontend/src/pages/BookPage/Structure/ChapterDetailDialog/ChatDialog.tsx`
- Modify: the component that renders `ChatDialog` (find with `grep -rn "ChatDialog" frontend/src/pages --include="*.tsx" -l`; expected: `ChapterDetailDialog.tsx` or `ChapterToolbar.tsx`)

**Interfaces:**
- Consumes: `NoteEditorDialog` (Task 8).
- Produces: `ChatMessageList` gains optional `onSaveNote?: (content: string) => void`; `ChatDialog` gains the same optional prop and threads it through.

- [ ] **Step 1: Add the save action to `ChatMessageList.tsx`**

Extend the props interface:

```tsx
interface ChatMessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSaveNote?: (content: string) => void;
}
```

In the assistant-message branch, render an action row below the markdown:

```tsx
{msg.role === 'assistant' ? (
  <>
    <Box sx={markdownStyles(theme)}>
      <ReactMarkdown>{msg.content}</ReactMarkdown>
    </Box>
    {onSaveNote && (
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 0.5 }}>
        <IconButtonWithTooltip
          title="Save as note"
          ariaLabel="Save as note"
          onClick={() => onSaveNote(msg.content)}
          icon={<NoteAddIcon fontSize="small" />}
        />
      </Box>
    )}
  </>
) : (
  <Typography variant="body1">{msg.content}</Typography>
)}
```

Add imports: `IconButtonWithTooltip` from `@/components/buttons/IconButtonWithTooltip.tsx`, `NoteAddIcon` from `@/theme/Icons.tsx`.

- [ ] **Step 2: Thread the prop through `ChatDialog.tsx`**

Add `onSaveNote?: (content: string) => void` to `ChatDialog`'s props interface (and to the inner `ChatContent` component if the file splits them), and pass it to `<ChatMessageList ... onSaveNote={onSaveNote} />`. The quiz variant simply won't pass it.

- [ ] **Step 3: Handle the save in the parent**

In the component that renders `ChatDialog` (inside `ChapterDetailDialog` scope, where `chapter` and `bookId` exist), add:

```tsx
const [chatNoteBody, setChatNoteBody] = useState<string | null>(null);
```

Pass to the chat variant only:

```tsx
<ChatDialog
  {...existingProps}
  onSaveNote={(content) => setChatNoteBody(content)}
/>
```

And render alongside:

```tsx
<NoteEditorDialog
  open={chatNoteBody !== null}
  onClose={() => setChatNoteBody(null)}
  initialBody={chatNoteBody ?? ''}
  initialChapterIds={[chapter.id]}
/>
```

Import `NoteEditorDialog` from `@/pages/BookPage/Notes/NoteEditorDialog`.

- [ ] **Step 4: Verify**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: no errors. Manually (AI enabled): open chapter chat, send a message, click "Save as note" on the reply → editor opens pre-filled with the message body and the chapter linked; save and confirm it appears in the Notes tab.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/BookPage/Structure/ChapterDetailDialog
git commit -m "feat: add save-as-note action to AI chat messages"
```

---

### Task 12: Final verification

- [ ] **Step 1: Backend full suite + static checks**

Run: `cd backend && uv run pytest && uv run pyright src/ && uv run ruff check src/ tests/`
Expected: all tests pass, zero errors

- [ ] **Step 2: Frontend static checks**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: zero errors

- [ ] **Step 3: Stale-import sweep**

Run: `rg "domain\.notes|application\.notes|infrastructure\.notes" backend/src backend/tests -l`
Confirm all hits are intentional; confirm no references to names that were renamed during implementation.

- [ ] **Step 4: End-to-end smoke test**

Start backend + frontend dev servers, then walk the four entry points: Notes tab CRUD + kind filter → chapter dialog Notes tab → highlight "Add to note" (both menu paths) → chat "Save as note". Confirm a note created from chat appears in the Notes tab with its chapter chip.

- [ ] **Step 5: Finish the branch**

Use the superpowers:finishing-a-development-branch skill to decide merge/PR/cleanup.
