from typing import Any, Protocol

from src.application.ai.ai_usage_context import AIUsageContext


class AIQuizServiceProtocol(Protocol):
    async def start_quiz(
        self, chapter_content: str, question_count: int, usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]: ...

    async def continue_quiz(
        self,
        user_message: str,
        message_history: list[dict[str, Any]],
        usage_context: AIUsageContext,
    ) -> tuple[str, list[dict[str, Any]]]: ...
