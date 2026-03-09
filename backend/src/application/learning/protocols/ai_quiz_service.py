from typing import Protocol

from src.application.ai.ai_usage_context import AIUsageContext
from src.domain.common.types import SerializedMessageHistory


class AIQuizServiceProtocol(Protocol):
    async def start_quiz(
        self, chapter_content: str, question_count: int, usage_context: AIUsageContext
    ) -> tuple[str, SerializedMessageHistory]: ...

    async def continue_quiz(
        self,
        user_message: str,
        message_history: SerializedMessageHistory,
        usage_context: AIUsageContext,
    ) -> tuple[str, SerializedMessageHistory]: ...
