# Blurhash Cover Placeholders Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add blurhash placeholder images for book covers so the frontpage shows a blurred preview while covers load, and resize cover images to 300x420 at upload time.

**Architecture:** Add `cover_blurhash` field through all layers (domain entity -> ORM -> API schema -> frontend). Create an infrastructure-layer image processing service that resizes covers and generates blurhash strings. Integrate into the existing EPUB upload flow. Frontend decodes blurhash into a canvas placeholder and crossfades to the real image on load.

**Tech Stack:** Pillow (image resize), blurhash-python (encoding), react-blurhash (decoding/rendering)

---

### Task 1: Add Backend Dependencies

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add Pillow and blurhash-python to backend dependencies**

In `backend/pyproject.toml`, add to the `[project] dependencies` array:

```toml
"Pillow>=11.0.0",
"blurhash-python>=1.2.0",
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
cd backend && uv sync
```

Expected: Dependencies install successfully, lock file updated.

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "feat: add Pillow and blurhash-python dependencies"
```

---

### Task 2: Add `cover_blurhash` to Domain Entity

**Files:**
- Modify: `backend/src/domain/library/entities/book.py`
- Test: `backend/tests/unit/domain/library/entities/test_book.py`

- [ ] **Step 1: Write failing test for `set_cover_blurhash`**

Add to `backend/tests/unit/domain/library/entities/test_book.py`:

```python
class TestSetCoverBlurhash:
    def test_sets_blurhash_on_book(self) -> None:
        book = _make_book()
        book.set_cover_blurhash("LEHV6nWB2yk8pyo0adR*.7kCMdnj")
        assert book.cover_blurhash == "LEHV6nWB2yk8pyo0adR*.7kCMdnj"

    def test_overwrites_existing_blurhash(self) -> None:
        book = _make_book(cover_blurhash="old-hash")
        book.set_cover_blurhash("new-hash")
        assert book.cover_blurhash == "new-hash"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/domain/library/entities/test_book.py::TestSetCoverBlurhash -v`

Expected: FAIL — `cover_blurhash` attribute not found.

- [ ] **Step 3: Add `cover_blurhash` field and method to Book entity**

In `backend/src/domain/library/entities/book.py`, add after the `cover_file` field (line 39):

```python
cover_blurhash: str | None = None
```

Add a method after `set_cover_file` (after line 87):

```python
def set_cover_blurhash(self, blurhash: str) -> None:
    """Set the blurhash string for the cover image."""
    self.cover_blurhash = blurhash
```

Update both factory methods (`create` and `create_with_id`) to accept and pass through `cover_blurhash: str | None = None`.

In `create` (around line 91), add parameter `cover_blurhash: str | None = None` and pass `cover_blurhash=cover_blurhash` in the constructor call.

In `create_with_id` (around line 127), add parameter `cover_blurhash: str | None = None` and pass `cover_blurhash=cover_blurhash` in the constructor call.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/domain/library/entities/test_book.py::TestSetCoverBlurhash -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/domain/library/entities/book.py backend/tests/unit/domain/library/entities/test_book.py
git commit -m "feat: add cover_blurhash field to Book domain entity"
```

---

### Task 3: Add Database Migration

**Files:**
- Create: `backend/alembic/versions/052_add_cover_blurhash_to_books.py`
- Modify: `backend/src/models.py`

- [ ] **Step 1: Add `cover_blurhash` column to ORM model**

In `backend/src/models.py`, add after the `cover_file` mapped column (around line 179):

```python
cover_blurhash: Mapped[str | None] = mapped_column(String(40), nullable=True)
```

- [ ] **Step 2: Create Alembic migration**

Run:
```bash
cd backend && uv run alembic revision -m "add_cover_blurhash_to_books" --rev-id 052
```

Then edit the generated file at `backend/alembic/versions/052_add_cover_blurhash_to_books.py`:

```python
"""add_cover_blurhash_to_books

Revision ID: 052
Revises: 051
Create Date: 2026-04-12
"""

from alembic import op
import sqlalchemy as sa

revision = "052"
down_revision = "051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("books", sa.Column("cover_blurhash", sa.String(40), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "cover_blurhash")
```

- [ ] **Step 3: Run migration to verify it works**

