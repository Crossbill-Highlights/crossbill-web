"""Protocol for QuizSession repository in learning context."""

from typing import Any, Protocol

from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession


class QuizSessionRepositoryProtocol(Protocol):
    """Protocol for QuizSession repository operations in learning context."""

    def create(self, session: QuizSession) -> QuizSession: ...

    def find_by_id(self, session_id: QuizSessionId, user_id: UserId) -> QuizSession | None: ...

    def update_message_history(
        self,
        session_id: QuizSessionId,
        message_history: list[dict[str, Any]],
    ) -> None: ...
