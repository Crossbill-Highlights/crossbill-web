# Book Notes — Design

**Date:** 2026-07-08
**Status:** Approved

## Overview

Crossbill gains in-app notes: user-authored notes about terms, characters, and concepts encountered while reading. Notes are created and viewed in a single book's context in v1, and can be associated with chapters, highlights, and highlight tags. Notes can also be created from AI chat sessions via a "save as note" action. The data model is designed so that a future cross-book feature (one concept linked to multiple books) requires no schema migration.

## Key Decisions

- A note is **title + markdown body + optional kind** (`character` / `term` / `concept` / `other`). The kind enables filtering and icons but is never required.
- Notes link **many-to-many** to chapters and highlights — a character note accumulates links to every chapter/highlight where the character appears.
- Notes use the existing book-scoped **HighlightTag** system for tagging, so a tag like "stoicism" groups both highlights and notes within a book. No new tag entity.
- Chat integration v1 is a **"save as note" button** on assistant chat messages. No AI tool use yet.
- Notes are **user-scoped with book links** (not `book_id`-scoped like `Flashcard`): the `Note` belongs to the user and attaches to books via a `note_books` link table. The v1 UI always creates a note with exactly one linked book, but the schema already supports cross-book association.

## 1. Domain Model & Schema

### New subdomain: `domain/notes`

Notes span library, reading, and learning concerns, so they get their own bounded context rather than living inside any existing subdomain.

### `Note` entity (aggregate root)

- `id: int`
- `user_id: int`
- `title: str` — required, non-empty
- `body: str` — markdown; may be empty (sometimes the title *is* the note, to be fleshed out later)
- `kind: NoteKind | None` — enum: `CHARACTER`, `TERM`, `CONCEPT`, `OTHER`; optional
- `created_at`, `updated_at`
- Link-id collections held on the aggregate (same pattern as `Highlight._tag_ids`):
  - `book_ids`
  - `chapter_ids`
  - `highlight_ids`
  - `highlight_tag_ids`

### Invariants (enforced in the entity)

1. A note must be linked to **at least one book**.
2. A chapter, highlight, or highlight-tag link is only valid if its parent book is among the note's linked books. (In v1 there is always exactly one linked book.)

### Exceptions

`domain/notes/exceptions.py`:

- `NoteNotFoundError` — specific `EntityNotFoundError` subclass.
- A validation error subclass for cross-book link violations.

### ORM (in `backend/src/models.py`)

- `notes` table: `id`, `user_id` FK, `title`, `body`, `kind` (nullable str), `created_at`, `updated_at`.
- Four association tables with real FKs and `ON DELETE CASCADE`, matching the existing `book_tags` / `highlight_highlight_tags` pattern:
  - `note_books` (`note_id`, `book_id`)
  - `note_chapters` (`note_id`, `chapter_id`)
  - `note_highlights` (`note_id`, `highlight_id`)
  - `note_highlight_tags` (`note_id`, `highlight_tag_id`)
- One Alembic migration creating all five tables.

### Repository

- `NoteRepositoryProtocol` defined for the application layer; implementation in `infrastructure/notes/repositories/` with a `note_mapper.py`, following the highlight repository pattern.
- Queries: get by id, list by book (join through `note_books`), list by chapter, list by highlight, create, update (including replacing link sets), delete.
- Use `.unique()` on any query with `joinedload()` over collections.

### Deletion semantics

- **Notes are hard-deleted.** Nothing references notes, so soft delete adds complexity without a driver.
- **Highlight soft-deletion keeps note links intact.** When a highlight is soft-deleted (`deleted_at` set), the `note_highlights` row remains; display queries filter out soft-deleted highlights. Undeleting a highlight restores the association for free.

## 2. Application Layer & API

### Use cases (`application/notes/use_cases/`)

- Create note
- Update note (fields + replace link sets)
- Delete note
- Get note
- List notes by book (optional filters: kind, chapter, highlight, tag)

Chapter- and highlight-scoped listings (ChapterDetailDialog, HighlightViewModal) are served by the list-by-book use case with `chapter_id` / `highlight_id` filters rather than separate use cases.

All use cases work with domain entities and repository protocols. Wired through a new DI container `containers/notes.py`.

### Endpoints (new router `infrastructure/notes/routers/notes.py`)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/notes` | Create; body includes title, body, kind, and book/chapter/highlight/tag ids |
| `GET` | `/api/v1/books/{book_id}/notes` | List for a book; filterable by kind, chapter, highlight, tag |
| `GET` | `/api/v1/notes/{note_id}` | Get one note with linked entities |
| `PUT` | `/api/v1/notes/{note_id}` | Update fields + replace links |
| `DELETE` | `/api/v1/notes/{note_id}` | Delete |

### Schemas

- Pydantic schemas convert the `NoteKind` enum to a plain string (value objects/enums never passed raw to Pydantic).
- List responses include lightweight link summaries (chapter names, highlight text snippets, tag names) so the UI does not need N+1 fetches.
- All endpoints are scoped to the authenticated user; accessing another user's note returns 404 via `NoteNotFoundError`.

## 3. Frontend

- **Notes tab** on the book page: new route `book.$bookId/notes.tsx`, page under `pages/BookPage/Notes/`. Note list with kind filter plus tag/chapter filters; create/edit in a dialog with title, kind picker, markdown body, and chapter/highlight/tag pickers scoped to the book.
- **NotesSection** in `ChapterDetailDialog`, mirroring `FlashcardsSection`: shows notes linked to the chapter, with quick-create pre-linked to that chapter.
- **Create-from-highlight**: an "Add to note" action in `HighlightViewModal` opening a small picker — create a new note (pre-filled, highlight linked) or link the highlight to an existing note.
- **Save-from-chat**: a "Save as note" action on assistant messages in `ChatDialog`; opens the note editor pre-filled with the message text as body and the session's chapter linked. The user edits title/kind and saves.
- API hooks via the existing generated client (orval) + TanStack Query, invalidating book-notes queries on mutation.

## 4. Testing & Error Handling

- **Repository tests**: link-table round-trips (create with links, update replacing link sets, list-by-book/chapter/highlight, cascade behavior).
- **Use case tests**: invariants — no linked books → validation error; chapter/highlight/tag link whose book is not linked → validation error.
- **Router tests**: auth scoping (a user cannot read/edit/delete another user's notes), 404 handling via `NoteNotFoundError`.
- **Frontend**: type-check and lint per project hooks.

## Out of Scope for v1

- AI tool-use note creation (chat agent `create_note` tool) — planned follow-up.
- Cross-book UI (linking one note to multiple books) — schema supports it; UI later.
- Note-to-note links.
- Full-text search over notes.
