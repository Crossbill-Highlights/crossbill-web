"""Tests for highlights AI API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src import models
from src.services.ai.ai_agents import FlashcardSuggestion
from tests.conftest import create_test_book, create_test_highlight


class TestHighlightFlashcardSuggestions:
    """Test suite for highlight flashcard suggestions endpoint."""

    @pytest.mark.asyncio
    async def test_get_flashcard_suggestions_success(
        self,
        client: TestClient,
        db_session: Session,
        test_highlight: models.Highlight,
    ) -> None:
        """Test successful generation of flashcard suggestions."""
        # Mock AI service to return suggestions
        mock_suggestions = [
            FlashcardSuggestion(
                question="What is the main topic?",
                answer="The main topic is testing",
            ),
            FlashcardSuggestion(
                question="What is the key concept?",
                answer="The key concept is AI-powered flashcards",
            ),
        ]

        with patch(
            "src.services.flashcard_service.get_ai_flashcard_suggestions_from_text",
            new=AsyncMock(return_value=mock_suggestions),
        ):
            response = client.get(f"/api/v1/highlights/{test_highlight.id}/flashcard_suggestions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 2
        assert data["suggestions"][0]["question"] == "What is the main topic?"
        assert data["suggestions"][0]["answer"] == "The main topic is testing"
        assert data["suggestions"][1]["question"] == "What is the key concept?"
        assert data["suggestions"][1]["answer"] == "The key concept is AI-powered flashcards"

    def test_get_flashcard_suggestions_not_found(
        self,
        client: TestClient,
        db_session: Session,
    ) -> None:
        """Test 404 when highlight does not exist."""
        response = client.get("/api/v1/highlights/999999/flashcard_suggestions")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_flashcard_suggestions_ownership_validation(
        self,
        client: TestClient,
        db_session: Session,
        test_user: models.User,
    ) -> None:
        """Test that user cannot access another user's highlight."""
        # Create a different user
        other_user = models.User(id=2, email="other@test.com")
        db_session.add(other_user)
        db_session.commit()

        # Create a book and highlight for the other user
        other_book = create_test_book(
            db_session=db_session,
            user_id=other_user.id,
            title="Other User's Book",
            author="Other Author",
        )
        other_highlight = create_test_highlight(
            db_session=db_session,
            book=other_book,
            user_id=other_user.id,
            text="Other user's highlight text",
            datetime_str="2024-01-15 14:30:22",
        )

        # Try to access other user's highlight with test_user credentials
        response = client.get(f"/api/v1/highlights/{other_highlight.id}/flashcard_suggestions")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_flashcard_suggestions_empty_list(
        self,
        client: TestClient,
        db_session: Session,
        test_highlight: models.Highlight,
    ) -> None:
        """Test handling when AI returns no suggestions."""
        # Mock AI service to return empty list
        with patch(
            "src.services.flashcard_service.get_ai_flashcard_suggestions_from_text",
            new=AsyncMock(return_value=[]),
        ):
            response = client.get(f"/api/v1/highlights/{test_highlight.id}/flashcard_suggestions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 0

    @pytest.mark.asyncio
    async def test_get_flashcard_suggestions_with_meaningful_text(
        self,
        client: TestClient,
        db_session: Session,
        test_user: models.User,
        test_book: models.Book,
    ) -> None:
        """Test suggestions generation with meaningful highlight text."""
        # Create a highlight with longer, more meaningful text
        highlight = create_test_highlight(
            db_session=db_session,
            book=test_book,
            user_id=test_user.id,
            text="The mitochondria is the powerhouse of the cell. "
            "It generates ATP through cellular respiration.",
            datetime_str="2024-01-15 14:30:22",
        )

        # Mock AI service
        mock_suggestions = [
            FlashcardSuggestion(
                question="What is the function of mitochondria?",
                answer="To generate ATP through cellular respiration",
            ),
        ]

        with patch(
            "src.services.flashcard_service.get_ai_flashcard_suggestions_from_text",
            new=AsyncMock(return_value=mock_suggestions),
        ):
            response = client.get(f"/api/v1/highlights/{highlight.id}/flashcard_suggestions")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["suggestions"]) == 1
        assert "mitochondria" in data["suggestions"][0]["question"].lower()
