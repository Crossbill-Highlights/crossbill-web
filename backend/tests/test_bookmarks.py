"""Tests for bookmarks API endpoints."""

import json

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models


class TestCreateBookmark:
    """Test suite for POST /book/:id/bookmark endpoint."""

    def test_create_bookmark_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful creation of a bookmark."""
        # Create a book with a highlight
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        # Create a bookmark
        response = client.post(
            f"/api/v1/book/{book.id}/bookmark",
            json={"highlight_id": highlight.id},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["book_id"] == book.id
        assert data["highlight_id"] == highlight.id
        assert "id" in data
        assert "created_at" in data

        # Verify bookmark was created in database
        bookmark = db_session.query(models.Bookmark).filter_by(id=data["id"]).first()
        assert bookmark is not None
        assert bookmark.book_id == book.id
        assert bookmark.highlight_id == highlight.id

    def test_create_bookmark_duplicate(self, client: TestClient, db_session: Session) -> None:
        """Test creating a duplicate bookmark returns existing bookmark."""
        # Create a book with a highlight
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        # Create first bookmark
        response1 = client.post(
            f"/api/v1/book/{book.id}/bookmark",
            json={"highlight_id": highlight.id},
        )
        assert response1.status_code == status.HTTP_201_CREATED
        data1 = response1.json()

        # Try to create duplicate bookmark
        response2 = client.post(
            f"/api/v1/book/{book.id}/bookmark",
            json={"highlight_id": highlight.id},
        )
        assert response2.status_code == status.HTTP_201_CREATED
        data2 = response2.json()

        # Should return the same bookmark
        assert data1["id"] == data2["id"]

        # Verify only one bookmark exists
        bookmarks = db_session.query(models.Bookmark).filter_by(book_id=book.id).all()
        assert len(bookmarks) == 1

    def test_create_bookmark_book_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test creating a bookmark for non-existent book."""
        response = client.post(
            "/api/v1/book/99999/bookmark",
            json={"highlight_id": 1},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_bookmark_highlight_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test creating a bookmark for non-existent highlight."""
        # Create a book
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        response = client.post(
            f"/api/v1/book/{book.id}/bookmark",
            json={"highlight_id": 99999},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_bookmark_highlight_belongs_to_different_book(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test creating a bookmark for a highlight that belongs to a different book."""
        # Create two books
        book1 = models.Book(title="Test Book 1", author="Test Author")
        book2 = models.Book(title="Test Book 2", author="Test Author")
        db_session.add_all([book1, book2])
        db_session.commit()
        db_session.refresh(book1)
        db_session.refresh(book2)

        # Create highlight for book2
        highlight = models.Highlight(
            book_id=book2.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        # Try to create bookmark for book1 with highlight from book2
        response = client.post(
            f"/api/v1/book/{book1.id}/bookmark",
            json={"highlight_id": highlight.id},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteBookmark:
    """Test suite for DELETE /book/:id/bookmark/:bookmark_id endpoint."""

    def test_delete_bookmark_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful deletion of a bookmark."""
        # Create a book with a highlight and bookmark
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        bookmark = models.Bookmark(book_id=book.id, highlight_id=highlight.id)
        db_session.add(bookmark)
        db_session.commit()
        db_session.refresh(bookmark)

        # Delete the bookmark
        response = client.delete(f"/api/v1/book/{book.id}/bookmark/{bookmark.id}")

        assert response.status_code == status.HTTP_200_OK

        # Verify bookmark was deleted
        deleted_bookmark = (
            db_session.query(models.Bookmark).filter_by(id=bookmark.id).first()
        )
        assert deleted_bookmark is None

    def test_delete_bookmark_idempotent(self, client: TestClient, db_session: Session) -> None:
        """Test that deleting a non-existent bookmark is idempotent (returns 200)."""
        # Create a book
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Try to delete non-existent bookmark
        response = client.delete(f"/api/v1/book/{book.id}/bookmark/99999")

        # Should succeed (idempotent operation)
        assert response.status_code == status.HTTP_200_OK

    def test_delete_bookmark_book_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test deleting a bookmark for non-existent book."""
        response = client.delete("/api/v1/book/99999/bookmark/1")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetBookmarks:
    """Test suite for GET /book/:id/bookmarks endpoint."""

    def test_get_bookmarks_success(self, client: TestClient, db_session: Session) -> None:
        """Test successful retrieval of bookmarks."""
        # Create a book with highlights and bookmarks
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

        bookmark1 = models.Bookmark(book_id=book.id, highlight_id=highlight1.id)
        bookmark2 = models.Bookmark(book_id=book.id, highlight_id=highlight2.id)
        db_session.add_all([bookmark1, bookmark2])
        db_session.commit()

        # Get bookmarks
        response = client.get(f"/api/v1/book/{book.id}/bookmarks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 2

        # Verify bookmark data
        bookmark_ids = {b["id"] for b in data["bookmarks"]}
        assert bookmark1.id in bookmark_ids
        assert bookmark2.id in bookmark_ids

    def test_get_bookmarks_empty(self, client: TestClient, db_session: Session) -> None:
        """Test getting bookmarks when book has none."""
        # Create a book with no bookmarks
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        response = client.get(f"/api/v1/book/{book.id}/bookmarks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 0

    def test_get_bookmarks_book_not_found(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test getting bookmarks for non-existent book."""
        response = client.get("/api/v1/book/99999/bookmarks")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBookDetailsWithBookmarks:
    """Test suite for bookmarks in book details endpoint."""

    def test_book_details_includes_bookmarks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that GET /book/:id includes bookmarks in the response."""
        # Create a book with highlights and bookmarks
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        chapter = models.Chapter(book_id=book.id, name="Chapter 1")
        db_session.add(chapter)
        db_session.commit()
        db_session.refresh(chapter)

        highlight1 = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Highlight 1",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        highlight2 = models.Highlight(
            book_id=book.id,
            chapter_id=chapter.id,
            text="Highlight 2",
            page=20,
            datetime="2024-01-15 15:00:00",
        )
        db_session.add_all([highlight1, highlight2])
        db_session.commit()
        db_session.refresh(highlight1)
        db_session.refresh(highlight2)

        # Create bookmarks for both highlights
        bookmark1 = models.Bookmark(book_id=book.id, highlight_id=highlight1.id)
        bookmark2 = models.Bookmark(book_id=book.id, highlight_id=highlight2.id)
        db_session.add_all([bookmark1, bookmark2])
        db_session.commit()
        db_session.refresh(bookmark1)
        db_session.refresh(bookmark2)

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify bookmarks are included
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 2

        # Verify bookmark data
        bookmark_ids = {b["id"] for b in data["bookmarks"]}
        assert bookmark1.id in bookmark_ids
        assert bookmark2.id in bookmark_ids

        # Verify bookmark details
        for bookmark in data["bookmarks"]:
            assert "id" in bookmark
            assert "book_id" in bookmark
            assert "highlight_id" in bookmark
            assert "created_at" in bookmark
            assert bookmark["book_id"] == book.id

    def test_book_details_empty_bookmarks(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that GET /book/:id returns empty bookmarks list when no bookmarks exist."""
        # Create a book without bookmarks
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        # Get book details
        response = client.get(f"/api/v1/book/{book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify bookmarks field exists but is empty
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 0


class TestBookmarkCascadeDelete:
    """Test suite for cascade deletion of bookmarks."""

    def test_bookmark_deleted_when_book_deleted(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that bookmarks are deleted when book is deleted."""
        # Create a book with a highlight and bookmark
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        bookmark = models.Bookmark(book_id=book.id, highlight_id=highlight.id)
        db_session.add(bookmark)
        db_session.commit()
        db_session.refresh(bookmark)

        bookmark_id = bookmark.id

        # Delete the book
        response = client.delete(f"/api/v1/book/{book.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify bookmark was cascade deleted
        deleted_bookmark = (
            db_session.query(models.Bookmark).filter_by(id=bookmark_id).first()
        )
        assert deleted_bookmark is None

    def test_bookmark_deleted_when_highlight_deleted(
        self, client: TestClient, db_session: Session
    ) -> None:
        """Test that bookmarks are deleted when highlight is deleted."""
        # Create a book with a highlight and bookmark
        book = models.Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        highlight = models.Highlight(
            book_id=book.id,
            text="Test highlight",
            page=10,
            datetime="2024-01-15 14:30:22",
        )
        db_session.add(highlight)
        db_session.commit()
        db_session.refresh(highlight)

        bookmark = models.Bookmark(book_id=book.id, highlight_id=highlight.id)
        db_session.add(bookmark)
        db_session.commit()
        db_session.refresh(bookmark)

        bookmark_id = bookmark.id

        # Soft delete the highlight
        payload = {"highlight_ids": [highlight.id]}
        response = client.request(
            "DELETE", f"/api/v1/book/{book.id}/highlight", content=json.dumps(payload)
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify bookmark was deleted when highlight was soft deleted
        deleted_bookmark = (
            db_session.query(models.Bookmark).filter_by(id=bookmark_id).first()
        )
        assert deleted_bookmark is None
