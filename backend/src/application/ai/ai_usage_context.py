from dataclasses import dataclass

from src.domain.common.value_objects.ids import UserId


@dataclass(frozen=True)
class AIUsageContext:
    """Context passed to AI service methods for usage tracking."""

    user_id: UserId
    task_type: str
    entity_type: str
    entity_id: int
