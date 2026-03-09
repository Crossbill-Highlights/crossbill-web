"""Protocol for AIChatSession repository in learning context."""

from typing import Protocol

from src.domain.common.types import SerializedMessageHistory
from src.domain.common.value_objects.ids import AIChatSessionId, UserId
from src.domain.learning.entities.ai_chat_session import AIChatSession


class AIChatSessionRepositoryProtocol(Protocol):
    """Protocol for AIChatSession repository operations in learning context."""

    def create(self, session: AIChatSession) -> AIChatSession: ...

    def find_by_id(self, session_id: AIChatSessionId, user_id: UserId) -> AIChatSession | None: ...

    def update_message_history(
        self,
        session_id: AIChatSessionId,
        message_history: SerializedMessageHistory,
    ) -> None: ...
