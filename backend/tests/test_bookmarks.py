"""Tests for bookmarks API endpoints."""

import json

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models
from tests.conftest import create_test_book, create_test_highlight

# Default user ID used by services (matches conftest default user)
DEFAULT_USER_ID = 1


# --- Fixtures for common test data ---


@pytest.fixture
async def test_highlight(db_session: AsyncSession, test_book: models.Book) -> models.Highlight:
    """Create a test highlight for the test book."""
    return await create_test_highlight(
        db_session=db_session,
        book=test_book,
        user_id=DEFAULT_USER_ID,
        text="Test highlight",
        page=10,
        datetime_str="2024-01-15 14:30:22",
    )


@pytest.fixture
async def test_bookmark(
    db_session: AsyncSession, test_book: models.Book, test_highlight: models.Highlight
) -> models.Bookmark:
    """Create a test bookmark linking the test book and highlight."""
    bookmark = models.Bookmark(book_id=test_book.id, highlight_id=test_highlight.id)
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    return bookmark


@pytest.fixture
async def test_chapter(db_session: AsyncSession, test_book: models.Book) -> models.Chapter:
    """Create a test chapter for the test book."""
    chapter = models.Chapter(book_id=test_book.id, name="Chapter 1")
    db_session.add(chapter)
    await db_session.commit()
    await db_session.refresh(chapter)
    return chapter


async def create_bookmark(
    db_session: AsyncSession, book: models.Book, highlight: models.Highlight
) -> models.Bookmark:
    """Helper function to create a bookmark."""
    bookmark = models.Bookmark(book_id=book.id, highlight_id=highlight.id)
    db_session.add(bookmark)
    await db_session.commit()
    await db_session.refresh(bookmark)
    return bookmark


