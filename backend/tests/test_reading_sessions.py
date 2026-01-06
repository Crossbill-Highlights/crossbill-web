"""Tests for reading sessions API endpoints."""

from datetime import UTC, datetime
from typing import NamedTuple

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
from src.utils import compute_reading_session_hash
from tests.conftest import create_test_book

# Default user ID used by services (matches conftest default user)
DEFAULT_USER_ID = 1


# --- NamedTuples for composite fixtures ---


class TwoBooks(NamedTuple):
    book1: models.Book
    book2: models.Book


class BookWithSessions(NamedTuple):
    book: models.Book
    sessions: list[models.ReadingSession]


# --- Fixtures for common test data ---


@pytest.fixture
def test_book(db_session: Session) -> models.Book:
    """Create a test book with default values."""
    return create_test_book(
        db_session=db_session,
        user_id=DEFAULT_USER_ID,
        title="Test Book",
        author="Test Author",
    )


@pytest.fixture
def test_reading_session(db_session: Session, test_book: models.Book) -> models.ReadingSession:
    """Create a test reading session for the test book."""
    return create_reading_session(
        db_session=db_session,
        book=test_book,
        user_id=DEFAULT_USER_ID,
        start_time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
        device_id="test-device-1",
        start_xpoint="/body/div[1]/p[1]",
        end_xpoint="/body/div[1]/p[50]",
    )


@pytest.fixture
def two_books(db_session: Session) -> TwoBooks:
    """Create two test books for bulk upload tests."""
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
    return TwoBooks(book1=book1, book2=book2)


@pytest.fixture
def book_with_sessions(db_session: Session, test_book: models.Book) -> BookWithSessions:
    """Create a test book with multiple reading sessions."""
    session1 = create_reading_session(
        db_session=db_session,
        book=test_book,
        user_id=DEFAULT_USER_ID,
        start_time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
        device_id="device-1",
        start_page=10,
        end_page=15,
    )
    session2 = create_reading_session(
        db_session=db_session,
        book=test_book,
        user_id=DEFAULT_USER_ID,
        start_time=datetime(2024, 1, 16, 10, 0, 0, tzinfo=UTC),
        end_time=datetime(2024, 1, 16, 11, 0, 0, tzinfo=UTC),
        device_id="device-1",
        start_page=16,
        end_page=25,
    )
    return BookWithSessions(book=test_book, sessions=[session1, session2])