Run:
```bash
cd backend && uv run alembic upgrade head
```

Expected: Migration applies successfully.

- [ ] **Step 4: Commit**

```bash
git add backend/src/models.py backend/alembic/versions/052_add_cover_blurhash_to_books.py
git commit -m "feat: add cover_blurhash column to books table"
```

---

### Task 4: Update BookMapper

**Files:**
- Modify: `backend/src/infrastructure/library/mappers/book_mapper.py`

- [ ] **Step 1: Add `cover_blurhash` to `to_domain` method**

In `backend/src/infrastructure/library/mappers/book_mapper.py`, in the `to_domain` method, add `cover_blurhash=orm_model.cover_blurhash` to the `Book.create_with_id()` call (after the `cover_file` line).

- [ ] **Step 2: Add `cover_blurhash` to `to_orm` method — update existing path**

In the "Update existing" branch of `to_orm`, add after `orm_model.cover_file = domain_entity.cover_file`:

```python
orm_model.cover_blurhash = domain_entity.cover_blurhash
```

- [ ] **Step 3: Add `cover_blurhash` to `to_orm` method — create new path**

In the "Create new" branch (the `return BookORM(...)` call), add after `cover_file=domain_entity.cover_file`:

```python
cover_blurhash=domain_entity.cover_blurhash,
```

- [ ] **Step 4: Run existing tests to verify nothing broke**

Run: `cd backend && uv run pytest tests/ -v --timeout=30 -x`

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/library/mappers/book_mapper.py
git commit -m "feat: add cover_blurhash to BookMapper"
```

---

### Task 5: Create Cover Image Processing Service

**Files:**
- Create: `backend/src/infrastructure/library/services/cover_image_service.py`
- Create: `backend/tests/unit/infrastructure/library/services/test_cover_image_service.py`

- [ ] **Step 1: Write failing tests for the cover image service**

Create `backend/tests/unit/infrastructure/library/services/test_cover_image_service.py`:

```python
"""Tests for cover image processing service."""

from io import BytesIO

import pytest
from PIL import Image

from src.infrastructure.library.services.cover_image_service import CoverImageService


def _create_test_image(width: int, height: int, color: str = "red") -> bytes:
    """Create a test JPEG image of given dimensions."""
    img = Image.new("RGB", (width, height), color)
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


