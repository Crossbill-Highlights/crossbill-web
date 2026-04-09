# UUID File References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace title/ID-based file naming with UUID4-based filenames for book ebooks and covers, making file references unguessable and stable across re-uploads.

**Architecture:** The Book domain entity generates UUID filenames on first upload via `set_file()` and `set_cover_file()`. File repositories become simple storage layers that accept a filename + content. A migration clears existing file references.

**Tech Stack:** Python, SQLAlchemy, Alembic, uuid4, pytest

**Spec:** `docs/superpowers/specs/2026-04-09-uuid-file-references-design.md`

---

### Task 1: Add `set_file` and `set_cover_file` to Book domain entity

**Files:**
- Modify: `backend/src/domain/library/entities/book.py:64-72` (replace `update_file` and `update_cover_file`)
- Create: `backend/tests/unit/domain/library/entities/test_book.py`

- [ ] **Step 1: Write failing tests for `set_file`**

Create `backend/tests/unit/domain/library/entities/test_book.py`:

```python
"""Unit tests for Book entity file reference methods."""

import uuid

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book


def _make_book(**overrides: object) -> Book:
    """Create a Book with sensible defaults for testing."""
    from datetime import UTC, datetime

    defaults: dict = {
        "id": BookId(1),
        "user_id": UserId(1),
        "title": "Test Book",
        "created_at": datetime(2024, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2024, 1, 1, tzinfo=UTC),
    }
    defaults.update(overrides)
    return Book(**defaults)


class TestSetFile:
    def test_generates_uuid_epub_filename_when_no_file_set(self) -> None:
        book = _make_book()

        filename = book.set_file("epub")

        assert filename.endswith(".epub")
        # Validate that the stem is a valid UUID
        stem = filename.removesuffix(".epub")
        uuid.UUID(stem)  # Raises if not valid UUID
        assert book.ebook_file == filename
        assert book.file_type == "epub"

    def test_generates_uuid_pdf_filename_when_no_file_set(self) -> None:
        book = _make_book()

        filename = book.set_file("pdf")

        assert filename.endswith(".pdf")
        stem = filename.removesuffix(".pdf")
        uuid.UUID(stem)
        assert book.ebook_file == filename
        assert book.file_type == "pdf"

    def test_returns_existing_filename_on_reupload(self) -> None:
        book = _make_book(ebook_file="existing-uuid.epub", file_type="epub")

        filename = book.set_file("epub")

        assert filename == "existing-uuid.epub"
        assert book.ebook_file == "existing-uuid.epub"

    def test_rejects_invalid_file_type(self) -> None:
        book = _make_book()

        with pytest.raises(DomainError, match="Invalid file type"):
            book.set_file("docx")

    def test_generates_unique_uuids(self) -> None:
        book1 = _make_book()
        book2 = _make_book()

        filename1 = book1.set_file("epub")
        filename2 = book2.set_file("epub")

        assert filename1 != filename2


class TestSetCoverFile:
    def test_generates_uuid_jpg_filename_when_no_cover_set(self) -> None:
        book = _make_book()

        filename = book.set_cover_file()

        assert filename.endswith(".jpg")
        stem = filename.removesuffix(".jpg")
        uuid.UUID(stem)
        assert book.cover_file == filename

    def test_returns_existing_filename_on_reupload(self) -> None:
        book = _make_book(cover_file="existing-uuid.jpg")

        filename = book.set_cover_file()

        assert filename == "existing-uuid.jpg"
        assert book.cover_file == "existing-uuid.jpg"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/domain/library/entities/test_book.py -v`
Expected: FAIL — `Book` has no `set_file` or `set_cover_file` methods.

- [ ] **Step 3: Implement `set_file` and `set_cover_file` on Book entity**

In `backend/src/domain/library/entities/book.py`, add `import uuid` at the top, then replace the `update_file` and `update_cover_file` methods (lines 64-72) with:

