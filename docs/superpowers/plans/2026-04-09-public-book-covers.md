# Public Book Covers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove authentication from book cover serving so covers load via plain `<img src>` URLs, enabling browser caching.

**Architecture:** New public `GET /api/v1/covers/{filename}` endpoint serves covers without auth. All API schemas replace `has_cover: bool` with `cover_file: str | None`. Frontend `BookCover` component switches from XHR blob fetching to native `<img src>`. Dead code (`BookCoverUseCase`, `useAuthenticatedImage`, unused `file_repository` dependencies) is removed.

**Tech Stack:** FastAPI, Pydantic, React, MUI

---

### Task 1: Create public cover endpoint

**Files:**
- Create: `backend/src/infrastructure/library/routers/covers.py`
- Modify: `backend/src/main.py:46-47,317-318` (add import and router registration)

- [ ] **Step 1: Create the covers router**

Create `backend/src/infrastructure/library/routers/covers.py`:

```python
"""Public endpoint for serving book cover images."""

import re

from fastapi import APIRouter, HTTPException
from starlette import status
from starlette.responses import Response

from src.infrastructure.library.repositories.file_repository import FileRepository

router = APIRouter(prefix="/covers", tags=["covers"])

# UUID filename pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg
_UUID_FILENAME_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$"
)


@router.get("/{filename}", status_code=status.HTTP_200_OK, response_class=Response)
async def get_cover(filename: str) -> Response:
    """
    Get a book cover image by filename.

    This is a public endpoint - no authentication required.
    Cover filenames are UUIDs, making enumeration infeasible.
    """
    if not _UUID_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Cover not found")

    file_repository = FileRepository()
    cover_bytes = await file_repository.get_cover(filename)

    if cover_bytes is None:
        raise HTTPException(status_code=404, detail="Cover not found")

    return Response(
        content=cover_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
```

- [ ] **Step 2: Register the router in main.py**

In `backend/src/main.py`, add the import alongside existing library router imports (around line 46-47):

```python
from src.infrastructure.library.routers import covers as library_covers
```

Add router registration after line 318 (after the ereader router):

```python
app.include_router(library_covers.router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 3: Verify the endpoint works**

Run: `cd backend && uv run python -c "from src.infrastructure.library.routers.covers import router; print('OK')"` 
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/library/routers/covers.py backend/src/main.py
git commit -m "feat: add public cover image endpoint without auth"
```

---

### Task 2: Replace `has_cover` with `cover_file` in schemas

**Files:**
- Modify: `backend/src/infrastructure/library/schemas/book_schemas.py:66,119`
- Modify: `backend/src/infrastructure/reading/schemas/highlight_schemas.py:178`

- [ ] **Step 1: Update `BookWithHighlightCount` schema**

In `backend/src/infrastructure/library/schemas/book_schemas.py`, line 66, change:

```python
has_cover: bool = Field(..., description="Whether the book has a cover image")
```

to:

```python
cover_file: str | None = Field(None, description="Cover image filename (UUID.jpg) or null")
```

- [ ] **Step 2: Update `EreaderBookMetadata` schema**

In the same file, line 119, change:

```python
has_cover: bool = Field(..., description="Whether the book has a cover image")
```

to:

```python
cover_file: str | None = Field(None, description="Cover image filename (UUID.jpg) or null")
```

- [ ] **Step 3: Update `BookDetails` schema**

In `backend/src/infrastructure/reading/schemas/highlight_schemas.py`, line 178, change:

```python
has_cover: bool = Field(..., description="Whether the book has a cover image")
```

to:

```python
cover_file: str | None = Field(None, description="Cover image filename (UUID.jpg) or null")
```

- [ ] **Step 4: Run type check to see what breaks**

