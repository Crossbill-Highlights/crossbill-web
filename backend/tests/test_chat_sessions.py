"""Tests for chat session endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AIChatSession as AIChatSessionModel
from src.models import Chapter

CHAT_OPENER = "What do you want to chat about this chapter?"


class TestCreateChatSession:
    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_create_chat_session_success(
        self,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        test_chapter: Chapter,
    ) -> None:
        response = await client.post(f"/api/v1/chapters/{test_chapter.id}/chat-sessions")
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert data["message"] == CHAT_OPENER

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_create_chat_session_chapter_not_found(
        self, mock_ai_enabled: MagicMock, client: AsyncClient
    ) -> None:
        response = await client.post("/api/v1/chapters/99999/chat-sessions")
        assert response.status_code == 404


class TestSendChatMessage:
    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_send_message_session_not_found(
        self, mock_ai_enabled: MagicMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/chat-sessions/99999/messages",
            json={"message": "Hi"},
        )
        assert response.status_code == 404

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    async def test_send_empty_message_rejected(
        self, mock_ai_enabled: MagicMock, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/chat-sessions/1/messages",
            json={"message": ""},
        )
        assert response.status_code == 422

    @patch("src.infrastructure.common.dependencies.is_ai_enabled", return_value=True)
    @patch(
        "src.infrastructure.ai.ai_service.AIService.continue_chat",
        new_callable=AsyncMock,
    )
    async def test_send_message_success(
        self,
        mock_continue_chat: AsyncMock,
        mock_ai_enabled: MagicMock,
        client: AsyncClient,
        db_session: AsyncSession,
        test_chapter: Chapter,
    ) -> None:
        chat_session = AIChatSessionModel(
            user_id=1,
            chapter_id=test_chapter.id,
            session_type="chat",
            message_history=[{"some": "history"}],
        )
        db_session.add(chat_session)
        await db_session.commit()
        await db_session.refresh(chat_session)

        mock_continue_chat.return_value = (
            "Sure — what interested you in this chapter?",
            [{"updated": "history"}],
        )

        response = await client.post(
            f"/api/v1/chat-sessions/{chat_session.id}/messages",
            json={"message": "Let's talk about the main theme"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sure — what interested you in this chapter?"
