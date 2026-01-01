"""Tests for books API endpoints."""

import json
from datetime import UTC, datetime
from typing import NamedTuple

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
from tests.conftest import create_test_book, create_test_highlight

# Default user ID used by services (matches conftest default user)
DEFAULT_USER_ID = 1


class BookWithChapter(NamedTuple):
    book: models.Book
    chapter: models.Chapter


class BookWithHighlights(NamedTuple):
    book: models.Book
    highlights: list[models.Highlight]


class BookWithChapterAndHighlights(NamedTuple):
    book: models.Book
    chapter: models.Chapter
    highlights: list[models.Highlight]


@pytest.fixture
def test_book(db_session: Session) -> models.Book:
    return create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
    )


@pytest.fixture
def test_book_with_isbn(db_session: Session) -> models.Book:
    return create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
    )


@pytest.fixture
def book_with_chapter(db_session: Session) -> BookWithChapter:
    book = create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
    )
    chapter = models.Chapter(book_id=book.id, name="Chapter 1")
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return BookWithChapter(book=book, chapter=chapter)


@pytest.fixture
def book_with_highlights(db_session: Session) -> BookWithHighlights:
    book = create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
    )
    highlight1 = create_test_highlight(
        db_session=db_session,
        book=book,
        user_id=DEFAULT_USER_ID,
        text="Highlight 1",
        page=10,
        datetime_str="2024-01-15 14:30:22",
    )
    highlight2 = create_test_highlight(
        db_session=db_session,
        book=book,
        user_id=DEFAULT_USER_ID,
        text="Highlight 2",
        page=20,
        datetime_str="2024-01-15 15:00:00",
    )
    return BookWithHighlights(book=book, highlights=[highlight1, highlight2])


@pytest.fixture
def book_with_chapter_and_highlight(db_session: Session) -> BookWithChapterAndHighlights:
    book = create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
    )
    chapter = models.Chapter(book_id=book.id, name="Chapter 1")
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)

    highlight = create_test_highlight(
        db_session=db_session,
        book=book,
        user_id=DEFAULT_USER_ID,
        chapter_id=chapter.id,
        text="Test highlight",
        page=10,
        datetime_str="2024-01-15 14:30:22",
    )
    return BookWithChapterAndHighlights(book=book, chapter=chapter, highlights=[highlight])


@pytest.fixture
def book_with_soft_deleted_highlight(db_session: Session) -> BookWithHighlights:
    book = create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
        isbn="1234567890",
    )
    highlight = create_test_highlight(
        db_session=db_session,
        book=book,
        user_id=DEFAULT_USER_ID,
        text="Deleted Highlight",
        page=10,
        datetime_str="2024-01-15 14:30:22",
        deleted_at=datetime.now(UTC),
    )
    return BookWithHighlights(book=book, highlights=[highlight])


