"""Tests for highlights API endpoints."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models, schemas
from tests.conftest import create_test_book

# Type alias for the book creation fixture
CreateBookFunc = Callable[[dict[str, Any]], schemas.EreaderBookMetadata]


@pytest.fixture
def create_book_via_api(client: TestClient) -> CreateBookFunc:
    """Fixture factory for creating books via the API endpoint.

    Returns a function that can be called with book data to create a book.
    """

    def _create_book(book_data: dict[str, Any]) -> schemas.EreaderBookMetadata:
        """Create a book via POST /api/v1/ereader/books endpoint.

        Args:
            book_data: Dictionary with book creation data (client_book_id, title, etc.)

        Returns:
            EreaderBookMetadata response from the API
        """
        response = client.post("/api/v1/ereader/books", json=book_data)
        assert response.status_code == status.HTTP_200_OK
        return schemas.EreaderBookMetadata(**response.json())

    return _create_book


class TestHighlightsUpload:
    """Test suite for highlights upload endpoint."""

    def test_upload_highlights_success(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test successful upload of highlights."""
        # Create the book via the fixture
        create_book_via_api(
            {
                "client_book_id": "test-client-book-id",
                "title": "Test Book",
                "author": "Test Author",
                "isbn": "1234567890",
            }
        )

        # Upload highlights
        payload = {
            "book": {
                "client_book_id": "test-client-book-id",
                "title": "Test Book",
                "author": "Test Author",
                "isbn": "1234567890",
            },
            "highlights": [
                {
                    "text": "Test highlight 1",
                    "chapter": "Chapter 1",
                    "page": 10,
                    "note": "Test note 1",
                    "datetime": "2024-01-15 14:30:22",
                },
                {
                    "text": "Test highlight 2",
                    "chapter": "Chapter 2",
                    "page": 25,
                    "note": "Test note 2",
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["highlights_created"] == 2
        assert data["highlights_skipped"] == 0
        assert "book_id" in data
        assert "Successfully synced highlights" in data["message"]

        # Verify book was created in database
        book = (
            db_session.query(models.Book).filter_by(title="Test Book", author="Test Author").first()
        )
        assert book is not None
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.isbn == "1234567890"

        # Verify highlights were created
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 2

        # Verify NO chapters were created (highlights without chapter_number don't create chapters)
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify highlights have no chapter association (no chapter_number provided)
        for highlight in highlights:
            assert highlight.chapter_id is None

    def test_upload_highlights_without_chapter(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test uploading highlights without chapter information."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-book-id-no-chapters",
                "title": "Test Book Without Chapters",
                "author": "Test Author",
            }
        )

        # Upload highlights
        payload = {
            "book": {
                "client_book_id": "test-client-book-id-no-chapters",
                "title": "Test Book Without Chapters",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight without chapter",
                    "page": 5,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["highlights_created"] == 1
        assert data["highlights_skipped"] == 0

        # Verify no chapters were created
        book = (
            db_session.query(models.Book)
            .filter_by(title="Test Book Without Chapters", author="Test Author")
            .first()
        )
        assert book is not None
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify highlight was created without chapter_id
        highlight = db_session.query(models.Highlight).filter_by(book_id=book.id).first()
        assert highlight is not None
        assert highlight.chapter_id is None

    def test_upload_highlights_with_xpoints(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test uploading highlights with start_xpoint and end_xpoint fields."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-book-xpoints",
                "title": "Test Book With Xpoints",
                "author": "Test Author",
            }
        )

        # Upload highlights
        payload = {
            "book": {
                "client_book_id": "test-client-book-xpoints",
                "title": "Test Book With Xpoints",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight with xpoints",
                    "chapter": "Chapter 1",
                    "page": 10,
                    "start_xpoint": "/body/div[1]/p[5]/text()[1].0",
                    "end_xpoint": "/body/div[1]/p[5]/text()[1].42",
                    "datetime": "2024-01-15 14:30:22",
                },
                {
                    "text": "Highlight without xpoints",
                    "chapter": "Chapter 2",
                    "page": 20,
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["highlights_created"] == 2

        # Verify xpoints were stored in database
        book = (
            db_session.query(models.Book)
            .filter_by(title="Test Book With Xpoints", author="Test Author")
            .first()
        )
        assert book is not None

        highlights = (
            db_session.query(models.Highlight)
            .filter_by(book_id=book.id)
            .order_by(models.Highlight.page)
            .all()
        )
        assert len(highlights) == 2

        # First highlight should have xpoints
        assert highlights[0].start_xpoint == "/body/div[1]/p[5]/text()[1].0"
        assert highlights[0].end_xpoint == "/body/div[1]/p[5]/text()[1].42"

        # Second highlight should have null xpoints
        assert highlights[1].start_xpoint is None
        assert highlights[1].end_xpoint is None

    def test_upload_duplicate_highlights(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that duplicate highlights are properly skipped."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-duplicate-book",
                "title": "Duplicate Test Book",
                "author": "Test Author",
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-duplicate-book",
                "title": "Duplicate Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Duplicate highlight",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        # First upload
        response1 = client.post("/api/v1/highlights/upload", json=payload)
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert data1["highlights_created"] == 1
        assert data1["highlights_skipped"] == 0

        # Second upload (should skip duplicate)
        response2 = client.post("/api/v1/highlights/upload", json=payload)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["highlights_created"] == 0
        assert data2["highlights_skipped"] == 1

        # Verify only one highlight exists in database
        book = (
            db_session.query(models.Book)
            .filter_by(title="Duplicate Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 1

    def test_upload_partial_duplicates(
        self, client: TestClient, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test uploading mix of new and duplicate highlights."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-partial-dup",
                "title": "Partial Duplicate Test Book",
                "author": "Test Author",
            }
        )

        # First upload
        payload1 = {
            "book": {
                "client_book_id": "test-client-partial-dup",
                "title": "Partial Duplicate Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight 1",
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Highlight 2",
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        response1 = client.post("/api/v1/highlights/upload", json=payload1)
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["highlights_created"] == 2

        # Second upload with mix of new and duplicate
        payload2 = {
            "book": {
                "client_book_id": "test-client-partial-dup",
                "title": "Partial Duplicate Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight 1",  # Duplicate
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Highlight 3",  # New
                    "datetime": "2024-01-15 16:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["highlights_created"] == 1
        assert data2["highlights_skipped"] == 1

    def test_upload_preserves_edited_book_metadata(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that user edits to book metadata are preserved during re-sync.

        When a user edits a book's title/author in the app, subsequent syncs from
        the device should NOT overwrite those edits. The book is identified by
        its content_hash (computed from original title+author), allowing metadata
        to be edited independently.
        """
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-original",
                "title": "Original Title",
                "author": "Original Author",
                "isbn": "1111111111",
            }
        )

        # First upload
        payload1 = {
            "book": {
                "client_book_id": "test-client-original",
                "title": "Original Title",
                "author": "Original Author",
                "isbn": "1111111111",
            },
            "highlights": [
                {
                    "text": "Highlight 1",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response1 = client.post("/api/v1/highlights/upload", json=payload1)
        assert response1.status_code == status.HTTP_200_OK
        book_id = response1.json()["book_id"]

        # Simulate user editing the book metadata in the app
        book = db_session.query(models.Book).filter_by(id=book_id).first()
        assert book is not None
        book.title = "User Edited Title"
        book.author = "User Edited Author"
        book.isbn = "9999999999"
        db_session.commit()

        # Second upload from device with original metadata (same hash)
        # This should NOT overwrite the user's edits
        payload2 = {
            "book": {
                "client_book_id": "test-client-original",
                "title": "Original Title",  # Original title from device
                "author": "Original Author",  # Original author from device
                "isbn": "1111111111",
            },
            "highlights": [
                {
                    "text": "Highlight 2",
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["book_id"] == book_id  # Same book (matched by hash)

        # Verify user's metadata edits were PRESERVED (not overwritten)
        db_session.refresh(book)
        assert book.title == "User Edited Title"
        assert book.author == "User Edited Author"
        assert book.isbn == "9999999999"

        # Verify both highlights exist on the same book
        highlights = db_session.query(models.Highlight).filter_by(book_id=book_id).all()
        assert len(highlights) == 2

    def test_upload_empty_highlights_list(
        self, client: TestClient, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test uploading with empty highlights list."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-empty",
                "title": "Empty Highlights Book",
                "author": "Test Author",
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-empty",
                "title": "Empty Highlights Book",
                "author": "Test Author",
            },
            "highlights": [],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["highlights_created"] == 0
        assert data["highlights_skipped"] == 0

    def test_upload_same_text_different_datetime_is_duplicate(
        self, client: TestClient, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that same text at different times is considered duplicate (hash-based dedup).

        With hash-based deduplication, the hash is computed from text + book_title + author.
        Datetime is NOT part of the hash, so same text in the same book is a duplicate.
        """
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-same-text",
                "title": "Same Text Test Book",
                "author": "Test Author",
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-same-text",
                "title": "Same Text Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Same text",
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Same text",
                    "datetime": "2024-01-15 15:00:00",  # Different datetime, same hash
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # With hash-based dedup, only 1 is created (same text = same hash)
        assert data["highlights_created"] == 1
        assert data["highlights_skipped"] == 1

    def test_upload_same_text_different_book_not_duplicate(
        self, client: TestClient, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that same text in different books creates separate highlights.

        The hash includes book_title and author, so same text in different books
        will have different hashes and create separate highlights.
        """
        # Create the first book
        create_book_via_api(
            {
                "client_book_id": "test-client-first-book",
                "title": "First Book",
                "author": "Author A",
            }
        )

        # First book
        payload1 = {
            "book": {
                "client_book_id": "test-client-first-book",
                "title": "First Book",
                "author": "Author A",
            },
            "highlights": [
                {
                    "text": "Same highlight text",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response1 = client.post("/api/v1/highlights/upload", json=payload1)
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["highlights_created"] == 1

        # Create the second book
        create_book_via_api(
            {
                "client_book_id": "test-client-second-book",
                "title": "Second Book",
                "author": "Author B",
            }
        )

        # Second book with same text
        payload2 = {
            "book": {
                "client_book_id": "test-client-second-book",
                "title": "Second Book",
                "author": "Author B",
            },
            "highlights": [
                {
                    "text": "Same highlight text",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        # Different book means different hash, so it's created
        assert response2.json()["highlights_created"] == 1
        assert response2.json()["highlights_skipped"] == 0

    def test_highlight_has_content_hash(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that created highlights have a content_hash field populated."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-hash-test",
                "title": "Hash Test Book",
                "author": "Test Author",
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-hash-test",
                "title": "Hash Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Test highlight for hash",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)
        assert response.status_code == status.HTTP_200_OK

        # Verify highlight has content_hash
        book = (
            db_session.query(models.Book)
            .filter_by(title="Hash Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        highlight = db_session.query(models.Highlight).filter_by(book_id=book.id).first()
        assert highlight is not None
        assert highlight.content_hash is not None
        assert len(highlight.content_hash) == 64  # SHA-256 hex string length

    def test_upload_invalid_payload_missing_book(self, client: TestClient) -> None:
        """Test upload with missing book data."""
        payload = {
            "highlights": [
                {
                    "text": "Test highlight",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_upload_invalid_payload_missing_required_fields(self, client: TestClient) -> None:
        """Test upload with missing required fields."""
        payload = {
            "book": {
                "client_book_id": "test-client-minimal",
                "title": "Test Book",
                # Missing required fields are okay (author, isbn are optional)
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    # Missing datetime
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_upload_creates_chapter_only_once(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that multiple highlights without chapter_number don't create chapters."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-chapter-dedup",
                "title": "Chapter Dedup Test Book",
                "author": "Test Author",
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-chapter-dedup",
                "title": "Chapter Dedup Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight 1 in Chapter 1",
                    "chapter": "Chapter 1",
                    # No chapter_number provided
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Highlight 2 in Chapter 1",
                    "chapter": "Chapter 1",
                    # No chapter_number provided
                    "datetime": "2024-01-15 15:00:00",
                },
                {
                    "text": "Highlight 3 in Chapter 1",
                    "chapter": "Chapter 1",
                    # No chapter_number provided
                    "datetime": "2024-01-15 16:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 3

        # Verify NO chapters were created (highlights without chapter_number don't create chapters)
        book = (
            db_session.query(models.Book)
            .filter_by(title="Chapter Dedup Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify all highlights were created but have no chapter association
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 3
        assert all(h.chapter_id is None for h in highlights)

    def test_upload_with_duplicates_and_new_chapters(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that duplicate highlights are properly skipped.

        Since chapters are no longer created during highlight upload (only via EPUB ToC),
        this test verifies that duplicate detection still works correctly.
        """
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-rollback-bug",
                "title": "Rollback Bug Test Book",
                "author": "Test Author",
            }
        )

        # First upload with some highlights
        payload1 = {
            "book": {
                "client_book_id": "test-client-rollback-bug",
                "title": "Rollback Bug Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "First highlight in Chapter 1",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Second highlight in Chapter 1",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:30:00",
                },
            ],
        }

        response1 = client.post("/api/v1/highlights/upload", json=payload1)
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["highlights_created"] == 2

        # Second upload with mix of duplicates and new highlights
        payload2 = {
            "book": {
                "client_book_id": "test-client-rollback-bug",
                "title": "Rollback Bug Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "First highlight in Chapter 1",  # Duplicate
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "New highlight in Chapter 2",  # New
                    "chapter": "Chapter 2",
                    "datetime": "2024-01-15 15:00:00",
                },
                {
                    "text": "Second highlight in Chapter 1",  # Duplicate
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:30:00",
                },
                {
                    "text": "Another new highlight in Chapter 3",  # New
                    "chapter": "Chapter 3",
                    "datetime": "2024-01-15 16:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["highlights_created"] == 2  # Two new highlights
        assert data2["highlights_skipped"] == 2  # Both duplicates

        # Verify NO chapters were created (highlights without chapter_number don't create chapters)
        book = (
            db_session.query(models.Book)
            .filter_by(title="Rollback Bug Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify all 4 unique highlights exist (2 from first upload, 2 new from second)
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 4

        # Verify all highlights have no chapter association (no chapter_number provided)
        assert all(h.chapter_id is None for h in highlights)

    def test_upload_with_language_and_page_count(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test uploading highlights with language and page_count metadata."""
        # Create the book
        create_book_via_api(
            {
                "client_book_id": "test-client-metadata",
                "title": "Test Book with Metadata",
                "author": "Test Author",
                "language": "en",
                "page_count": 350,
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-metadata",
                "title": "Test Book with Metadata",
                "author": "Test Author",
                "language": "en",
                "page_count": 350,
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["highlights_created"] == 1

        # Verify book was created with language and page_count
        book = (
            db_session.query(models.Book)
            .filter_by(title="Test Book with Metadata", author="Test Author")
            .first()
        )
        assert book is not None
        assert book.language == "en"
        assert book.page_count == 350

    def test_upload_with_keywords_creates_tags(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that uploading with keywords creates corresponding tags."""
        # Create the book with keywords
        create_book_via_api(
            {
                "client_book_id": "test-client-keywords",
                "title": "Test Book with Keywords",
                "author": "Test Author",
                "keywords": ["Fiction", "Science", "Adventure"],
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-keywords",
                "title": "Test Book with Keywords",
                "author": "Test Author",
                "keywords": ["Fiction", "Science", "Adventure"],
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify book was created
        book = (
            db_session.query(models.Book)
            .filter_by(title="Test Book with Keywords", author="Test Author")
            .first()
        )
        assert book is not None

        # Verify tags were created and associated with the book
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Fiction", "Science", "Adventure"}

        # Verify tags exist in the database for user
        tags = db_session.query(models.Tag).filter_by(user_id=book.user_id).all()
        assert len(tags) >= 3
        db_tag_names = {tag.name for tag in tags}
        assert "Fiction" in db_tag_names
        assert "Science" in db_tag_names
        assert "Adventure" in db_tag_names

    def test_upload_keywords_no_duplicates_on_resync(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that resyncing with same keywords doesn't create duplicate tags."""
        # Create the book with keywords
        create_book_via_api(
            {
                "client_book_id": "test-client-dup-keywords",
                "title": "Duplicate Keywords Test Book",
                "author": "Test Author",
                "keywords": ["Tag1", "Tag2"],
            }
        )

        payload = {
            "book": {
                "client_book_id": "test-client-dup-keywords",
                "title": "Duplicate Keywords Test Book",
                "author": "Test Author",
                "keywords": ["Tag1", "Tag2"],
            },
            "highlights": [
                {
                    "text": "Test highlight",
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        # First upload
        response1 = client.post("/api/v1/highlights/upload", json=payload)
        assert response1.status_code == status.HTTP_200_OK

        # Second upload with same keywords
        response2 = client.post("/api/v1/highlights/upload", json=payload)
        assert response2.status_code == status.HTTP_200_OK

        # Verify book has only 2 tags (no duplicates)
        book = (
            db_session.query(models.Book)
            .filter_by(title="Duplicate Keywords Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        assert len(book.tags) == 2
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Tag1", "Tag2"}

        # Verify only 2 tags exist in database for this user
        tags = db_session.query(models.Tag).filter_by(user_id=book.user_id).all()
        tag_counts = {}
        for tag in tags:
            tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1
        # Each tag name should only appear once
        for name in ["Tag1", "Tag2"]:
            assert tag_counts.get(name) == 1

    def test_upload_keywords_only_on_first_upload(
        self, client: TestClient, db_session: Session, create_book_via_api: CreateBookFunc
    ) -> None:
        """Test that keywords are only added on first upload, not subsequent syncs.

        This ensures user's tag edits are preserved across re-syncs from the device.
        """
        # Create the book with initial keywords
        create_book_via_api(
            {
                "client_book_id": "test-client-keywords-first",
                "title": "Keywords First Upload Test Book",
                "author": "Test Author",
                "keywords": ["Original1", "Original2"],
            }
        )

        # First upload with initial keywords - these should be added
        payload1 = {
            "book": {
                "client_book_id": "test-client-keywords-first",
                "title": "Keywords First Upload Test Book",
                "author": "Test Author",
                "keywords": ["Original1", "Original2"],
            },
            "highlights": [
                {
                    "text": "Test highlight 1",
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }
        response1 = client.post("/api/v1/highlights/upload", json=payload1)
        assert response1.status_code == status.HTTP_200_OK

        # Verify initial tags were added
        book = (
            db_session.query(models.Book)
            .filter_by(title="Keywords First Upload Test Book", author="Test Author")
            .first()
        )
        assert book is not None
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Original1", "Original2"}

        # Second upload with different keywords - these should NOT be added
        payload2 = {
            "book": {
                "client_book_id": "test-client-keywords-first",
                "title": "Keywords First Upload Test Book",
                "author": "Test Author",
                "keywords": ["NewTag1", "NewTag2"],  # Different keywords
            },
            "highlights": [
                {
                    "text": "Test highlight 2",
                    "datetime": "2024-01-15 15:30:22",
                },
            ],
        }
        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK

        # Verify book still has only original tags (new keywords not added)
        db_session.refresh(book)
        tag_names = {tag.name for tag in book.tags}
        assert tag_names == {"Original1", "Original2"}

    def test_books_response_includes_language_and_page_count(
        self, client: TestClient, db_session: Session, test_user: models.User
    ) -> None:
        """Test that book list response includes language and page_count fields."""
        # Create a book with language and page_count
        create_test_book(
            db_session,
            user_id=test_user.id,
            title="Book with Metadata",
            author="Test Author",
            language="de",
            page_count=500,
        )

        response = client.get("/api/v1/books/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["books"]) == 1
        book_data = data["books"][0]
        assert book_data["language"] == "de"
        assert book_data["page_count"] == 500

    def test_book_details_includes_language_and_page_count(
        self, client: TestClient, db_session: Session, test_user: models.User
    ) -> None:
        """Test that book details response includes language and page_count fields."""
        # Create a book with language and page_count
        book = create_test_book(
            db_session,
            user_id=test_user.id,
            title="Book Details Metadata Test",
            author="Test Author",
            language="fr",
            page_count=200,
        )

        response = client.get(f"/api/v1/books/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["language"] == "fr"
        assert data["page_count"] == 200
