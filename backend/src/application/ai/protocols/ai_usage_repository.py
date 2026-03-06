from typing import Protocol

from src.domain.ai.entities.ai_usage_record import AIUsageRecord


class AIUsageRepositoryProtocol(Protocol):
    def save(self, record: AIUsageRecord) -> None: ...
