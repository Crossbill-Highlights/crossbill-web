from typing import Protocol

from src.application.ai.ai_usage_context import AIUsageContext
from src.domain.common.types import SerializedMessageHistory


class AIChatServiceProtocol(Protocol):
    async def start_chat(
        self, chapter_content: str, usage_context: AIUsageContext
    ) -> tuple[str, SerializedMessageHistory]: ...

    async def continue_chat(
        self,
        user_message: str,
        message_history: SerializedMessageHistory,
        usage_context: AIUsageContext,
    ) -> tuple[str, SerializedMessageHistory]: ...
