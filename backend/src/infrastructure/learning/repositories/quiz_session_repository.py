"""Repository for QuizSession domain entities."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession
from src.infrastructure.learning.mappers.quiz_session_mapper import QuizSessionMapper
from src.models import QuizSession as QuizSessionModel


class QuizSessionRepository:
    """Repository for QuizSession domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = QuizSessionMapper()

    def create(self, session: QuizSession) -> QuizSession:
        orm_model = self.mapper.to_orm(session)
        self.db.add(orm_model)
        self.db.commit()
        self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    def find_by_id(self, session_id: QuizSessionId, user_id: UserId) -> QuizSession | None:
        result = self.db.execute(
            select(QuizSessionModel).where(
                QuizSessionModel.id == session_id.value,
                QuizSessionModel.user_id == user_id.value,
            )
        ).scalar_one_or_none()
        if result is None:
            return None
        return self.mapper.to_domain(result)

    def update_message_history(
        self,
        session_id: QuizSessionId,
        message_history: list[dict[str, Any]],
    ) -> None:
        result = self.db.execute(
            select(QuizSessionModel).where(QuizSessionModel.id == session_id.value)
        ).scalar_one_or_none()
        if result is None:
            return
        result.message_history = message_history
        self.db.commit()
