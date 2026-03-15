"""Repository for AIChatSession domain entities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.types import SerializedMessageHistory
from src.domain.common.value_objects.ids import AIChatSessionId, UserId
from src.domain.learning.entities.ai_chat_session import AIChatSession
from src.infrastructure.learning.mappers.ai_chat_session_mapper import AIChatSessionMapper
from src.models import AIChatSession as AIChatSessionModel


class AIChatSessionRepository:
    """Repository for AIChatSession domain entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.mapper = AIChatSessionMapper()

    async def create(self, session: AIChatSession) -> AIChatSession:
        orm_model = self.mapper.to_orm(session)
        self.db.add(orm_model)
        await self.db.commit()
        await self.db.refresh(orm_model)
        return self.mapper.to_domain(orm_model)

    async def find_by_id(
        self, session_id: AIChatSessionId, user_id: UserId
    ) -> AIChatSession | None:
        result = await self.db.execute(
            select(AIChatSessionModel).where(
                AIChatSessionModel.id == session_id.value,
                AIChatSessionModel.user_id == user_id.value,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self.mapper.to_domain(row)

    async def update_message_history(
        self,
        session_id: AIChatSessionId,
        message_history: SerializedMessageHistory,
    ) -> None:
        result = await self.db.execute(
            select(AIChatSessionModel).where(AIChatSessionModel.id == session_id.value)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return
        row.message_history = message_history
        await self.db.commit()
