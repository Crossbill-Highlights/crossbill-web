from sqlalchemy.orm import Session

from src.domain.ai.entities.ai_usage_record import AIUsageRecord
from src.infrastructure.ai.mappers.ai_usage_mapper import AIUsageMapper


class AIUsageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = AIUsageMapper()

    def save(self, record: AIUsageRecord) -> None:
        orm = self.mapper.to_orm(record)
        self.db.add(orm)
        self.db.commit()
