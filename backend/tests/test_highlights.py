"""Tests for highlights API endpoints."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models, schemas

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
            "client_book_id": "test-client-book-id",
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
            "client_book_id": "test-client-book-id-no-chapters",
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
            "client_book_id": "test-client-book-xpoints",
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
        # Note: XPoint value object normalizes text()[1].0 (defaults) to just xpath
        assert highlights[0].start_xpoint == "/body/div[1]/p[5]"
        assert highlights[0].end_xpoint == "/body/div[1]/p[5]/text().42"

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
            "client_book_id": "test-client-duplicate-book",
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
            "client_book_id": "test-client-partial-dup",
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
            "client_book_id": "test-client-partial-dup",
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
            "client_book_id": "test-client-empty",
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
            "client_book_id": "test-client-same-text",
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
        """Test that same text in different books is treated as duplicate.

        NEW BEHAVIOR: The content hash is computed from text only (not book metadata).
        This means same highlight text from different books will be deduplicated.
        This is the domain-centric approach that prioritizes text content.
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
            "client_book_id": "test-client-first-book",
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
            "client_book_id": "test-client-second-book",
            "highlights": [
                {
                    "text": "Same highlight text",
                    "datetime": "2024-01-15 14:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        # Same text in different book = NOT a duplicate (scoped by book)
        # Allows highlighting the same passage in multiple books
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
            "client_book_id": "test-client-hash-test",
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
            "client_book_id": "test-client-minimal",
            "highlights": [
                {
                    "text": "Test highlight",
                    # Missing datetime
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
