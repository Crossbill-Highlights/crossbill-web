"""Tests for highlights API endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models


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

    @pytest.mark.skip
    def test_upload_preserves_edited_book_metadata(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that user edits to book metadata are preserved during re-sync.

        When a user edits a book's title/author in the app, subsequent syncs from
        the device should NOT overwrite those edits. The book is identified by
        its content_hash (computed from original title+author), allowing metadata
        to be edited independently.
        """
        # First upload - creates the book with original metadata
        payload1 = {
            "book": {
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
        book.title = "User Edited Title"
        book.author = "User Edited Author"
        book.isbn = "9999999999"
        db_session.commit()

        # Second upload from device with original metadata (same hash)
        # This should NOT overwrite the user's edits
        payload2 = {
            "book": {
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

    def test_upload_same_text_different_datetime_is_duplicate(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that same text at different times is considered duplicate (hash-based dedup).

        With hash-based deduplication, the hash is computed from text + book_title + author.
        Datetime is NOT part of the hash, so same text in the same book is a duplicate.
        """
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
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that same text in different books creates separate highlights.

        The hash includes book_title and author, so same text in different books
        will have different hashes and create separate highlights.
        """
        # First book
        payload1 = {
            "book": {
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

        # Second book with same text
        payload2 = {
            "book": {
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

    def test_highlight_has_content_hash(self, client: TestClient, db_session: Session) -> None:
        """Test that created highlights have a content_hash field populated."""
        payload = {
            "book": {
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

    def test_upload_with_duplicates_and_new_chapters(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that duplicate highlights don't cause rollback of chapter creation.

        This is a regression test for a bug where:
        1. Chapters are created and flushed
        2. Highlights are created, some are duplicates causing IntegrityError
        3. The rollback from duplicate detection rolled back chapter creation
        4. Subsequent highlights failed due to missing chapter foreign keys
        """
        # First upload with some highlights in Chapter 1
        payload1 = {
            "book": {
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

        # Second upload with mix of duplicates and new highlights in new chapters
        # This tests that when a duplicate is encountered, it doesn't roll back
        # the creation of new chapters for subsequent highlights
        payload2 = {
            "book": {
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
                    "text": "New highlight in Chapter 2",  # New chapter
                    "chapter": "Chapter 2",
                    "datetime": "2024-01-15 15:00:00",
                },
                {
                    "text": "Second highlight in Chapter 1",  # Duplicate
                    "chapter": "Chapter 1",
                    "datetime": "2024-01-15 14:30:00",
                },
                {
                    "text": "Another new highlight in Chapter 3",  # New chapter
                    "chapter": "Chapter 3",
                    "datetime": "2024-01-15 16:00:00",
                },
            ],
        }

        response2 = client.post("/api/v1/highlights/upload", json=payload2)
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert data2["highlights_created"] == 2  # Chapter 2 and Chapter 3 highlights
        assert data2["highlights_skipped"] == 2  # Both duplicates

        # Verify all chapters were created correctly
        book = (
            db_session.query(models.Book)
            .filter_by(title="Rollback Bug Test Book", author="Test Author")
            .first()
        )
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 3
        chapter_names = {c.name for c in chapters}
        assert chapter_names == {"Chapter 1", "Chapter 2", "Chapter 3"}

        # Verify all 4 highlights exist (2 from first upload, 2 new from second)
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 4

        # Verify highlights are correctly associated with chapters
        chapter_map = {c.name: c.id for c in chapters}
        highlight_texts = {h.text: h.chapter_id for h in highlights}
        assert highlight_texts["First highlight in Chapter 1"] == chapter_map["Chapter 1"]
        assert highlight_texts["Second highlight in Chapter 1"] == chapter_map["Chapter 1"]
        assert highlight_texts["New highlight in Chapter 2"] == chapter_map["Chapter 2"]
        assert highlight_texts["Another new highlight in Chapter 3"] == chapter_map["Chapter 3"]