Run: `cd backend && uv run pyright src/infrastructure/library/schemas/book_schemas.py src/infrastructure/reading/schemas/highlight_schemas.py`
Expected: PASS (schemas are self-contained at this point)

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/library/schemas/book_schemas.py backend/src/infrastructure/reading/schemas/highlight_schemas.py
git commit -m "refactor: replace has_cover with cover_file in API schemas"
```

---

### Task 3: Update routers to pass `cover_file` instead of `has_cover`

**Files:**
- Modify: `backend/src/infrastructure/library/routers/books.py:165,261,278,319,336,392,401`
- Modify: `backend/src/infrastructure/library/routers/ereader.py:61-67,99-105`

- [ ] **Step 1: Update `_build_book_details_schema` in books.py**

In `backend/src/infrastructure/library/routers/books.py`, line 165, change:

```python
has_cover=agg.has_cover,
```

to:

```python
cover_file=agg.book.cover_file,
```

- [ ] **Step 2: Update `get_books` response construction**

In the same file, lines 254-279. In the list comprehension building `BookWithHighlightCount`, change line 261:

```python
has_cover=has_cover,
```

to:

```python
cover_file=book.cover_file,
```

And update the tuple unpacking on line 278 — remove `has_cover`:

```python
for book, highlight_count, flashcard_count, tags in results
```

(was: `for book, highlight_count, flashcard_count, tags, has_cover in results`)

- [ ] **Step 3: Update `get_recently_viewed_books` response construction**

Same file, lines 312-337. Change line 319:

```python
has_cover=has_cover,
```

to:

```python
cover_file=book.cover_file,
```

And update tuple unpacking on line 336:

```python
for book, highlight_count, flashcard_count, tags in results
```

(was: `for book, highlight_count, flashcard_count, tags, has_cover in results`)

- [ ] **Step 4: Update `update_book` response construction**

Same file, lines 392-417. Change the tuple unpacking on line 392:

```python
book, highlight_count, flashcard_count, tags = await use_case.update_book(
```

(was: `book, highlight_count, flashcard_count, tags, has_cover = await use_case.update_book(`)

And change line 401:

```python
has_cover=has_cover,
```

to:

```python
cover_file=book.cover_file,
```

- [ ] **Step 5: Update ereader router**

In `backend/src/infrastructure/library/routers/ereader.py`, update the two `EreaderBookMetadata` constructions.

Lines 61-67 (POST endpoint), change:

```python
return EreaderBookMetadata(
    book_id=metadata.book_id,
    bookname=metadata.title,
    author=metadata.author,
    has_cover=metadata.has_cover,
    has_ebook=metadata.has_ebook,
)
```

to:

```python
return EreaderBookMetadata(
    book_id=metadata.book_id,
    bookname=metadata.title,
    author=metadata.author,
    cover_file=metadata.cover_file,
    has_ebook=metadata.has_ebook,
)
```

Lines 99-105 (GET endpoint), same change:

```python
return EreaderBookMetadata(
    book_id=metadata.book_id,
    bookname=metadata.title,
    author=metadata.author,
    cover_file=metadata.cover_file,
    has_ebook=metadata.has_ebook,
)
```

- [ ] **Step 6: Run type check**

Run: `cd backend && uv run pyright src/infrastructure/library/routers/books.py src/infrastructure/library/routers/ereader.py`
Expected: Errors about use case return types (has_cover still in tuples) — these are fixed in Task 4.

- [ ] **Step 7: Commit**

```bash
git add backend/src/infrastructure/library/routers/books.py backend/src/infrastructure/library/routers/ereader.py
git commit -m "refactor: update routers to pass cover_file instead of has_cover"
```

---

### Task 4: Remove `has_cover` from use cases and domain aggregation

**Files:**
- Modify: `backend/src/application/library/use_cases/book_queries/get_books_with_counts_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_queries/get_recently_viewed_books_use_case.py`
- Modify: `backend/src/application/library/use_cases/book_queries/get_ereader_metadata_use_case.py:12-19,53-62`
- Modify: `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py:176,186`
- Modify: `backend/src/application/library/use_cases/book_management/update_book_use_case.py:40,75,80`
- Modify: `backend/src/domain/library/services/book_details_aggregator.py:27`

- [ ] **Step 1: Simplify `GetBooksWithCountsUseCase`**

Replace the entire file `backend/src/application/library/use_cases/book_queries/get_books_with_counts_use_case.py` with:

```python
"""Use case for retrieving books with counts."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetBooksWithCountsUseCase:
    """Use case for retrieving books with highlight and flashcard counts."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.book_repository = book_repository

    async def get_books_with_counts(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> tuple[list[tuple[Book, int, int, list[Tag]]], int]:
        """
        Get books with their highlight and flashcard counts.

        Returns:
            tuple[list[tuple[Book, highlight_count, flashcard_count, list[Tag]]], total_count]
        """
        user_id_vo = UserId(user_id)
        return await self.book_repository.get_books_with_counts(
            user_id=user_id_vo,
            offset=offset,
            limit=limit,
            include_only_with_flashcards=include_only_with_flashcards,
            search_text=search_text,
        )
```

Key changes: removed `file_repository` dependency, removed `has_cover` computation, return type is now `tuple[Book, int, int, list[Tag]]` (no bool).

- [ ] **Step 2: Simplify `GetRecentlyViewedBooksUseCase`**

Replace `backend/src/application/library/use_cases/book_queries/get_recently_viewed_books_use_case.py` with:

```python
"""
Get recently viewed books use case.

Retrieves books ordered by last viewed timestamp with highlight and flashcard counts.
"""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetRecentlyViewedBooksUseCase:
    """Use case for retrieving recently viewed books."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.book_repository = book_repository

    async def get_recently_viewed(
        self, user_id: int, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag]]]:
        """
        Get recently viewed books with their counts and tags.

        Returns:
            List of tuples containing (Book, highlight_count, flashcard_count, list[Tag])
            ordered by last_viewed DESC.
        """
        user_id_vo = UserId(user_id)
        return await self.book_repository.get_recently_viewed_books(
            user_id=user_id_vo,
            limit=limit,
        )
```

Key changes: removed `file_repository` dependency, removed `has_cover` computation, simplified return type.

- [ ] **Step 3: Update `EreaderMetadata` dataclass and use case**

In `backend/src/application/library/use_cases/book_queries/get_ereader_metadata_use_case.py`, change the `EreaderMetadata` dataclass (lines 12-19):

```python
@dataclass
class EreaderMetadata:
    """Lightweight book metadata for ereader operations."""

    book_id: int
    title: str
    author: str | None
    cover_file: str | None
    has_ebook: bool
```

And update `get_metadata_for_ereader` method — change lines 53-62:

```python
        cover_file = book.cover_file
        has_ebook = book.ebook_file is not None

        return EreaderMetadata(
            book_id=book.id.value,
            title=book.title,
            author=book.author,
            cover_file=cover_file,
            has_ebook=has_ebook,
        )
```

Also remove the `file_repository` dependency from `__init__` — the use case doesn't use it. Change `__init__`:

```python
    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
```

And remove the `FileRepositoryProtocol` import.

- [ ] **Step 4: Update `GetBookDetailsUseCase`**

In `backend/src/application/library/use_cases/book_management/get_book_details_use_case.py`:

Remove line 176 (`has_cover = book.cover_file is not None`).

Change line 186 from `has_cover=has_cover,` — remove it entirely (the field is being removed from `BookDetailsAggregation`).

Also remove the `file_repository` parameter from `__init__` (lines 52, 66), and remove the `FileRepositoryProtocol` import (line 8). Remove `file_repository` from the constructor assignment.

- [ ] **Step 5: Update `UpdateBookUseCase`**

In `backend/src/application/library/use_cases/book_management/update_book_use_case.py`:

Change the return type on line 40:

```python
    ) -> tuple[Book, int, int, list[Tag]]:
```

Remove line 75 (`has_cover = book.cover_file is not None`).

Change line 80 to remove the trailing `has_cover`:

```python
        return book, highlight_count, flashcard_count, tags
```

Also remove `file_repository` from `__init__` parameters (line 29) and constructor assignment (line 35), and remove the `FileRepositoryProtocol` import (line 7).

- [ ] **Step 6: Remove `has_cover` from `BookDetailsAggregation`**

In `backend/src/domain/library/services/book_details_aggregator.py`, remove line 27:

```python
    has_cover: bool = False
```

- [ ] **Step 7: Run type check**

Run: `cd backend && uv run pyright src/application/library/use_cases/ src/domain/library/services/book_details_aggregator.py src/infrastructure/library/routers/books.py src/infrastructure/library/routers/ereader.py`
Expected: PASS (or errors only in DI container — fixed in Task 5)

- [ ] **Step 8: Commit**

```bash
git add backend/src/application/library/use_cases/ backend/src/domain/library/services/book_details_aggregator.py
git commit -m "refactor: remove has_cover from use cases and domain aggregation"
```

---

### Task 5: Remove `BookCoverUseCase` and clean up DI container

**Files:**
- Delete: `backend/src/application/library/use_cases/book_files/book_cover_use_case.py`
- Modify: `backend/src/containers/library.py:3,80-84,137-151`
- Modify: `backend/src/infrastructure/library/routers/books.py:8,442-469` (remove old endpoint)

- [ ] **Step 1: Delete `BookCoverUseCase`**

Delete the file: `backend/src/application/library/use_cases/book_files/book_cover_use_case.py`

- [ ] **Step 2: Remove old cover endpoint from books router**

In `backend/src/infrastructure/library/routers/books.py`:

Remove the `BookCoverUseCase` import (line 8):

```python
from src.application.library.use_cases.book_files.book_cover_use_case import BookCoverUseCase
```

Remove the entire `get_book_cover` endpoint (lines 442-469).

- [ ] **Step 3: Clean up DI container**

In `backend/src/containers/library.py`:

Remove the `BookCoverUseCase` import (line 3):

```python
from src.application.library.use_cases.book_files.book_cover_use_case import BookCoverUseCase
```

Remove the `book_cover_use_case` factory (lines 80-84):

```python
    book_cover_use_case = providers.Factory(
        BookCoverUseCase,
        book_repository=book_repository,
        file_repository=file_repository,
    )
```

Remove `file_repository` from the three query use case factories. Change lines 137-151:

```python
    get_books_with_counts_use_case = providers.Factory(
        GetBooksWithCountsUseCase,
        book_repository=book_repository,
    )
    get_recently_viewed_books_use_case = providers.Factory(
        GetRecentlyViewedBooksUseCase,
        book_repository=book_repository,
    )
    get_ereader_metadata_use_case = providers.Factory(
        GetEreaderMetadataUseCase,
        book_repository=book_repository,
    )
```

Also remove `file_repository` from `get_book_details_use_case` factory (line 114) and `update_book_use_case` factory (line 127). These lines reference `file_repository=file_repository` and should be deleted.

- [ ] **Step 4: Run type check and tests**

Run: `cd backend && uv run pyright src/containers/library.py src/infrastructure/library/routers/books.py && uv run pytest -x`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -u backend/
git commit -m "refactor: remove BookCoverUseCase and clean up DI wiring"
```

---

### Task 6: Update frontend `BookCover` component

**Files:**
- Modify: `frontend/src/components/BookCover.tsx`

- [ ] **Step 1: Rewrite `BookCover` component**

Replace the entire file `frontend/src/components/BookCover.tsx` with:

```tsx
import { BookCoverIcon } from '@/theme/Icons.tsx';
import { Box, type SxProps, type Theme, useTheme } from '@mui/material';

export interface BookCoverProps {
  coverFile: string | null;
  title: string;
  /**
   * Width of the cover container
   */
  width?: number | string | { xs?: number | string; sm?: number | string };
  /**
   * Height of the cover container
   */
  height?: number | string | { xs?: number | string; sm?: number | string };
  /**
   * Object fit for the image ('contain' | 'cover')
   * @default 'contain'
   */
  objectFit?: 'contain' | 'cover';
  /**
   * Additional sx props for the container
   */
  sx?: SxProps<Theme>;
}

export const BookCover = ({
  coverFile,
  title,
  width = '100%',
  height = 200,
  objectFit = 'contain',
  sx,
}: BookCoverProps) => {
  const theme = useTheme();
  const apiUrl =
    import.meta.env.VITE_API_URL !== undefined
      ? import.meta.env.VITE_API_URL
      : 'http://localhost:8000';

  const coverUrl = coverFile ? `${apiUrl}/api/v1/covers/${coverFile}` : null;
  const placeholderBackground = theme.palette.action.hover;
  const showPlaceholder = !coverUrl;

  return (
    <Box
      sx={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: showPlaceholder ? placeholderBackground : 'transparent',
        overflow: 'hidden',
        ...sx,
      }}
    >
      {coverUrl ? (
        <img
          src={coverUrl}
          alt={`${title} cover`}
          style={{
            width: '100%',
            height: '100%',
            objectFit,
          }}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
            const placeholder = e.currentTarget.nextSibling as HTMLElement | null;
            if (placeholder) placeholder.style.display = 'flex';
          }}
        />
      ) : null}

      <Box
        sx={{
          display: showPlaceholder ? 'flex' : 'none',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
        }}
      >
        <BookCoverIcon
          sx={{
            fontSize: typeof height === 'number' ? height * 0.4 : 80,
            color: 'text.disabled',
            opacity: 1,
          }}
        />
      </Box>
    </Box>
  );
};
```

Key changes: removed `bookId`/`hasCover` props, added `coverFile` prop, removed `useAuthenticatedImage` hook, removed loading spinner, uses plain `<img src>`.

- [ ] **Step 2: Run lint check**

Run: `cd frontend && npm run lint -- --no-warn-ignored src/components/BookCover.tsx`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/BookCover.tsx
git commit -m "refactor: BookCover uses plain img src instead of authenticated blob"
```

---

### Task 7: Update BookCover consumers

**Files:**
- Modify: `frontend/src/pages/LandingPage/components/BookCard.tsx:42-46`
- Modify: `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx:54-58`
- Modify: `frontend/src/pages/BookPage/BookTitle/BookEditModal.tsx:155-160`

- [ ] **Step 1: Update BookCard**

In `frontend/src/pages/LandingPage/components/BookCard.tsx`, change the `BookCover` usage (around lines 42-46) from:

```tsx
<BookCover
  bookId={book.id}
  hasCover={book.has_cover}
  title={book.title}
```

to:

```tsx
<BookCover
  coverFile={book.cover_file}
  title={book.title}
```

- [ ] **Step 2: Update BookTitle**

In `frontend/src/pages/BookPage/BookTitle/BookTitle.tsx`, change the `BookCover` usage (around lines 54-58) from:

```tsx
<BookCover
  bookId={book.id}
  hasCover={book.has_cover}
  title={book.title}
```

to:

```tsx
<BookCover
  coverFile={book.cover_file}
  title={book.title}
```

- [ ] **Step 3: Update BookEditModal**

In `frontend/src/pages/BookPage/BookTitle/BookEditModal.tsx`, change the `BookCover` usage (around lines 155-160) from:

```tsx
<BookCover
  bookId={book.id}
  hasCover={book.has_cover}
  title={book.title}
```

to:

```tsx
<BookCover
  coverFile={book.cover_file}
  title={book.title}
```

- [ ] **Step 4: Run type check**

Run: `cd frontend && npm run type-check`
Expected: Errors about `book.cover_file` not existing on generated types — this is expected until API types are regenerated (Task 9).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/LandingPage/components/BookCard.tsx frontend/src/pages/BookPage/BookTitle/BookTitle.tsx frontend/src/pages/BookPage/BookTitle/BookEditModal.tsx
git commit -m "refactor: update BookCover consumers to use cover_file prop"
```

---

### Task 8: Delete `useAuthenticatedImage` hook

**Files:**
- Delete: `frontend/src/hooks/useAuthenticatedImage.ts`

- [ ] **Step 1: Delete the hook file**

Delete: `frontend/src/hooks/useAuthenticatedImage.ts`

- [ ] **Step 2: Commit**

```bash
git rm frontend/src/hooks/useAuthenticatedImage.ts
git commit -m "refactor: remove useAuthenticatedImage hook (no longer needed)"
```

---

### Task 9: Regenerate frontend API types

- [ ] **Step 1: Ask user to regenerate API types**

The backend API now returns `cover_file: str | None` instead of `has_cover: bool`. Ask the user to regenerate the frontend API types so `BookWithHighlightCount`, `BookDetails`, and `EreaderBookMetadata` TypeScript interfaces reflect the new field.

- [ ] **Step 2: Run full frontend type check**

Run: `cd frontend && npm run type-check`
Expected: PASS

- [ ] **Step 3: Run frontend lint**

Run: `cd frontend && npm run lint`
Expected: PASS

- [ ] **Step 4: Commit (if regeneration produced changes)**

```bash
git add frontend/src/api/generated/
git commit -m "chore: regenerate API types with cover_file field"
```

---

### Task 10: Run full test suite and verify

- [ ] **Step 1: Run backend tests**

Run: `cd backend && uv run pytest -x`
Expected: All tests pass.

- [ ] **Step 2: Run backend type check**

Run: `cd backend && uv run pyright`
Expected: PASS

- [ ] **Step 3: Run frontend type check and lint**

Run: `cd frontend && npm run type-check && npm run lint`
Expected: PASS

- [ ] **Step 4: Manual smoke test**

Start the app and verify:
1. Book list page loads cover images (visible in Network tab as regular `GET /api/v1/covers/{uuid}.jpg` requests, no Authorization header)
2. Books without covers show the placeholder icon
3. Book detail page shows cover
4. Browser caches covers on subsequent visits (304 or cache hit in Network tab)
