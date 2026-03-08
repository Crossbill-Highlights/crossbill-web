"""Mapper for QuizSession ORM <-> Domain conversion."""

from src.domain.common.value_objects.ids import ChapterId, QuizSessionId, UserId
from src.domain.learning.entities.quiz_session import QuizSession
from src.models import QuizSession as QuizSessionModel


class QuizSessionMapper:
    """Mapper for QuizSession ORM <-> Domain conversion."""

    def to_domain(self, model: QuizSessionModel) -> QuizSession:
        """Convert ORM model to domain entity."""
        return QuizSession.create_with_id(
            id=QuizSessionId(model.id),
            user_id=UserId(model.user_id),
            chapter_id=ChapterId(model.chapter_id),
            message_history=model.message_history,
            created_at=model.created_at,
        )

    def to_orm(self, entity: QuizSession) -> QuizSessionModel:
        """Convert domain entity to ORM model."""
        model = QuizSessionModel(
            user_id=entity.user_id.value,
            chapter_id=entity.chapter_id.value,
            message_history=entity.message_history,
            created_at=entity.created_at,
        )
        if entity.id.value != 0:
            model.id = entity.id.value
        return model