```python
def set_file(self, file_type: str) -> str:
    """Set ebook file reference, generating a UUID filename on first upload.

    Returns the filename (existing or newly generated).
    """
    if file_type not in ("epub", "pdf"):
        raise DomainError(f"Invalid file type: {file_type}")
    if self.ebook_file is not None:
        self.file_type = file_type
        return self.ebook_file
    self.ebook_file = f"{uuid.uuid4()}.{file_type}"
    self.file_type = file_type
    return self.ebook_file

def set_cover_file(self) -> str:
    """Set cover file reference, generating a UUID filename on first upload.

    Returns the filename (existing or newly generated).
    """
    if self.cover_file is not None:
        return self.cover_file
    self.cover_file = f"{uuid.uuid4()}.jpg"
    return self.cover_file
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/domain/library/entities/test_book.py -v`
Expected: All PASS.

- [ ] **Step 5: Run pyright on the modified file**

Run: `cd backend && uv run pyright src/domain/library/entities/book.py`
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add backend/src/domain/library/entities/book.py backend/tests/unit/domain/library/entities/test_book.py
git commit -m "feat: add set_file and set_cover_file with UUID generation to Book entity"
```

---

### Task 2: Update FileRepositoryProtocol signatures

**Files:**
- Modify: `backend/src/application/library/protocols/file_repository.py:1-24`

- [ ] **Step 1: Update the protocol**

Replace the entire file content with:

```python
from typing import Protocol


class FileRepositoryProtocol(Protocol):
    async def save_epub(self, filename: str, content: bytes) -> str: ...

    async def save_pdf(self, filename: str, content: bytes) -> str: ...

    async def save_cover(self, filename: str, content: bytes) -> str: ...

    async def delete_epub(self, filename: str | None) -> bool: ...

    async def delete_pdf(self, filename: str | None) -> bool: ...

    async def delete_cover(self, filename: str | None) -> bool: ...

    async def get_epub(self, filename: str | None) -> bytes | None: ...

    async def get_pdf(self, filename: str | None) -> bytes | None: ...

    async def get_cover(self, filename: str | None) -> bytes | None: ...
```

Note: the `BookId` import is removed since save methods no longer take `book_id`.

- [ ] **Step 2: Run pyright to check for downstream breakage**

Run: `cd backend && uv run pyright src/application/library/protocols/file_repository.py`
Expected: No errors on the protocol itself. (Implementations will break — fixed in next tasks.)

- [ ] **Step 3: Commit**

```bash
git add backend/src/application/library/protocols/file_repository.py
git commit -m "refactor: simplify FileRepositoryProtocol save methods to accept filename + content"
```

---

### Task 3: Update local FileRepository implementation

**Files:**
- Modify: `backend/src/infrastructure/library/repositories/file_repository.py:1-66`

- [ ] **Step 1: Update the implementation**

Replace save methods and remove unused imports/helpers. The new file should:

1. Remove `import re` and `from src.domain.common.value_objects.ids import BookId`
2. Remove the `_sanitize_title` function entirely (lines 19-42)
3. Replace `save_epub` (lines 48-66) with:

```python
async def save_epub(self, filename: str, content: bytes) -> str:
    """Save an EPUB file to disk."""
    _validate_filename(filename)
    await asyncio.to_thread(lambda: EPUBS_DIR.mkdir(parents=True, exist_ok=True))
    file_path = EPUBS_DIR / filename
    await asyncio.to_thread(file_path.write_bytes, content)
    logger.info(f"Saved EPUB file: {file_path}")
    return file_path.name
```

4. Replace `save_pdf` (lines 68-85) with:

```python
async def save_pdf(self, filename: str, content: bytes) -> str:
    """Save a PDF file to disk."""
    _validate_filename(filename)
    await asyncio.to_thread(lambda: PDFS_DIR.mkdir(parents=True, exist_ok=True))
    file_path = PDFS_DIR / filename
    await asyncio.to_thread(file_path.write_bytes, content)
    logger.info(f"Saved PDF file: {file_path}")
    return file_path.name
```

5. Replace `save_cover` (lines 87-103) with:

```python
async def save_cover(self, filename: str, content: bytes) -> str:
    """Save a cover image to disk."""
    _validate_filename(filename)
    await asyncio.to_thread(lambda: BOOK_COVERS_DIR.mkdir(parents=True, exist_ok=True))
    file_path = BOOK_COVERS_DIR / filename
    await asyncio.to_thread(file_path.write_bytes, content)
    logger.info(f"Saved cover file: {file_path}")
    return file_path.name
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/library/repositories/file_repository.py`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/library/repositories/file_repository.py
git commit -m "refactor: update local FileRepository to accept filename instead of book_id/title"
```