def create_reading_session(
    db_session: Session,
    book: models.Book,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    device_id: str | None = None,
    start_xpoint: str | None = None,
    end_xpoint: str | None = None,
    start_page: int | None = None,
    end_page: int | None = None,
) -> models.ReadingSession:
    """Helper function to create a reading session."""
    session_hash = compute_reading_session_hash(
        book_title=book.title,
        book_author=book.author,
        start_time=start_time.isoformat(),
        device_id=device_id,
    )
    session = models.ReadingSession(
        user_id=user_id,
        book_id=book.id,
        start_time=start_time,
        end_time=end_time,
        start_xpoint=start_xpoint,
        end_xpoint=end_xpoint,
        start_page=start_page,
        end_page=end_page,
        device_id=device_id,
        content_hash=session_hash,
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


class TestUploadReadingSessions:
    """Test suite for POST /reading_sessions/upload endpoint."""

    def test_upload_single_session_success(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test successful upload of a single reading session."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "position_type": "xpoint",
                        "start_xpoint": "/body/div[1]/p[1]",
                        "end_xpoint": "/body/div[1]/p[50]",
                        "device_id": "kindle-123",
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify session was created in database with correct values
        session = db_session.query(models.ReadingSession).first()
        assert session is not None
        assert session.book_id == test_book.id
        assert session.device_id == "kindle-123"
        # Compare with timezone-aware datetimes (use replace to normalize for SQLite)
        assert session.start_time.replace(tzinfo=UTC) == datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC)
        assert session.end_time.replace(tzinfo=UTC) == datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC)
        assert session.start_xpoint == "/body/div[1]/p[1]"
        assert session.end_xpoint == "/body/div[1]/p[50]"

    def test_upload_session_skipped_if_book_not_exists(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that sessions for non-existent books are skipped."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": "Non-existent Book",
                        "book_author": "Unknown Author",
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify no book was created
        book = db_session.query(models.Book).filter_by(title="Non-existent Book").first()
        assert book is None

        # Verify no session was created
        sessions = db_session.query(models.ReadingSession).all()
        assert len(sessions) == 0

    def test_upload_session_uses_existing_book(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test that uploading a session uses existing book if it exists."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "start_page": 10,
                        "end_page": 15,
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify session is linked to existing book
        session = db_session.query(models.ReadingSession).first()
        assert session is not None
        assert session.book_id == test_book.id

        # Verify no new book was created
        books = db_session.query(models.Book).filter_by(title=test_book.title).all()
        assert len(books) == 1

    def test_upload_bulk_sessions_success(
        self, client: TestClient, db_session: Session, two_books: TwoBooks
    ) -> None:
        """Test successful bulk upload of multiple sessions for existing books."""
        book1, book2 = two_books

        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": book1.title,
                        "book_author": book1.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "device_id": "device-1",
                        "start_page": 10,
                        "end_page": 15,
                    },
                    {
                        "book_title": book1.title,
                        "book_author": book1.author,
                        "start_time": "2024-01-16T10:00:00Z",
                        "end_time": "2024-01-16T11:00:00Z",
                        "device_id": "device-1",
                        "start_page": 16,
                        "end_page": 20,
                    },
                    {
                        "book_title": book2.title,
                        "book_author": book2.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "device_id": "device-2",
                        "start_page": 1,
                        "end_page": 5,
                    },
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify sessions were created with correct book associations
        book1_sessions = db_session.query(models.ReadingSession).filter_by(book_id=book1.id).all()
        book2_sessions = db_session.query(models.ReadingSession).filter_by(book_id=book2.id).all()
        assert len(book1_sessions) == 2
        assert len(book2_sessions) == 1

        # Verify session details
        assert book2_sessions[0].device_id == "device-2"
        assert book2_sessions[0].start_page == 1
        assert book2_sessions[0].end_page == 5

    def test_upload_mixed_existing_and_missing_books(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test that sessions for existing books are created while missing books are skipped."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "start_page": 10,
                        "end_page": 15,
                    },
                    {
                        "book_title": "Missing Book",
                        "book_author": "Unknown Author",
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "start_page": 10,
                        "end_page": 15,
                    },
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify only the session for the existing book was created
        sessions = db_session.query(models.ReadingSession).all()
        assert len(sessions) == 1
        assert sessions[0].book_id == test_book.id
        assert sessions[0].start_page == 10
        assert sessions[0].end_page == 15

    def test_upload_duplicate_sessions_skipped(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test that duplicate sessions are skipped."""
        session_data = {
            "sessions": [
                {
                    "book_title": test_book.title,
                    "book_author": test_book.author,
                    "start_time": "2024-01-15T10:00:00Z",
                    "end_time": "2024-01-15T11:00:00Z",
                    "device_id": "kindle-123",
                    "start_page": 10,
                    "end_page": 15,
                }
            ]
        }

        # First upload
        response1 = client.post("/api/v1/reading_sessions/upload", json=session_data)
        assert response1.status_code == status.HTTP_200_OK

        # Second upload (duplicate)
        response2 = client.post("/api/v1/reading_sessions/upload", json=session_data)
        assert response2.status_code == status.HTTP_200_OK

        # Verify only one session exists
        sessions = db_session.query(models.ReadingSession).all()
        assert len(sessions) == 1

    def test_upload_same_time_different_device_allowed(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test that same start time from different devices is allowed."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "device_id": "device-1",
                        "start_page": 10,
                        "end_page": 15,
                    },
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "device_id": "device-2",
                        "start_page": 10,
                        "end_page": 15,
                    },
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify both sessions were created with different device IDs
        sessions = db_session.query(models.ReadingSession).all()
        assert len(sessions) == 2
        device_ids = {s.device_id for s in sessions}
        assert device_ids == {"device-1", "device-2"}

    def test_upload_session_with_page_positions(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test uploading a session with page positions (for PDFs)."""
        response = client.post(
            "/api/v1/reading_sessions/upload",
            json={
                "sessions": [
                    {
                        "book_title": test_book.title,
                        "book_author": test_book.author,
                        "start_time": "2024-01-15T10:00:00Z",
                        "end_time": "2024-01-15T11:00:00Z",
                        "position_type": "page",
                        "start_page": 10,
                        "end_page": 25,
                    }
                ]
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify session was created with correct page positions
        session = db_session.query(models.ReadingSession).first()
        assert session is not None
        assert session.book_id == test_book.id
        assert session.start_page == 10
        assert session.end_page == 25
        assert session.start_xpoint is None
        assert session.end_xpoint is None


class TestGetBookReadingSessions:
    """Test suite for GET /books/:id/reading_sessions endpoint."""

    def test_get_sessions_success(
        self, client: TestClient, book_with_sessions: BookWithSessions
    ) -> None:
        """Test successful retrieval of reading sessions for a book."""
        book, sessions = book_with_sessions

        response = client.get(f"/api/v1/books/{book.id}/reading_sessions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) == 2
        assert data["total"] == 2

        # Verify session data matches database records
        returned_ids = {s["id"] for s in data["sessions"]}
        expected_ids = {s.id for s in sessions}
        assert returned_ids == expected_ids

    def test_get_sessions_ordered_by_start_time_desc(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test that sessions are ordered by start_time descending (newest first)."""
        older_session = create_reading_session(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            start_time=datetime(2024, 1, 15, 10, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 15, 11, 0, 0, tzinfo=UTC),
            device_id="device-older",
            start_page=10,
            end_page=15,
        )
        newer_session = create_reading_session(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            start_time=datetime(2024, 1, 17, 10, 0, 0, tzinfo=UTC),
            end_time=datetime(2024, 1, 17, 11, 0, 0, tzinfo=UTC),
            device_id="device-newer",
            start_page=16,
            end_page=25,
        )

        response = client.get(f"/api/v1/books/{test_book.id}/reading_sessions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        sessions = data["sessions"]

        # Newer session should come first
        assert sessions[0]["id"] == newer_session.id
        assert sessions[0]["device_id"] == "device-newer"
        assert sessions[1]["id"] == older_session.id
        assert sessions[1]["device_id"] == "device-older"

    def test_get_sessions_empty(self, client: TestClient, test_book: models.Book) -> None:
        """Test getting sessions when book has none."""
        response = client.get(f"/api/v1/books/{test_book.id}/reading_sessions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sessions"] == []
        assert data["total"] == 0

    def test_get_sessions_book_not_found(self, client: TestClient) -> None:
        """Test getting sessions for non-existent book."""
        response = client.get("/api/v1/books/99999/reading_sessions")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_sessions_pagination(
        self, client: TestClient, db_session: Session, test_book: models.Book
    ) -> None:
        """Test pagination of reading sessions."""
        for i in range(5):
            create_reading_session(
                db_session=db_session,
                book=test_book,
                user_id=DEFAULT_USER_ID,
                start_time=datetime(2024, 1, 15 + i, 10, 0, 0, tzinfo=UTC),
                end_time=datetime(2024, 1, 15 + i, 11, 0, 0, tzinfo=UTC),
                device_id=f"device-{i}",
                start_page=10,
                end_page=15,
            )

        # Get first 2
        response = client.get(f"/api/v1/books/{test_book.id}/reading_sessions?limit=2&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 5

        # Get next 2
        response = client.get(f"/api/v1/books/{test_book.id}/reading_sessions?limit=2&offset=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sessions"]) == 2


class TestReadingSessionCascadeDelete:
    """Test suite for cascade deletion of reading sessions."""

    def test_sessions_deleted_when_book_deleted(
        self,
        client: TestClient,
        db_session: Session,
        test_book: models.Book,
        test_reading_session: models.ReadingSession,
    ) -> None:
        """Test that reading sessions are deleted when book is deleted."""
        session_id = test_reading_session.id

        response = client.delete(f"/api/v1/books/{test_book.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify session was cascade deleted
        deleted_session = db_session.query(models.ReadingSession).filter_by(id=session_id).first()
        assert deleted_session is None
