# Chapter-Level Flashcards Design

## Problem

Flashcards can currently be created from the HighlightViewModal and are always linked to a highlight, or created as book-level flashcards with no chapter association. There is no way to create flashcards tied to a chapter (without a highlight), and no AI suggestion feature for generating flashcards from chapter content.

## Solution

Add optional `chapter_id` to the flashcard model. Enable flashcard creation (manual + AI suggestions) in the ChapterDetailDialog. AI suggestions use the chapter's prereading summary + keypoints as input.

## Database

Add nullable `chapter_id` FK column to `flashcards` table:

```sql
ALTER TABLE flashcards ADD COLUMN chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE;
```

A flashcard can be:
- **Highlight-linked**: `highlight_id` set, `chapter_id` null (existing behavior, chapter derived from highlight)
- **Chapter-linked**: `chapter_id` set, `highlight_id` null (new)
- **Book-level**: both null (existing behavior)

## Backend Changes

### Domain Entity

Add `chapter_id: ChapterId | None = None` to `Flashcard` dataclass. Update `Flashcard.create()` factory to accept optional `chapter_id`.

### ORM Model

Add `chapter_id` mapped column (nullable FK to `chapters.id`, CASCADE delete). Add relationship to `Chapter`.

### Mapper

Update `FlashcardMapper.to_domain()` and `to_orm()` to handle `chapter_id`.

### Schemas

Add `chapter_id: int | None` to:
- `FlashcardCreateRequest` (optional input)
- `Flashcard` response schema
- `FlashcardWithHighlight` response schema

### Use Case: CreateFlashcardForBookUseCase

Update to accept optional `chapter_id`. Validate the chapter exists and belongs to the book (via `ChapterRepository`). Pass `chapter_id` through to `Flashcard.create()`.

### Use Case: GetFlashcardsByBookUseCase

Update to include `chapter_id` in the `FlashcardWithHighlight` DTO. For chapter-linked flashcards (no highlight), the chapter info comes directly from the flashcard's `chapter_id` rather than from the highlight's chapter.

### Router: book_flashcards.py

Update `POST /api/v1/books/{book_id}/flashcards` to pass `chapter_id` from request body to use case. Update response mapping to include `chapter_id`.

### New Use Case: GetChapterFlashcardSuggestionsUseCase

- Dependencies: `ChapterPrereadingRepository`, `AIFlashcardServiceProtocol`
- Loads the chapter's prereading data
- Combines `summary` + `keypoints` (joined with newlines) into a single text block
- Passes to `ai_flashcard_service.generate_flashcard_suggestions(content)`
- Returns `list[FlashcardSuggestion]`

### New Router Endpoint

`GET /api/v1/chapters/{chapter_id}/flashcard_suggestions`
- Decorated with `@require_ai_enabled`
- Returns `HighlightFlashcardSuggestionsResponse` (reuse existing schema)

### BookDetails Response

Add `chapter_id` to flashcard objects within the book details response so the frontend can group chapter-linked flashcards correctly. Chapter-linked flashcards should appear in their chapter's data (alongside highlight-sourced flashcards).

## MCP Server Changes

### Tool: `create_flashcard`

Add optional `chapter_id: int | None = None` parameter.

### Client: `CrossbillClient.create_flashcard()`

When `highlight_id` is None and calling `POST /api/v1/books/{book_id}/flashcards`, include `chapter_id` in the JSON body if provided.

## Frontend Changes

### API Types (regenerated via orval)

`Flashcard` type gains `chapter_id: number | null`. `FlashcardCreateRequest` gains optional `chapter_id`.

### ChapterDetailDialog/FlashcardsSection

Transform from a read-only list into a full flashcard management section (modeled after `HighlightViewModal/FlashcardSection`):

1. **Existing flashcards list** -- show both highlight-sourced and chapter-linked flashcards for this chapter
2. **Create form** -- two text fields (question, answer) with Add/Update button. Uses `POST /api/v1/books/{book_id}/flashcards` with `chapter_id` set.
3. **AI suggestions** (gated by `<AIFeature>`) -- "Suggest flashcards" button that calls `GET /api/v1/chapters/{chapter_id}/flashcard_suggestions`. Shows suggestion cards with accept/reject. Accept creates via the same book flashcard endpoint with `chapter_id`. Only available when prereading summary exists.

### FlashcardsTab

Update the grouping logic in `FlashcardsTab.tsx`:
- Currently, flashcards are grouped by chapter using the highlight's chapter. Book-level flashcards (from `book.book_flashcards`) go into a separate "Book Flashcards" group.
- After this change: flashcards with `chapter_id` set (but no `highlight_id`) are grouped into the matching chapter section alongside highlight-sourced flashcards.
- The `FlashcardWithContext` already has `chapterId` — for chapter-linked flashcards, this comes from `flashcard.chapter_id` instead of from the highlight's chapter.

### No Visual Distinction

Chapter-level flashcards look identical to highlight-based ones. The only difference is they won't show a source highlight snippet (which is already handled since `highlight` will be null).
