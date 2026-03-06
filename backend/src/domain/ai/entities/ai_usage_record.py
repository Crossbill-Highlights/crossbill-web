from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import AIUsageRecordId, UserId


@dataclass
class AIUsageRecord(Entity[AIUsageRecordId]):
    """Records AI service usage for cost tracking."""

    id: AIUsageRecordId
    user_id: UserId
    task_type: str
    entity_type: str
    entity_id: int
    model_name: str
    input_tokens: int
    output_tokens: int
    created_at: datetime

    @classmethod
    def create(
        cls,
        user_id: UserId,
        task_type: str,
        entity_type: str,
        entity_id: int,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        created_at: datetime,
    ) -> "AIUsageRecord":
        return cls(
            id=AIUsageRecordId.generate(),
            user_id=user_id,
            task_type=task_type,
            entity_type=entity_type,
            entity_id=entity_id,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_at=created_at,
        )
