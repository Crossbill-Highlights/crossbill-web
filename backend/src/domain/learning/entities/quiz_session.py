from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import ChapterId, QuizSessionId, UserId


@dataclass
class QuizSession(Entity[QuizSessionId]):
    """A quiz conversation session for a chapter."""

    id: QuizSessionId
    user_id: UserId
    chapter_id: ChapterId
    message_history: list[dict[str, Any]]
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: UserId,
        chapter_id: ChapterId,
        created_at: datetime,
    ) -> "QuizSession":
        return cls(
            id=QuizSessionId.generate(),
            user_id=user_id,
            chapter_id=chapter_id,
            message_history=[],
            created_at=created_at,
        )

    @classmethod
    def create_with_id(
        cls,
        id: QuizSessionId,
        user_id: UserId,
        chapter_id: ChapterId,
        message_history: list[dict[str, Any]],
        created_at: datetime,
    ) -> "QuizSession":
        return cls(
            id=id,
            user_id=user_id,
            chapter_id=chapter_id,
            message_history=message_history,
            created_at=created_at,
        )
