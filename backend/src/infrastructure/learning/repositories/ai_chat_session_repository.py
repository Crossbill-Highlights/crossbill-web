"""Repository for AIChatSession domain entities."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import AIChatSessionId, UserId
from src.domain.learning.entities.ai_chat_session import AIChatSession
from src.infrastructure.learning.mappers.ai_chat_session_mapper import AIChatSessionMapper
from src.models import AIChatSession as AIChatSessionModel


class AIChatSessionRepository:
    """Repository for AIChatSession domain entities."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = AIChatSessionMapper()

    def create(self, session: AIChatSession) -> AIChatSession:
        orm_model = self.mapper.to_orm(session)
        self.db.add(orm_model)
        self.db.commit()
        self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    def find_by_id(self, session_id: AIChatSessionId, user_id: UserId) -> AIChatSession | None:
        result = self.db.execute(
            select(AIChatSessionModel).where(
                AIChatSessionModel.id == session_id.value,
                AIChatSessionModel.user_id == user_id.value,
            )
        ).scalar_one_or_none()
        if result is None:
            return None
        return self.mapper.to_domain(result)

    def update_message_history(
        self,
        session_id: AIChatSessionId,
        message_history: list[dict[str, Any]],
    ) -> None:
        result = self.db.execute(
            select(AIChatSessionModel).where(AIChatSessionModel.id == session_id.value)
        ).scalar_one_or_none()
        if result is None:
            return
        result.message_history = message_history
        self.db.commit()