---

### Task 4: Update S3FileRepository implementation and its tests

**Files:**
- Modify: `backend/src/infrastructure/library/repositories/s3_file_repository.py:1-104`
- Modify: `backend/tests/unit/infrastructure/library/repositories/test_s3_file_repository.py`

- [ ] **Step 1: Update the S3 implementation**

1. Remove `import re` and `from src.domain.common.value_objects.ids import BookId`
2. Remove the `_sanitize_title` function entirely (lines 20-38)
3. Replace `save_epub` (lines 87-104) with:

```python
async def save_epub(self, filename: str, content: bytes) -> str:
    """Upload an EPUB file to S3."""
    _validate_filename(filename)
    key = f"epubs/{filename}"
    await asyncio.to_thread(self._client.put_object, Bucket=self._bucket, Key=key, Body=content)
    logger.info(f"Uploaded EPUB to S3: {key}")
    return filename
```

4. Replace `save_pdf` (lines 106-123) with:

```python
async def save_pdf(self, filename: str, content: bytes) -> str:
    """Upload a PDF file to S3."""
    _validate_filename(filename)
    key = f"pdfs/{filename}"
    await asyncio.to_thread(self._client.put_object, Bucket=self._bucket, Key=key, Body=content)
    logger.info(f"Uploaded PDF to S3: {key}")
    return filename
```

5. Replace `save_cover` (lines 125-140) with:

```python
async def save_cover(self, filename: str, content: bytes) -> str:
    """Upload a cover image to S3."""
    _validate_filename(filename)
    key = f"book-covers/{filename}"
    await asyncio.to_thread(self._client.put_object, Bucket=self._bucket, Key=key, Body=content)
    logger.info(f"Uploaded cover to S3: {key}")
    return filename
```

- [ ] **Step 2: Update S3 save tests**

In `backend/tests/unit/infrastructure/library/repositories/test_s3_file_repository.py`:

1. Remove the `book_id` fixture (lines 13-14) and the `BookId` import (line 5)
2. Replace `test_save_epub_uploads_with_correct_key` (lines 36-46) with:

```python
@pytest.mark.asyncio
async def test_save_epub_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock
) -> None:
    filename = await repo.save_epub("abc123.epub", b"epub-bytes")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="epubs/abc123.epub",
        Body=b"epub-bytes",
    )
    assert filename == "abc123.epub"
```

3. Remove `test_save_epub_sanitizes_title` (lines 49-57) — no longer relevant.

4. Replace `test_save_pdf_uploads_with_correct_key` (lines 65-76) with:

```python
@pytest.mark.asyncio
async def test_save_pdf_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock
) -> None:
    filename = await repo.save_pdf("abc123.pdf", b"pdf-bytes")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="pdfs/abc123.pdf",
        Body=b"pdf-bytes",
    )
    assert filename == "abc123.pdf"
```

5. Remove `test_save_pdf_sanitizes_title` (lines 79-85) — no longer relevant.

6. Replace `test_save_cover_uploads_with_correct_key` (lines 93-104) with:

```python
@pytest.mark.asyncio
async def test_save_cover_uploads_with_correct_key(
    repo: S3FileRepository, s3_client: MagicMock
) -> None:
    filename = await repo.save_cover("abc123.jpg", b"image-bytes")

    s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket",
        Key="book-covers/abc123.jpg",
        Body=b"image-bytes",
    )
    assert filename == "abc123.jpg"
```

