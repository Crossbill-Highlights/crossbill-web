from typing import Protocol

from src.application.ai.ai_usage_context import AIUsageContext


class AITextSummaryServiceProtocol(Protocol):
    async def generate_summary(self, content: str, usage_context: AIUsageContext) -> str: ...