class TestProcessCover:
    def test_resizes_large_image_to_fit_within_target(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        resized_bytes, blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 300
        assert img.height == 420

    def test_preserves_aspect_ratio_for_wide_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(800, 600)

        resized_bytes, blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 300
        assert img.height == 225

    def test_preserves_aspect_ratio_for_tall_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(400, 1000)

        resized_bytes, blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 168
        assert img.height == 420

    def test_does_not_upscale_small_image(self) -> None:
        service = CoverImageService()
        original = _create_test_image(100, 150)

        resized_bytes, blurhash = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.width == 100
        assert img.height == 150

    def test_returns_valid_blurhash_string(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        _, blurhash = service.process_cover(original)

        assert isinstance(blurhash, str)
        assert len(blurhash) > 0
        assert len(blurhash) <= 40

    def test_output_is_jpeg(self) -> None:
        service = CoverImageService()
        original = _create_test_image(600, 840)

        resized_bytes, _ = service.process_cover(original)

        img = Image.open(BytesIO(resized_bytes))
        assert img.format == "JPEG"

    def test_handles_png_input(self) -> None:
        service = CoverImageService()
        img = Image.new("RGBA", (600, 840), (255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        resized_bytes, blurhash = service.process_cover(png_bytes)

        result_img = Image.open(BytesIO(resized_bytes))
        assert result_img.format == "JPEG"
        assert result_img.mode == "RGB"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/infrastructure/library/services/test_cover_image_service.py -v`

Expected: FAIL — module not found.

- [ ] **Step 3: Implement the cover image service**

Create `backend/src/infrastructure/library/services/cover_image_service.py`:

```python
"""Service for processing book cover images."""

from io import BytesIO

import blurhash
from PIL import Image

MAX_WIDTH = 300
MAX_HEIGHT = 420
JPEG_QUALITY = 85
BLURHASH_X_COMPONENTS = 4
BLURHASH_Y_COMPONENTS = 3


class CoverImageService:
    """Resizes cover images and generates blurhash strings."""

    def process_cover(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Process a cover image: resize and generate blurhash.

        Args:
            image_bytes: Raw image bytes (JPEG, PNG, etc.)

        Returns:
            Tuple of (resized JPEG bytes, blurhash string)
        """
        img = Image.open(BytesIO(image_bytes))

        # Convert RGBA/palette to RGB for JPEG output
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Resize to fit within MAX_WIDTH x MAX_HEIGHT, preserving aspect ratio.
        # Only downscale, never upscale.
        if img.width > MAX_WIDTH or img.height > MAX_HEIGHT:
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

        # Generate blurhash from the (possibly resized) image
        hash_str = blurhash.encode(img, x_components=BLURHASH_X_COMPONENTS, y_components=BLURHASH_Y_COMPONENTS)

        # Save as JPEG
        output = BytesIO()
        img.save(output, format="JPEG", quality=JPEG_QUALITY)
        return output.getvalue(), hash_str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/infrastructure/library/services/test_cover_image_service.py -v`

Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/library/services/cover_image_service.py backend/tests/unit/infrastructure/library/services/test_cover_image_service.py
git commit -m "feat: add CoverImageService for resize and blurhash generation"
```

---

### Task 6: Integrate CoverImageService into EPUB Upload Flow

**Files:**
- Modify: `backend/src/application/library/use_cases/book_files/ebook_upload_use_case.py`
- Modify: `backend/src/application/library/protocols/file_repository.py` (no change needed — `save_cover` already accepts bytes)
- Modify: `backend/src/containers/library.py`

- [ ] **Step 1: Add a protocol for the image processing service**

Create `backend/src/application/library/protocols/cover_image_service.py`:

```python
from typing import Protocol


class CoverImageServiceProtocol(Protocol):
    def process_cover(self, image_bytes: bytes) -> tuple[bytes, str]: ...
```

- [ ] **Step 2: Update EbookUploadUseCase to accept and use the image service**

In `backend/src/application/library/use_cases/book_files/ebook_upload_use_case.py`:

Add import:
```python
from src.application.library.protocols.cover_image_service import CoverImageServiceProtocol
```

Add `cover_image_service: CoverImageServiceProtocol` parameter to `__init__` (after `epub_parser`):

```python
def __init__(
    self,
    book_repository: BookRepositoryProtocol,
    chapter_repository: ChapterRepositoryProtocol,
    file_repository: FileRepositoryProtocol,
    epub_parser: EpubParserProtocol,
    cover_image_service: CoverImageServiceProtocol,
    position_index_service: PositionIndexServiceProtocol,
    highlight_repository: HighlightRepositoryProtocol,
    session_repository: ReadingSessionRepositoryProtocol,
) -> None:
    ...
    self.cover_image_service = cover_image_service
    ...
```

Update `_extract_and_save_cover` to process the cover image:

```python
async def _extract_and_save_cover(
    self,
    book: Book,
    epub_content: bytes,
) -> None:
    """Extract cover from EPUB, resize, generate blurhash, and save."""
    if book.cover_file is not None:
        return

    cover_bytes = self.epub_parser.extract_cover(epub_content)
    if cover_bytes:
        processed_bytes, blurhash_str = self.cover_image_service.process_cover(cover_bytes)
        cover_filename = book.set_cover_file()
        book.set_cover_blurhash(blurhash_str)
        await self.file_repository.save_cover(cover_filename, processed_bytes)
```

- [ ] **Step 3: Wire CoverImageService in DI container**

In `backend/src/containers/library.py`, add import:

```python
from src.infrastructure.library.services.cover_image_service import CoverImageService
```

Add provider:
```python
cover_image_service = providers.Factory(CoverImageService)
```

Update `ebook_upload_use_case` factory to include `cover_image_service=cover_image_service`.

- [ ] **Step 4: Run full test suite**

Run: `cd backend && uv run pytest tests/ -v --timeout=30 -x`

Expected: All tests pass. (Existing tests that mock `EbookUploadUseCase.__init__` may need an extra mock argument — fix any that fail.)

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/library/protocols/cover_image_service.py backend/src/application/library/use_cases/book_files/ebook_upload_use_case.py backend/src/containers/library.py
git commit -m "feat: integrate CoverImageService into EPUB upload flow"
```

---

### Task 7: Update API Schemas and Routers

**Files:**
- Modify: `backend/src/infrastructure/library/schemas/book_schemas.py`
- Modify: `backend/src/infrastructure/library/routers/books.py`

- [ ] **Step 1: Add `cover_blurhash` to BookWithHighlightCount schema**

In `backend/src/infrastructure/library/schemas/book_schemas.py`, add after the `cover_file` field in `BookWithHighlightCount`:

```python
cover_blurhash: str | None = Field(None, description="Blurhash string for cover placeholder")
```

Also add it to `EreaderBookMetadata` after the `cover_file` field:

```python
cover_blurhash: str | None = Field(None, description="Blurhash string for cover placeholder")
```

- [ ] **Step 2: Pass `cover_blurhash` in router schema construction**

In `backend/src/infrastructure/library/routers/books.py`, in every place where `BookWithHighlightCount(...)` is constructed (there are 3 locations: `get_books`, `get_recently_viewed_books`, and `update_book`), add after `cover_file=book.cover_file`:

```python
cover_blurhash=book.cover_blurhash,
```

Also in `_build_book_details_schema`, if `BookDetails` includes `cover_file`, add `cover_blurhash=agg.book.cover_blurhash` there too.

In `backend/src/infrastructure/library/routers/ereader.py`, in both places where `EreaderBookMetadata(...)` is constructed, add after `cover_file=metadata.cover_file`:

```python
cover_blurhash=metadata.cover_blurhash,
```

Note: The `metadata` object comes from a use case — you may need to check that `cover_blurhash` flows through the ereader metadata use case. If the metadata DTO/entity doesn't include `cover_blurhash`, add it there too.

- [ ] **Step 3: Run tests and type check**

Run:
```bash
cd backend && uv run pytest tests/ -v --timeout=30 -x
cd backend && uv run pyright src/infrastructure/library/schemas/book_schemas.py src/infrastructure/library/routers/books.py src/infrastructure/library/routers/ereader.py
```

Expected: All pass.

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/library/schemas/book_schemas.py backend/src/infrastructure/library/routers/books.py backend/src/infrastructure/library/routers/ereader.py
git commit -m "feat: add cover_blurhash to API schemas and routers"
```

---

### Task 8: Add Frontend Dependency and Update BookCover Component

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/components/BookCover.tsx`

- [ ] **Step 1: Install react-blurhash**

Run:
```bash
cd frontend && npm install react-blurhash
```

- [ ] **Step 2: Regenerate API types**

Start the backend server, then run:
```bash
cd frontend && npm run api:generate
```

Verify the generated `BookWithHighlightCount` type now includes `cover_blurhash: string | null`.

- [ ] **Step 3: Update BookCover component**

Replace the contents of `frontend/src/components/BookCover.tsx` with:

```tsx
import { useState } from 'react';
import { Blurhash } from 'react-blurhash';
import { BookCoverIcon } from '@/theme/Icons.tsx';
import { Box, type SxProps, type Theme, useTheme } from '@mui/material';

/** Neutral gray fallback for books without a generated blurhash. */
const FALLBACK_BLURHASH = 'L6PZfSi_.AyE_3t7t7R**0o#DgR4';

export interface BookCoverProps {
  coverFile: string | null;
  title: string;
  /**
   * Blurhash string for placeholder. Falls back to a neutral default if null.
   */
  blurhash?: string | null;
  width?: number | string | { xs?: number | string; sm?: number | string };
  height?: number | string | { xs?: number | string; sm?: number | string };
  objectFit?: 'contain' | 'cover';
  sx?: SxProps<Theme>;
}

export const BookCover = ({
  coverFile,
  title,
  blurhash,
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
  const showPlaceholder = !coverUrl;
  const [imageLoaded, setImageLoaded] = useState(false);

  // Resolve numeric dimensions for Blurhash (needs numbers, not strings)
  const numericWidth = typeof width === 'number' ? width : 150;
  const numericHeight = typeof height === 'number' ? height : 200;

  return (
    <Box
      className="book-cover"
      sx={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        position: 'relative',
        ...sx,
      }}
    >
      {coverUrl ? (
        <>
          {/* Blurhash placeholder — visible until image loads */}
          {!imageLoaded && (
            <Box
              sx={{
                position: 'absolute',
                inset: 0,
              }}
            >
              <Blurhash
                hash={blurhash || FALLBACK_BLURHASH}
                width="100%"
                height="100%"
              />
            </Box>
          )}

          {/* Actual cover image */}
          <img
            src={coverUrl}
            alt={`${title} cover`}
            style={{
              width: '100%',
              height: '100%',
              objectFit,
              opacity: imageLoaded ? 1 : 0,
              transition: 'opacity 0.3s ease-in',
            }}
            onLoad={() => setImageLoaded(true)}
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              const placeholder = e.currentTarget
                .parentElement!.querySelector('.book-cover-icon-fallback') as HTMLElement | null;
              if (placeholder) placeholder.style.display = 'flex';
            }}
          />

          {/* Icon fallback for broken images */}
          <Box
            className="book-cover-icon-fallback"
            sx={{
              display: 'none',
              alignItems: 'center',
              justifyContent: 'center',
              width: '100%',
              height: '100%',
              background: theme.palette.action.hover,
            }}
          >
            <BookCoverIcon
              sx={{
                fontSize: numericHeight * 0.4,
                color: 'text.disabled',
                opacity: 1,
              }}
            />
          </Box>
        </>
      ) : (
        /* No cover file at all — show icon placeholder */
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            height: '100%',
            background: theme.palette.action.hover,
          }}
        >
          <BookCoverIcon
            sx={{
              fontSize: numericHeight * 0.4,
              color: 'text.disabled',
              opacity: 1,
            }}
          />
        </Box>
      )}
    </Box>
  );
};
```

- [ ] **Step 4: Run frontend type check and lint**

Run:
```bash
cd frontend && npm run type-check && npm run lint
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/BookCover.tsx frontend/src/api/generated/
git commit -m "feat: add blurhash placeholder to BookCover component"
```

---

### Task 9: Pass Blurhash Through BookCard

**Files:**
- Modify: `frontend/src/pages/LandingPage/components/BookCard.tsx`

- [ ] **Step 1: Pass `blurhash` prop to BookCover in BookCard**

In `frontend/src/pages/LandingPage/components/BookCard.tsx`, update the `<BookCover>` usage (around line 42) to include the blurhash:

```tsx
<BookCover
  coverFile={book.cover_file ?? null}
  title={book.title}
  blurhash={book.cover_blurhash}
  width={150}
  height={220}
  objectFit="cover"
  sx={{
    boxShadow: 3,
    borderRadius: 1,
    transition: 'box-shadow 0.3s ease',
  }}
/>
```

- [ ] **Step 2: Check for other BookCover usages that should also pass blurhash**

Run:
```bash
cd frontend && grep -rn "BookCover" src/ --include="*.tsx" --include="*.ts"
```

For each usage that has access to a book object with `cover_blurhash`, pass it through. If a usage doesn't have access to the blurhash (e.g., it only receives `coverFile` as a string), the component will fall back to the default — no change needed.

- [ ] **Step 3: Run frontend type check and lint**

Run:
```bash
cd frontend && npm run type-check && npm run lint
```

Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/LandingPage/components/BookCard.tsx
git commit -m "feat: pass cover_blurhash from BookCard to BookCover"
```

---

### Task 10: Manual Verification

- [ ] **Step 1: Run full backend test suite**

Run:
```bash
cd backend && uv run pytest tests/ -v --timeout=30
```

Expected: All tests pass.

- [ ] **Step 2: Run backend type check**

Run:
```bash
cd backend && uv run pyright
```

Expected: No errors.

- [ ] **Step 3: Run frontend checks**

Run:
```bash
cd frontend && npm run type-check && npm run lint
```

Expected: No errors.

- [ ] **Step 4: Manual test — upload an EPUB and verify**

1. Start backend: `cd backend && uv run uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Upload a book via KOReader or the UI
4. Check the database: the book should now have a `cover_blurhash` value
5. Check the frontpage: the cover should show a blurred placeholder briefly before the real image fades in
6. Check an existing book (no blurhash): should show the neutral default placeholder during load
