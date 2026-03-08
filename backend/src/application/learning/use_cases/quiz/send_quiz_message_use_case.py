from datetime import UTC, datetime

import structlog
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_ai.messages import ModelRequest

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.learning.protocols.ai_quiz_service import AIQuizServiceProtocol
from src.application.learning.protocols.quiz_session_repository import (
    QuizSessionRepositoryProtocol,
)
from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class SendQuizMessageUseCase:
    def __init__(
        self,
        quiz_session_repository: QuizSessionRepositoryProtocol,
        ai_quiz_service: AIQuizServiceProtocol,
    ) -> None:
        self.quiz_session_repo = quiz_session_repository
        self.ai_quiz_service = ai_quiz_service

    async def send(self, session_id: int, user_message: str, user_id: int) -> tuple[str, bool]:
        """Send a message to an existing quiz session.

        Returns:
            Tuple of (ai_response, is_complete)
        """
        session_id_vo = QuizSessionId(session_id)
        user_id_vo = UserId(user_id)

        # 1. Load session
        session = self.quiz_session_repo.find_by_id(session_id_vo, user_id_vo)
        if not session:
            raise NotFoundError(f"Quiz session {session_id} not found")

        if session.completed_at is not None:
            raise NotFoundError(f"Quiz session {session_id} is already completed")

        # 2. Run AI with message history
        usage_context = AIUsageContext(
            user_id=user_id_vo,
            task_type="quiz",
            entity_type="chapter",
            entity_id=session.chapter_id.value,
        )
        ai_response, updated_history = await self.ai_quiz_service.continue_quiz(
            user_message, session.message_history, usage_context
        )

        # 3. Check if quiz is complete
        # Count user turns (ModelRequest messages) in updated history.
        # Subtract 1 for the initial chapter content message.
        restored = ModelMessagesTypeAdapter.validate_python(updated_history)
        user_turn_count = sum(1 for msg in restored if isinstance(msg, ModelRequest))
        answer_count = user_turn_count - 1
        is_complete = answer_count >= session.question_count

        # 4. Update session
        completed_at = datetime.now(UTC) if is_complete else None

        self.quiz_session_repo.update_message_history(
            session_id_vo, updated_history, completed_at
        )

        logger.info(
            "quiz_message_sent",
            session_id=session_id,
            is_complete=is_complete,
            answer_count=answer_count,
        )

        return ai_response, is_complete
