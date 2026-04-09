# Public Book Covers - Remove Auth from Cover Image Serving

## Context

Book cover files are now stored with UUID-based filenames (e.g. `a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`). These UUIDs are unguessable, making enumeration attacks infeasible. The current implementation requires JWT authentication and ownership verification to serve cover images, which forces the frontend to use XHR requests with bearer tokens and blob URLs instead of native `<img src>` tags. This prevents browser caching of cover images.

## Goal

Remove authentication from cover image serving so covers can be loaded via plain `<img src>` URLs, enabling browser caching and simplifying the frontend.

## Design

### 1. New Public Cover Endpoint

**New file:** `backend/src/infrastructure/library/routers/covers.py`

- `GET /api/v1/covers/{filename}` — no auth required
- Validates `filename` matches expected UUID format (e.g. `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg`)
- Uses `FileRepository.get_cover(filename)` to read the file from disk/S3
- Returns `Response(content=bytes, media_type="image/jpeg")` or 404
- No use case layer needed — this is pure file serving with no business logic
- Register the router on the FastAPI app

### 2. Schema and API Response Changes

**Replace `has_cover: bool` with `cover_file: str | None` in:**
- `BookWithHighlightCount` schema
- `BookDetails` schema
- Ereader schemas (`EreaderBookMetadata` and similar)

**Router mapping changes in `books.py`:**
- All response construction sites change from `has_cover=...` to `cover_file=book.cover_file` (or equivalent from domain entity)

### 3. Remove Old Cover Endpoint and Dead Code

**Delete:**
- `GET /api/v1/books/{book_id}/cover` endpoint from `books.py`
- `BookCoverUseCase` class and its module
- DI wiring for `BookCoverUseCase` in the container

**Remove `has_cover` computation everywhere:**
- Remove from use case return types (tuples that include `has_cover`)
- Remove from repository query logic that computes it (likely `cover_file IS NOT NULL` checks)
- Remove from any aggregation or DTO classes that carry it
- Trace all usages to ensure no dead code remains

### 4. Frontend: Rewrite `BookCover.tsx`

**Props change:**
- Remove `bookId: number` and `hasCover: boolean`
- Add `coverFile: string | null`

**Rendering:**
- If `coverFile` is null → show placeholder immediately (no loading state)
- If `coverFile` exists → render `<img src="${apiUrl}/api/v1/covers/${coverFile}">`
- Remove loading spinner logic (browser handles image loading natively)
- Keep `onError` fallback to placeholder icon

### 5. Update BookCover Consumers

Update all components that use `BookCover`:
- `BookCard.tsx` → `coverFile={book.cover_file}`
- `BookTitle.tsx` → `coverFile={book.cover_file}`
- `BookEditModal.tsx` → `coverFile={book.cover_file}`

### 6. Delete `useAuthenticatedImage` Hook

Remove `frontend/src/hooks/useAuthenticatedImage.ts` entirely. No other consumers exist after the `BookCover` rewrite.

### 7. Regenerate Frontend API Types

Ask user to regenerate API types so `has_cover: boolean` becomes `cover_file: string | null` in the generated TypeScript types.

## Security Considerations

- Cover filenames are UUIDs generated server-side — not guessable or enumerable
- The public endpoint validates filename format to prevent path traversal
- Book files (EPUB, PDF) remain behind authentication — only covers become public
- No user data is exposed through cover images
