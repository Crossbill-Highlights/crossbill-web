"""Tests for highlights API endpoints."""

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from inkwell import models


class TestHighlightsUpload:
    """Test suite for highlights upload endpoint."""

    def test_upload_highlights_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful upload of highlights."""
        payload = {
            "book": {
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

        # Verify chapters were created
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 2
        chapter_names = {c.name for c in chapters}
        assert chapter_names == {"Chapter 1", "Chapter 2"}

    def test_upload_highlights_without_chapter(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test uploading highlights without chapter information."""
        payload = {
            "book": {
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
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify highlight was created without chapter_id
        highlight = db_session.query(models.Highlight).filter_by(book_id=book.id).first()
        assert highlight is not None
        assert highlight.chapter_id is None

    def test_upload_duplicate_highlights(self, client: TestClient, db_session: Session) -> None:
        """Test that duplicate highlights are properly skipped."""
        payload = {
            "book": {
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
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 1

    def test_upload_partial_duplicates(self, client: TestClient, db_session: Session) -> None:
        """Test uploading mix of new and duplicate highlights."""
        # First upload
        payload1 = {
            "book": {
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

    def test_upload_updates_book_metadata(self, client: TestClient, db_session: Session) -> None:
        """Test that uploading to existing book updates its metadata."""
        # First upload
        payload1 = {
            "book": {
                "title": "Update Test Book",
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

        # Second upload with updated metadata (same title and author means same book)
        payload2 = {
            "book": {
                "title": "Update Test Book",
                "author": "Original Author",
                "isbn": "2222222222",  # Updated ISBN
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
        assert response2.json()["book_id"] == book_id  # Same book

        # Verify book metadata was updated
        book = db_session.query(models.Book).filter_by(id=book_id).first()
        assert book.title == "Update Test Book"
        assert book.author == "Original Author"
        assert book.isbn == "2222222222"

        # Verify both highlights exist
        highlights = db_session.query(models.Highlight).filter_by(book_id=book_id).all()
        assert len(highlights) == 2

    def test_upload_empty_highlights_list(self, client: TestClient) -> None:
        """Test uploading with empty highlights list."""
        payload = {
            "book": {
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

    def test_upload_same_text_different_datetime(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that same text at different times creates separate highlights."""
        payload = {
            "book": {
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
                    "datetime": "2024-01-15 15:00:00",  # Different datetime
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 2  # Both should be created
        assert data["highlights_skipped"] == 0

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

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_invalid_payload_missing_required_fields(self, client: TestClient) -> None:
        """Test upload with missing required fields."""
        payload = {
            "book": {
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

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upload_creates_chapter_only_once(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that multiple highlights in same chapter only create one chapter."""
        payload = {
            "book": {
                "title": "Chapter Dedup Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Highlight 1 in Chapter 1",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:00:00",
                },
                {
                    "text": "Highlight 2 in Chapter 1",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 15:00:00",
                },
                {
                    "text": "Highlight 3 in Chapter 1",
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 16:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 3

        # Verify only one chapter was created
        book = (
            db_session.query(models.Book)
            .filter_by(title="Chapter Dedup Test Book", author="Test Author")
            .first()
        )
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 1
        assert chapters[0].name == "Chapter 1"

        # Verify all highlights are associated with the same chapter
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 3
        assert all(h.chapter_id == chapters[0].id for h in highlights)
