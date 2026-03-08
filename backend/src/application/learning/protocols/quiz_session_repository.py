"""Protocol for QuizSession repository in learning context."""

from datetime import datetime
from typing import Any, Protocol

from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession


class QuizSessionRepositoryProtocol(Protocol):
    """Protocol for QuizSession repository operations in learning context."""

    def create(self, session: QuizSession) -> QuizSession:
        """
        Create a new quiz session.

        Args:
            session: The quiz session entity to create

        Returns:
            Created quiz session entity with database-generated values
        """
        ...

    def find_by_id(self, session_id: QuizSessionId, user_id: UserId) -> QuizSession | None:
        """
        Find a quiz session by ID with user ownership check.

        Args:
            session_id: The quiz session ID
            user_id: The user ID for ownership verification

        Returns:
            QuizSession entity if found and owned by user, None otherwise
        """
        ...

    def update_message_history(
        self,
        session_id: QuizSessionId,
        message_history: list[dict[str, Any]],
        completed_at: datetime | None,
    ) -> None:
        """
        Update the message history and completion status of a quiz session.

        Args:
            session_id: The quiz session ID
            message_history: The updated message history
            completed_at: The completion timestamp, or None if not yet completed
        """
        ...
