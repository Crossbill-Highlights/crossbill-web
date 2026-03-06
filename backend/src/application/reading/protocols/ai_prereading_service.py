from dataclasses import dataclass
from typing import Protocol

from src.application.ai.ai_usage_context import AIUsageContext


@dataclass(frozen=True)
class PrereadingResult:
    summary: str
    keypoints: list[str]


class AIPrereadingServiceProtocol(Protocol):
    async def generate_prereading(
        self, content: str, usage_context: AIUsageContext
    ) -> PrereadingResult: ...
