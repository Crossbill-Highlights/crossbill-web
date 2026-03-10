"""Mapper for AIChatSession ORM <-> Domain conversion."""

from src.domain.common.value_objects.ids import AIChatSessionId, ChapterId, UserId
from src.domain.learning.entities.ai_chat_session import AIChatSession
from src.models import AIChatSession as AIChatSessionModel


class AIChatSessionMapper:
    """Mapper for AIChatSession ORM <-> Domain conversion."""

    def to_domain(self, model: AIChatSessionModel) -> AIChatSession:
        """Convert ORM model to domain entity."""
        return AIChatSession.create_with_id(
            id=AIChatSessionId(model.id),
            user_id=UserId(model.user_id),
            chapter_id=ChapterId(model.chapter_id),
            session_type=model.session_type,
            message_history=model.message_history,
            created_at=model.created_at,
        )

    def to_orm(self, entity: AIChatSession) -> AIChatSessionModel:
        """Convert domain entity to ORM model."""
        model = AIChatSessionModel(
            user_id=entity.user_id.value,
            chapter_id=entity.chapter_id.value,
            session_type=entity.session_type,
            message_history=entity.message_history,
            created_at=entity.created_at,
        )
        if entity.id.value != 0:
            model.id = entity.id.value
        return model
