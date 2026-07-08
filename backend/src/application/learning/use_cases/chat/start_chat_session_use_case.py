from datetime import UTC, datetime

import structlog

from src.application.learning.protocols.ai_chat_service import AIChatServiceProtocol
from src.application.learning.protocols.ai_chat_session_repository import (
    AIChatSessionRepositoryProtocol,
)
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.domain.common.value_objects.ids import ChapterId, UserId
from src.domain.learning.entities.ai_chat_session import AIChatSession
from src.domain.reading.exceptions import ChapterNotFoundError

logger = structlog.get_logger(__name__)


class StartChatSessionUseCase:
    def __init__(
        self,
        ai_chat_session_repository: AIChatSessionRepositoryProtocol,
        chapter_repo: ChapterRepositoryProtocol,
        ai_chat_service: AIChatServiceProtocol,
    ) -> None:
        self.ai_chat_session_repo = ai_chat_session_repository
        self.chapter_repo = chapter_repo
        self.ai_chat_service = ai_chat_service

    async def start(self, chapter_id: int, user_id: int) -> tuple[int, str]:
        """Start a new chat session for a chapter.

        Returns:
            Tuple of (session_id, first_question)
        """
        chapter_id_vo = ChapterId(chapter_id)
        user_id_vo = UserId(user_id)

        chapter = await self.chapter_repo.find_by_id(chapter_id_vo, user_id_vo)
        if not chapter:
            raise ChapterNotFoundError(chapter_id)

        session = AIChatSession.create(
            user_id=user_id_vo,
            chapter_id=chapter_id_vo,
            session_type="chat",
            created_at=datetime.now(UTC),
        )

        first_response = "What do you want to chat about this chapter?"

        session.message_history = []
        saved_session = await self.ai_chat_session_repo.create(session)

        logger.info(
            "chat_session_started",
            session_id=saved_session.id.value,
            chapter_id=chapter_id,
        )

        return saved_session.id.value, first_response
