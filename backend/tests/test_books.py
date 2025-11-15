"""Tests for books API endpoints."""

import json
from datetime import UTC, datetime

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from crossbill import models


class TestDeleteBook:
    """Test suite for DELETE /book/:id endpoint."""

    def test_delete_book_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful deletion of a book."""
        # Create a book with chapters and highlights
        book = models.Book(title="Test Book", author="Test Author", isbn="1234567890")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        chapter = models.Chapter(book_id=book.id, name="Chapter 1")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        highlight = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()

        # Delete the book
        response = client.delete(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify book was deleted (cascade delete should handle chapters and highlights)
        deleted_book = db_session.query(models.Book).filter_by(id=book.id).first()
        assert deleted_book is None

        # Verify chapters were deleted
        chapters = db_session.query(models.Chapter).filter_by(book_id=book.id).all()
        assert len(chapters) == 0

        # Verify highlights were deleted
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 0

    def test_delete_book_not_found(self, client: TestClient, db_session: Session) -> None:
        """Test deletion of non-existent book."""
        response = client.delete("/api/v1/book/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["message"].lower()
        assert data["book_id"] == 99999

    def test_delete_book_empty_database(self, client: TestClient, db_session: Session) -> None:
        """Test deletion when database is empty."""
        response = client.delete("/api/v1/book/1")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteHighlights:
    """Test suite for DELETE /book/:id/highlight endpoint."""

    def test_delete_highlights_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful soft deletion of highlights."""
        # Create a book with highlights
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight1 = models.Highlight(
            book_id=book.id,
            text="Highlight 1",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        highlight2 = models.Highlight(
            book_id=book.id,
            text="Highlight 2",
            page=20,
            datetime="2024-01-15 15:00:00",
        )
        db_session.add_all([highlight1, highlight2])
        db_session.commit()
        db_session.refresh(highlight1)
        db_session.refresh(highlight2)

        # Delete highlights
        payload = {"highlight_ids": [highlight1.id, highlight2.id]}
        response = client.request(
            "DELETE", f"/api/v1/book/{book.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2
        assert "Successfully deleted 2 highlight(s)" in data["message"]

        # Verify highlights were soft-deleted
        db_session.refresh(highlight1)
        db_session.refresh(highlight2)
        assert highlight1.deleted_at is not None
        assert highlight2.deleted_at is not None

    def test_delete_highlights_partial(self, client: TestClient, db_session: Session) -> None:
        """Test deletion of subset of highlights."""
        # Create a book with highlights
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight1 = models.Highlight(
            book_id=book.id,
            text="Highlight 1",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        highlight2 = models.Highlight(
            book_id=book.id,
            text="Highlight 2",
            page=20,
            datetime="2024-01-15 15:00:00",
        )
        db_session.add_all([highlight1, highlight2])
        db_session.commit()
        db_session.refresh(highlight1)
        db_session.refresh(highlight2)

        # Delete only first highlight
        payload = {"highlight_ids": [highlight1.id]}
        response = client.request(
            "DELETE", f"/api/v1/book/{book.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 1

        # Verify only first highlight was soft-deleted
        db_session.refresh(highlight1)
        db_session.refresh(highlight2)
        assert highlight1.deleted_at is not None
        assert highlight2.deleted_at is None

    def test_delete_highlights_already_deleted(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test deletion of already soft-deleted highlights."""
        # Create a book with highlights
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Create a highlight and soft-delete it
        highlight = models.Highlight(
            book_id=book.id,
            text="Deleted Highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
            deleted_at=datetime.now(UTC),
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        # Try to delete it again
        payload = {"highlight_ids": [highlight.id]}
        response = client.request(
            "DELETE", f"/api/v1/book/{book.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0  # Should not count already deleted highlights

    def test_delete_highlights_wrong_book(self, client: TestClient, db_session: Session) -> None:
        """Test deletion of highlights with wrong book ID."""
        # Create two books with highlights
        book1 = models.Book(title="Book 1", author="Author 1")
        book2 = models.Book(title="Book 2", author="Author 2")
        db_session.add_all([book1, book2])
        db_session.commit()
        db_session.refresh(book1)
        db_session.refresh(book2)

        highlight1 = models.Highlight(
            book_id=book1.id,
            text="Highlight from Book 1",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight1)
        db_session.commit()
        db_session.refresh(highlight1)

        # Try to delete book1's highlight using book2's ID
        payload = {"highlight_ids": [highlight1.id]}
        response = client.request(
            "DELETE", f"/api/v1/book/{book2.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0  # Should not delete highlights from different book

        # Verify highlight was not deleted
        db_session.refresh(highlight1)
        assert highlight1.deleted_at is None

    def test_delete_highlights_book_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test deletion of highlights for non-existent book."""
        payload = {"highlight_ids": [1, 2, 3]}
        response = client.request(
            "DELETE", "/api/v1/book/99999/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["message"].lower()
        assert data["book_id"] == 99999

    def test_delete_highlights_empty_list(self, client: TestClient, db_session: Session) -> None:
        """Test deletion with empty highlight list."""
        # Create a book
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to delete with empty list
        payload = {"highlight_ids": []}
        response = client.request(
            "DELETE", f"/api/v1/book/{book.id}/highlight", content=json.dumps(payload)
        )

        # Should fail validation because of min_length=1
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestHighlightSyncWithSoftDelete:
    """Test suite for highlight sync with soft-deleted highlights."""

    def test_sync_skips_soft_deleted_highlights(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that sync does not recreate soft-deleted highlights."""
        # Create a book with a highlight and soft-delete it
        book = models.Book(title="Test Book", author="Test Author", isbn="1234567890")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Deleted Highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
            deleted_at=datetime.now(UTC),
        )
        db_session.add(highlight)
        db_session.commit()

        # Try to sync the same highlight again
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
                "isbn": "1234567890",
            },
            "highlights": [
                {
                    "text": "Deleted Highlight",
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 0
        assert data["highlights_skipped"] == 1  # Should skip the soft-deleted highlight

        # Verify no new highlight was created (still only one, the soft-deleted one)
        highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(highlights) == 1
        assert highlights[0].deleted_at is not None

    def test_sync_creates_new_highlights_skips_deleted(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that sync creates new highlights but skips deleted ones."""
        # Create a book with a soft-deleted highlight
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        deleted_highlight = models.Highlight(
            book_id=book.id,
            text="Deleted Highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
            deleted_at=datetime.now(UTC),
        )
        db_session.add(deleted_highlight)
        db_session.commit()

        # Sync with the deleted highlight and a new one
        payload = {
            "book": {
                "title": "Test Book",
                "author": "Test Author",
            },
            "highlights": [
                {
                    "text": "Deleted Highlight",  # Should be skipped
                    "page": 10,
                    "datetime": "2024-01-15 14:30:22",
                },
                {
                    "text": "New Highlight",  # Should be created
                    "page": 20,
                    "datetime": "2024-01-15 15:00:00",
                },
            ],
        }

        response = client.post("/api/v1/highlights/upload", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["highlights_created"] == 1
        assert data["highlights_skipped"] == 1

        # Verify we have 2 highlights: 1 deleted, 1 active
        all_highlights = db_session.query(models.Highlight).filter_by(book_id=book.id).all()
        assert len(all_highlights) == 2

        active_highlights = [h for h in all_highlights if h.deleted_at is None]
        deleted_highlights = [h for h in all_highlights if h.deleted_at is not None]

        assert len(active_highlights) == 1
        assert active_highlights[0].text == "New Highlight"
        assert len(deleted_highlights) == 1
        assert deleted_highlights[0].text == "Deleted Highlight"


class TestGetBookDetails:
    """Test suite for GET /book/:id endpoint to verify soft-delete filtering."""

    def test_get_book_details_excludes_deleted_highlights(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that book details endpoint excludes soft-deleted highlights."""
        # Create a book with both active and deleted highlights
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        chapter = models.Chapter(book_id=book.id, name="Chapter 1")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        active_highlight = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Active Highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        deleted_highlight = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Deleted Highlight",
            page=20,
            datetime="2024-01-15 15:00:00",
            deleted_at=datetime.now(UTC),
        )
        db_session.add_all([active_highlight, deleted_highlight])
        db_session.commit()

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify only active highlight is returned
        assert len(data["chapters"]) == 1
        assert len(data["chapters"][0]["highlights"]) == 1
        assert data["chapters"][0]["highlights"][0]["text"] == "Active Highlight"