class TestDeleteBook:
    """Test suite for DELETE /books/:id endpoint."""

    def test_delete_book_success(
        self,
        client: TestClient,
        db_session: Session,
        book_with_chapter_and_highlight: BookWithChapterAndHighlights,
    ) -> None:
        """Test successful deletion of a book."""
        book = book_with_chapter_and_highlight.book

        response = client.delete(f"/api/v1/books/{book.id}")

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

    def test_delete_book_not_found(self, client: TestClient) -> None:
        """Test deletion of non-existent book."""
        response = client.delete("/api/v1/books/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["message"].lower()
        assert data["book_id"] == 99999

    def test_delete_book_empty_database(self, client: TestClient) -> None:
        """Test deletion when database is empty."""
        response = client.delete("/api/v1/books/1")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteHighlights:
    """Test suite for DELETE /books/:id/highlight endpoint."""

    def test_delete_highlights_success(
        self,
        client: TestClient,
        db_session: Session,
        book_with_highlights: BookWithHighlights,
    ) -> None:
        """Test successful soft deletion of highlights."""
        book = book_with_highlights.book
        highlight1, highlight2 = book_with_highlights.highlights

        payload = {"highlight_ids": [highlight1.id, highlight2.id]}
        response = client.request(
            "DELETE", f"/api/v1/books/{book.id}/highlight", content=json.dumps(payload)
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

    def test_delete_highlights_partial(
        self,
        client: TestClient,
        db_session: Session,
        book_with_highlights: BookWithHighlights,
    ) -> None:
        """Test deletion of subset of highlights."""
        book = book_with_highlights.book
        highlight1, highlight2 = book_with_highlights.highlights

        payload = {"highlight_ids": [highlight1.id]}
        response = client.request(
            "DELETE", f"/api/v1/books/{book.id}/highlight", content=json.dumps(payload)
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
        self,
        client: TestClient,
        book_with_soft_deleted_highlight: BookWithHighlights,
    ) -> None:
        """Test deletion of already soft-deleted highlights."""
        book = book_with_soft_deleted_highlight.book
        highlight = book_with_soft_deleted_highlight.highlights[0]

        payload = {"highlight_ids": [highlight.id]}
        response = client.request(
            "DELETE", f"/api/v1/books/{book.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0  # Should not count already deleted highlights

    def test_delete_highlights_wrong_book(self, client: TestClient, db_session: Session) -> None:
        """Test deletion of highlights with wrong book ID."""
        # Create two books - this test needs specific setup for cross-book verification
        book1 = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Book 1",
            author="Author 1",
        )
        book2 = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Book 2",
            author="Author 2",
        )

        highlight1 = create_test_highlight(
            db_session=db_session,
            book=book1,
            user_id=DEFAULT_USER_ID,
            text="Highlight from Book 1",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )

        # Try to delete book1's highlight using book2's ID
        payload = {"highlight_ids": [highlight1.id]}
        response = client.request(
            "DELETE", f"/api/v1/books/{book2.id}/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["deleted_count"] == 0  # Should not delete highlights from different book

        # Verify highlight was not deleted
        db_session.refresh(highlight1)
        assert highlight1.deleted_at is None

    def test_delete_highlights_book_not_found(self, client: TestClient) -> None:
        """Test deletion of highlights for non-existent book."""
        payload = {"highlight_ids": [1, 2, 3]}
        response = client.request(
            "DELETE", "/api/v1/books/99999/highlight", content=json.dumps(payload)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["message"].lower()
        assert data["book_id"] == 99999

    def test_delete_highlights_empty_list(self, client: TestClient, test_book: models.Book) -> None:
        """Test deletion with empty highlight list."""
        payload = {"highlight_ids": []}
        response = client.request(
            "DELETE", f"/api/v1/books/{test_book.id}/highlight", content=json.dumps(payload)
        )

        # Should fail validation because of min_length=1
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestHighlightSyncWithSoftDelete:
    """Test suite for highlight sync with soft-deleted highlights."""

    def test_sync_skips_soft_deleted_highlights(
        self,
        client: TestClient,
        db_session: Session,
        book_with_soft_deleted_highlight: BookWithHighlights,
    ) -> None:
        """Test that sync does not recreate soft-deleted highlights."""
        book = book_with_soft_deleted_highlight.book

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
        # This test needs specific book without ISBN to test author-based matching
        book = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Test Book",
            author="Test Author",
        )

        create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            text="Deleted Highlight",
            page=10,
            datetime_str="2024-01-15 14:30:22",
            deleted_at=datetime.now(UTC),
        )

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
    """Test suite for GET /books/:id endpoint to verify soft-delete filtering."""

    def test_get_book_details_excludes_deleted_highlights(
        self,
        client: TestClient,
        db_session: Session,
        book_with_chapter: BookWithChapter,
    ) -> None:
        """Test that book details endpoint excludes soft-deleted highlights."""
        book, chapter = book_with_chapter

        # Add active and deleted highlights to the chapter
        create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            chapter_id=chapter.id,
            text="Active Highlight",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )
        create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            chapter_id=chapter.id,
            text="Deleted Highlight",
            page=20,
            datetime_str="2024-01-15 15:00:00",
            deleted_at=datetime.now(UTC),
        )

        response = client.get(f"/api/v1/books/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify only active highlight is returned
        assert len(data["chapters"]) == 1
        assert len(data["chapters"][0]["highlights"]) == 1
        assert data["chapters"][0]["highlights"][0]["text"] == "Active Highlight"

    def test_get_book_details_includes_highlight_tags(
        self,
        client: TestClient,
        db_session: Session,
        book_with_chapter: BookWithChapter,
    ) -> None:
        """Test that book details endpoint includes highlight tags for each highlight."""
        book, chapter = book_with_chapter

        highlight = create_test_highlight(
            db_session=db_session,
            book=book,
            user_id=DEFAULT_USER_ID,
            chapter_id=chapter.id,
            text="Test Highlight",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )

        # Create highlight tags for the book
        tag1 = models.HighlightTag(book_id=book.id, user_id=DEFAULT_USER_ID, name="Important")
        tag2 = models.HighlightTag(book_id=book.id, user_id=DEFAULT_USER_ID, name="Review")
        db_session.add_all([tag1, tag2])
        db_session.commit()
        db_session.refresh(tag1)
        db_session.refresh(tag2)

        # Associate tags with the highlight
        highlight.highlight_tags.append(tag1)
        highlight.highlight_tags.append(tag2)
        db_session.commit()

        response = client.get(f"/api/v1/books/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify highlight tags are returned
        assert len(data["chapters"]) == 1
        assert len(data["chapters"][0]["highlights"]) == 1

        highlight_data = data["chapters"][0]["highlights"][0]
        assert "highlight_tags" in highlight_data
        assert len(highlight_data["highlight_tags"]) == 2

        tag_names = [tag["name"] for tag in highlight_data["highlight_tags"]]
        assert "Important" in tag_names
        assert "Review" in tag_names


class TestGetBooksWithFlashcardFilter:
    @pytest.fixture
    def books_with_flashcards(self, db_session: Session) -> None:
        """Create test books: one with flashcards, one without."""
        book_with = create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Book with Flashcards",
            author="Author 1",
        )
        create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Book without Flashcards",
            author="Author 2",
        )

        # Add flashcard to first book
        flashcard = models.Flashcard(
            user_id=DEFAULT_USER_ID,
            book_id=book_with.id,
            question="Test question?",
            answer="Test answer",
        )
        db_session.add(flashcard)
        db_session.commit()

    def test_get_books_without_filter_returns_all(
        self, client: TestClient, books_with_flashcards: None
    ) -> None:
        """Test that without filter, all books are returned."""
        response = client.get("/api/v1/books/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert len(data["books"]) == 2

    def test_get_books_with_flashcard_filter_returns_only_books_with_flashcards(
        self, client: TestClient, books_with_flashcards: None
    ) -> None:
        """Test that only_with_flashcards=true returns only books with flashcards."""
        response = client.get("/api/v1/books/?only_with_flashcards=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["books"]) == 1
        assert data["books"][0]["title"] == "Book with Flashcards"
        assert data["books"][0]["flashcard_count"] == 1
