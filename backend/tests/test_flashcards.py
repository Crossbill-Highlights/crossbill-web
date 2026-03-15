"""Tests for flashcards API endpoints."""

import json

from fastapi import status
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src import models


class TestCreateFlashcardForHighlight:
    """Test suite for POST /highlights/:id/flashcards endpoint."""

    async def test_create_flashcard_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_user: models.User,
    ) -> None:
        """Test successful creation of a flashcard for a highlight."""
        response = await client.post(
            f"/api/v1/highlights/{test_highlight.id}/flashcards",
            json={"question": "What is this about?", "answer": "Test content"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        assert "flashcard" in data
        flashcard = data["flashcard"]
        assert flashcard["question"] == "What is this about?"
        assert flashcard["answer"] == "Test content"
        assert flashcard["book_id"] == test_book.id
        assert flashcard["highlight_id"] == test_highlight.id
        assert flashcard["user_id"] == test_user.id

        # Verify flashcard was created in database
        result = await db_session.execute(select(models.Flashcard).filter_by(id=flashcard["id"]))
        db_flashcard = result.scalar_one_or_none()
        assert db_flashcard is not None
        assert db_flashcard.question == "What is this about?"
        assert db_flashcard.answer == "Test content"

    async def test_create_flashcard_highlight_not_found(self, client: AsyncClient) -> None:
        """Test creating a flashcard for non-existent highlight."""
        response = await client.post(
            "/api/v1/highlights/99999/flashcards",
            json={"question": "What is this?", "answer": "Answer"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_flashcard_empty_question(
        self, client: AsyncClient, test_highlight: models.Highlight
    ) -> None:
        """Test creating a flashcard with empty question fails."""
        response = await client.post(
            f"/api/v1/highlights/{test_highlight.id}/flashcards",
            json={"question": "", "answer": "Test answer"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestCreateFlashcardForBook:
    """Test suite for POST /books/:id/flashcards endpoint."""

    async def test_create_flashcard_success(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        """Test successful creation of a standalone flashcard for a book."""
        response = await client.post(
            f"/api/v1/books/{test_book.id}/flashcards",
            json={"question": "What is the main theme?", "answer": "The main theme is..."},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["success"] is True
        flashcard = data["flashcard"]
        assert flashcard["question"] == "What is the main theme?"
        assert flashcard["answer"] == "The main theme is..."
        assert flashcard["book_id"] == test_book.id
        assert flashcard["highlight_id"] is None  # Standalone flashcard
        assert flashcard["chapter_id"] is None

    async def test_create_flashcard_with_chapter_id(
        self, client: AsyncClient, test_book: models.Book, test_chapter: models.Chapter
    ) -> None:
        """Test creating a flashcard linked to a specific chapter."""
        response = await client.post(
            f"/api/v1/books/{test_book.id}/flashcards",
            json={
                "question": "Chapter question",
                "answer": "Chapter answer",
                "chapter_id": test_chapter.id,
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["flashcard"]["chapter_id"] == test_chapter.id
        assert data["flashcard"]["highlight_id"] is None

    async def test_create_flashcard_with_invalid_chapter_id(
        self, client: AsyncClient, test_book: models.Book
    ) -> None:
        """Test creating a flashcard with a non-existent chapter_id returns 404."""
        response = await client.post(
            f"/api/v1/books/{test_book.id}/flashcards",
            json={
                "question": "Q",
                "answer": "A",
                "chapter_id": 99999,
            },
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_create_flashcard_book_not_found(self, client: AsyncClient) -> None:
        """Test creating a flashcard for non-existent book."""
        response = await client.post(
            "/api/v1/books/99999/flashcards",
            json={"question": "What is this?", "answer": "Answer"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetFlashcardsForBook:
    """Test suite for GET /books/:id/flashcards endpoint."""

    async def test_get_flashcards_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_user: models.User,
    ) -> None:
        """Test successful retrieval of flashcards for a book."""
        # Create flashcards
        flashcard1 = models.Flashcard(
            user_id=test_user.id,
            book_id=test_book.id,
            highlight_id=test_highlight.id,
            question="Question 1",
            answer="Answer 1",
        )
        flashcard2 = models.Flashcard(
            user_id=test_user.id,
            book_id=test_book.id,
            highlight_id=None,
            question="Question 2",
            answer="Answer 2",
        )
        db_session.add_all([flashcard1, flashcard2])
        await db_session.commit()

        response = await client.get(f"/api/v1/books/{test_book.id}/flashcards")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "flashcards" in data
        assert len(data["flashcards"]) == 2

    async def test_get_flashcards_empty(self, client: AsyncClient, test_book: models.Book) -> None:
        """Test getting flashcards when book has none."""
        response = await client.get(f"/api/v1/books/{test_book.id}/flashcards")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "flashcards" in data
        assert len(data["flashcards"]) == 0

    async def test_get_flashcards_book_not_found(self, client: AsyncClient) -> None:
        """Test getting flashcards for non-existent book."""
        response = await client.get("/api/v1/books/99999/flashcards")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateFlashcard:
    """Test suite for PUT /flashcards/:id endpoint."""

    async def test_update_flashcard_success(
        self, client: AsyncClient, test_flashcard: models.Flashcard
    ) -> None:
        """Test successful update of a flashcard."""
        response = await client.put(
            f"/api/v1/flashcards/{test_flashcard.id}",
            json={"question": "Updated question", "answer": "Updated answer"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["flashcard"]["question"] == "Updated question"
        assert data["flashcard"]["answer"] == "Updated answer"

    async def test_update_flashcard_partial(
        self, client: AsyncClient, test_flashcard: models.Flashcard
    ) -> None:
        """Test partial update of a flashcard (only question)."""
        original_answer = test_flashcard.answer

        response = await client.put(
            f"/api/v1/flashcards/{test_flashcard.id}",
            json={"question": "Updated question only"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["flashcard"]["question"] == "Updated question only"
        assert data["flashcard"]["answer"] == original_answer

    async def test_update_flashcard_not_found(self, client: AsyncClient) -> None:
        """Test updating non-existent flashcard."""
        response = await client.put(
            "/api/v1/flashcards/99999",
            json={"question": "Updated question"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteFlashcard:
    """Test suite for DELETE /flashcards/:id endpoint."""

    async def test_delete_flashcard_success(
        self, client: AsyncClient, db_session: AsyncSession, test_flashcard: models.Flashcard
    ) -> None:
        """Test successful deletion of a flashcard."""
        flashcard_id = test_flashcard.id

        response = await client.delete(f"/api/v1/flashcards/{flashcard_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

        # Verify flashcard was deleted
        result = await db_session.execute(select(models.Flashcard).filter_by(id=flashcard_id))
        deleted = result.scalar_one_or_none()
        assert deleted is None

    async def test_delete_flashcard_not_found(self, client: AsyncClient) -> None:
        """Test deleting non-existent flashcard."""
        response = await client.delete("/api/v1/flashcards/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestFlashcardCascadeDelete:
    """Test suite for cascade deletion of flashcards."""

    async def test_flashcard_deleted_when_book_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_flashcard: models.Flashcard,
    ) -> None:
        """Test that flashcards are deleted when book is deleted."""
        flashcard_id = test_flashcard.id

        # Delete the book
        response = await client.delete(f"/api/v1/books/{test_book.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify flashcard was cascade deleted
        result = await db_session.execute(select(models.Flashcard).filter_by(id=flashcard_id))
        deleted = result.scalar_one_or_none()
        assert deleted is None

    async def test_flashcard_deleted_when_highlight_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_book: models.Book,
        test_highlight: models.Highlight,
        test_user: models.User,
    ) -> None:
        """Test that flashcards linked to a highlight are deleted when highlight is deleted."""
        flashcard = models.Flashcard(
            user_id=test_user.id,
            book_id=test_book.id,
            highlight_id=test_highlight.id,
            question="Test question",
            answer="Test answer",
        )
        db_session.add(flashcard)
        await db_session.commit()
        await db_session.refresh(flashcard)

        flashcard_id = flashcard.id

        # Soft delete the highlight
        payload = {"highlight_ids": [test_highlight.id]}
        response = await client.request(
            "DELETE", f"/api/v1/books/{test_book.id}/highlight", content=json.dumps(payload)
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify flashcard was deleted (cascade from highlight delete)
        result = await db_session.execute(select(models.Flashcard).filter_by(id=flashcard_id))
        deleted = result.scalar_one_or_none()
        assert deleted is None
