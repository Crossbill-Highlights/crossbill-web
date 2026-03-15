from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.types import SerializedMessageHistory
from src.domain.common.value_objects.ids import AIChatSessionId, ChapterId, UserId


@dataclass
class AIChatSession(Entity[AIChatSessionId]):
    """A generalized AI chat session (e.g. quiz, discussion)."""

    id: AIChatSessionId
    user_id: UserId
    chapter_id: ChapterId
    session_type: str
    message_history: SerializedMessageHistory
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: UserId,
        chapter_id: ChapterId,
        session_type: str,
        created_at: datetime,
    ) -> "AIChatSession":
        return cls(
            id=AIChatSessionId.generate(),
            user_id=user_id,
            chapter_id=chapter_id,
            session_type=session_type,
            message_history=[],
            created_at=created_at,
        )

    @classmethod
    def create_with_id(
        cls,
        id: AIChatSessionId,
        user_id: UserId,
        chapter_id: ChapterId,
        session_type: str,
        message_history: SerializedMessageHistory,
        created_at: datetime,
    ) -> "AIChatSession":
        return cls(
            id=id,
            user_id=user_id,
            chapter_id=chapter_id,
            session_type=session_type,
            message_history=message_history,
            created_at=created_at,
        )