7. Remove `book_id` from all remaining test function signatures that reference it (the get/delete tests don't use `book_id` as a parameter, but check if the fixture is used anywhere — it is not used in get/delete tests, so removing the fixture is safe).

- [ ] **Step 3: Run tests**

Run: `cd backend && uv run pytest tests/unit/infrastructure/library/repositories/test_s3_file_repository.py -v`
Expected: All PASS.

- [ ] **Step 4: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/library/repositories/s3_file_repository.py`
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/library/repositories/s3_file_repository.py backend/tests/unit/infrastructure/library/repositories/test_s3_file_repository.py
git commit -m "refactor: update S3FileRepository to accept filename instead of book_id/title"
```

---

### Task 5: Update EbookUploadUseCase to use new Book entity methods

**Files:**
- Modify: `backend/src/application/library/use_cases/book_files/ebook_upload_use_case.py:119-176`

- [ ] **Step 1: Update `_upload_epub` method**

In `_upload_epub` (lines 87-162), replace lines 120-127:

```python
# Delete old ebook file if exists
await self.file_repository.delete_epub(book.ebook_file)

epub_filename = await self.file_repository.save_epub(book.id, content, book.title)
book.update_file(epub_filename, "epub")

# Extract and save cover if none exists
await self._extract_and_save_cover(book, content)
```

With:

```python
# Get or generate UUID filename
epub_filename = book.set_file("epub")
await self.file_repository.save_epub(epub_filename, content)

# Extract and save cover if none exists
await self._extract_and_save_cover(book, content)
```

- [ ] **Step 2: Update `_extract_and_save_cover` method**

Replace lines 164-176:

```python
async def _extract_and_save_cover(
    self,
    book: Book,
    epub_content: bytes,
) -> None:
    """Extract cover from EPUB and save it, if no cover already exists."""
    if book.cover_file is not None:
        return

    cover_bytes = self.epub_parser.extract_cover(epub_content)
    if cover_bytes:
        cover_filename = await self.file_repository.save_cover(book.id, cover_bytes)
        book.update_cover_file(cover_filename)
```

With:

```python
async def _extract_and_save_cover(
    self,
    book: Book,
    epub_content: bytes,
) -> None:
    """Extract cover from EPUB and save it, if no cover already exists."""
    if book.cover_file is not None:
        return

    cover_bytes = self.epub_parser.extract_cover(epub_content)
    if cover_bytes:
        cover_filename = book.set_cover_file()
        await self.file_repository.save_cover(cover_filename, cover_bytes)
```

- [ ] **Step 3: Check for any other callers of `update_file` or `update_cover_file`**

Run: `cd backend && grep -r "update_file\|update_cover_file" src/ --include="*.py"`

If any other callers exist, update them to use `set_file` / `set_cover_file` accordingly.

- [ ] **Step 4: Run pyright**

Run: `cd backend && uv run pyright src/application/library/use_cases/book_files/ebook_upload_use_case.py`
Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/library/use_cases/book_files/ebook_upload_use_case.py
git commit -m "feat: use Book entity UUID generation in ebook upload use case"
```

---

### Task 6: Alembic migration to clear existing file references

**Files:**
- Create: `backend/alembic/versions/051_clear_file_references_for_uuid_migration.py`

- [ ] **Step 1: Create migration**

Create `backend/alembic/versions/051_clear_file_references_for_uuid_migration.py`:

```python
"""Clear file references for UUID migration.

Clears ebook_file, file_type, and cover_file columns so that
users re-upload files with new UUID-based filenames.

Revision ID: 051
Revises: 050
Create Date: 2026-04-09

"""

from collections.abc import Sequence

from alembic import op

revision: str = "051"
down_revision: str | None = "050"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE books SET ebook_file = NULL, file_type = NULL, cover_file = NULL")


def downgrade() -> None:
    # Cannot restore old filenames; no-op
    pass
```

- [ ] **Step 2: Commit**

```bash
git add backend/alembic/versions/051_clear_file_references_for_uuid_migration.py
git commit -m "migration: clear file references for UUID-based filenames"
```

---

### Task 7: Run full test suite and verify

- [ ] **Step 1: Run all tests**

Run: `cd backend && uv run pytest -v`
Expected: All tests pass. If any tests call `save_epub(book_id, content, title)` or similar with old signatures, update them.

- [ ] **Step 2: Run full pyright check**

Run: `cd backend && uv run pyright`
Expected: No new errors.

- [ ] **Step 3: Run ruff**

Run: `cd backend && uv run ruff check src/ tests/`
Expected: No errors.

- [ ] **Step 4: Fix any failures found in steps 1-3, then commit**

```bash
git add -u
git commit -m "fix: resolve test/type issues from UUID file references migration"
```