class TestCreateBookmark:
    """Test suite for POST /books/:id/bookmark endpoint."""

    async def test_create_bookmark_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
    ) -> None:
        """Test successful creation of a bookmark."""
        response = await client.post(
            f"/api/v1/books/{test_book.id}/bookmarks",
            json={"highlight_id": test_highlight.id},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["book_id"] == str(test_book.id)
        assert data["highlight_id"] == test_highlight.id
        assert "id" in data
        assert "created_at" in data

        # Verify bookmark was created in database
        result = await db_session.execute(select(models.Bookmark).filter_by(id=data["id"]))
        bookmark = result.scalar_one_or_none()
        assert bookmark is not None
        assert bookmark.book_id == test_book.id
        assert bookmark.highlight_id == test_highlight.id

    async def test_create_bookmark_duplicate(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
    ) -> None:
        """Test creating a duplicate bookmark returns existing bookmark."""
        # Create first bookmark
        response1 = await client.post(
            f"/api/v1/books/{test_book.id}/bookmarks",
            json={"highlight_id": test_highlight.id},
        )
        assert response1.status_code == status.HTTP_201_CREATED
        data1 = response1.json()

        # Try to create duplicate bookmark
        response2 = await client.post(
            f"/api/v1/books/{test_book.id}/bookmarks",
            json={"highlight_id": test_highlight.id},
        )
        assert response2.status_code == status.HTTP_201_CREATED
        data2 = response2.json()

        # Should return the same bookmark
        assert data1["id"] == data2["id"]

        # Verify only one bookmark exists
        result = await db_session.execute(select(models.Bookmark).filter_by(book_id=test_book.id))
        bookmarks = result.scalars().all()
        assert len(bookmarks) == 1

    async def test_create_bookmark_book_not_found(self, client: AsyncClient) -> None:
        """Test creating a bookmark for non-existent book."""
        response = await client.post(
            "/api/v1/books/00000000-0000-0000-0000-000000099999/bookmarks",
            json={"highlight_id": 1},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_bookmark_highlight_not_found(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        """Test creating a bookmark for non-existent highlight."""
        response = await client.post(
            f"/api/v1/books/{test_book.id}/bookmarks",
            json={"highlight_id": 99999},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_bookmark_highlight_belongs_to_different_book(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        """Test creating a bookmark for a highlight that belongs to a different book."""
        # Create a second book with a highlight
        book2 = await create_test_book(
            db_session=db_session,
            user_id=DEFAULT_USER_ID,
            title="Test Book 2",
            author="Test Author 2",
        )
        highlight = await create_test_highlight(
            db_session=db_session,
            book=book2,
            user_id=DEFAULT_USER_ID,
            text="Test highlight",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )

        # Try to create bookmark for test_book with highlight from book2
        response = await client.post(
            f"/api/v1/books/{test_book.id}/bookmarks",
            json={"highlight_id": highlight.id},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestDeleteBookmark:
    """Test suite for DELETE /books/:id/bookmarks/:bookmark_id endpoint."""

    async def test_delete_bookmark_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_bookmark: models.Bookmark,
    ) -> None:
        """Test successful deletion of a bookmark."""
        bookmark_id = test_bookmark.id

        response = await client.delete(f"/api/v1/books/{test_book.id}/bookmarks/{bookmark_id}")

        assert response.status_code == status.HTTP_200_OK

        # Verify bookmark was deleted
        result = await db_session.execute(select(models.Bookmark).filter_by(id=bookmark_id))
        deleted_bookmark = result.scalar_one_or_none()
        assert deleted_bookmark is None

    async def test_delete_bookmark_idempotent(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        """Test that deleting a non-existent bookmark is idempotent (returns 200)."""
        response = await client.delete(f"/api/v1/books/{test_book.id}/bookmarks/99999")

        # Should succeed (idempotent operation)
        assert response.status_code == status.HTTP_200_OK

    async def test_delete_bookmark_book_not_found(self, client: AsyncClient) -> None:
        """Test deleting a bookmark for non-existent book."""
        response = await client.delete("/api/v1/books/00000000-0000-0000-0000-000000099999/bookmarks/1")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetBookmarks:
    """Test suite for GET /books/:id/bookmarks endpoint."""

    async def test_get_bookmarks_success(
        self, client: AsyncClient, db_session: AsyncSession, test_book: models.Book
    ) -> None:
        """Test successful retrieval of bookmarks."""
        # Create multiple highlights and bookmarks for the test
        highlight1 = await create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            text="Highlight 1",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )
        highlight2 = await create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            text="Highlight 2",
            page=20,
            datetime_str="2024-01-15 15:00:00",
        )

        bookmark1 = await create_bookmark(db_session, test_book, highlight1)
        bookmark2 = await create_bookmark(db_session, test_book, highlight2)

        response = await client.get(f"/api/v1/books/{test_book.id}/bookmarks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 2

        # Verify bookmark data
        bookmark_ids = {b["id"] for b in data["bookmarks"]}
        assert bookmark1.id in bookmark_ids
        assert bookmark2.id in bookmark_ids

    async def test_get_bookmarks_empty(self, client: AsyncClient, test_book: models.Book) -> None:
        """Test getting bookmarks when book has none."""
        response = await client.get(f"/api/v1/books/{test_book.id}/bookmarks")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 0

    async def test_get_bookmarks_book_not_found(self, client: AsyncClient) -> None:
        """Test getting bookmarks for non-existent book."""
        response = await client.get("/api/v1/books/00000000-0000-0000-0000-000000099999/bookmarks")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBookDetailsWithBookmarks:
    """Test suite for bookmarks in book details endpoint."""

    async def test_book_details_includes_bookmarks(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_chapter: models.Chapter,
    ) -> None:
        """Test that GET /books/:id includes bookmarks in the response."""
        # Create highlights with chapter association
        highlight1 = await create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            chapter_id=test_chapter.id,
            text="Highlight 1",
            page=10,
            datetime_str="2024-01-15 14:30:22",
        )
        highlight2 = await create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=DEFAULT_USER_ID,
            chapter_id=test_chapter.id,
            text="Highlight 2",
            page=20,
            datetime_str="2024-01-15 15:00:00",
        )

        bookmark1 = await create_bookmark(db_session, test_book, highlight1)
        bookmark2 = await create_bookmark(db_session, test_book, highlight2)

        response = await client.get(f"/api/v1/books/{test_book.id}")

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
            assert bookmark["book_id"] == str(test_book.id)

    async def test_book_details_empty_bookmarks(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        """Test that GET /books/:id returns empty bookmarks list when no bookmarks exist."""
        response = await client.get(f"/api/v1/books/{test_book.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify bookmarks field exists but is empty
        assert "bookmarks" in data
        assert len(data["bookmarks"]) == 0


class TestBookmarkCascadeDelete:
    """Test suite for cascade deletion of bookmarks."""

    async def test_bookmark_deleted_when_book_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_bookmark: models.Bookmark,
    ) -> None:
        """Test that bookmarks are deleted when book is deleted."""
        bookmark_id = test_bookmark.id

        response = await client.delete(f"/api/v1/books/{test_book.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify bookmark was cascade deleted
        result = await db_session.execute(select(models.Bookmark).filter_by(id=bookmark_id))
        deleted_bookmark = result.scalar_one_or_none()
        assert deleted_bookmark is None

    async def test_bookmark_deleted_when_highlight_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_bookmark: models.Bookmark,
    ) -> None:
        """Test that bookmarks are deleted when highlight is deleted."""
        bookmark_id = test_bookmark.id

        # Soft delete the highlight
        payload = {"highlight_ids": [test_highlight.id]}
        response = await client.request(
            "DELETE", f"/api/v1/books/{test_book.id}/highlight", content=json.dumps(payload)
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify bookmark was deleted when highlight was soft deleted
        result = await db_session.execute(select(models.Bookmark).filter_by(id=bookmark_id))
        deleted_bookmark = result.scalar_one_or_none()
        assert deleted_bookmark is None
