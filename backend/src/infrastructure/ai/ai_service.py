from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.ai.protocols.ai_usage_repository import AIUsageRepositoryProtocol
from src.application.learning.protocols.ai_flashcard_service import AIFlashcardSuggestion
from src.application.reading.protocols.ai_prereading_service import PrereadingResult
from src.domain.ai.entities.ai_usage_record import AIUsageRecord
from src.infrastructure.ai.ai_agents import (
    get_flashcard_agent,
    get_prereading_agent,
    get_quiz_agent,
    get_summary_agent,
)

logger = structlog.get_logger(__name__)


class AIService:
    def __init__(self, usage_repository: AIUsageRepositoryProtocol) -> None:
        self.usage_repository = usage_repository

    def _save_usage(
        self,
        usage_context: AIUsageContext,
        model_name: str | None,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        record = AIUsageRecord.create(
            user_id=usage_context.user_id,
            task_type=usage_context.task_type,
            entity_type=usage_context.entity_type,
            entity_id=usage_context.entity_id,
            model_name=model_name or "unknown",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            created_at=datetime.now(UTC),
        )
        self.usage_repository.save(record)
        logger.info(
            "ai_usage_recorded",
            task_type=usage_context.task_type,
            entity_type=usage_context.entity_type,
            entity_id=usage_context.entity_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model_name=model_name,
        )

    async def generate_summary(self, content: str, usage_context: AIUsageContext) -> str:
        agent = get_summary_agent()
        result = await agent.run(content)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        return result.output

    async def generate_prereading(
        self, content: str, usage_context: AIUsageContext
    ) -> PrereadingResult:
        agent = get_prereading_agent()
        result = await agent.run(content[:10000])
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        return PrereadingResult(summary=result.output.summary, keypoints=result.output.keypoints)

    async def generate_flashcard_suggestions(
        self, content: str, usage_context: AIUsageContext
    ) -> list[AIFlashcardSuggestion]:
        agent = get_flashcard_agent()
        result = await agent.run(content)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        return [AIFlashcardSuggestion(question=s.question, answer=s.answer) for s in result.output]

    async def start_quiz(
        self, chapter_content: str, question_count: int, usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]:
        agent = get_quiz_agent()
        prompt = f"The reader wants to be quizzed on this chapter. Ask {question_count} questions total.\n\n--- CHAPTER CONTENT ---\n{chapter_content}"
        result = await agent.run(prompt)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        serialized = to_jsonable_python(result.all_messages())
        return result.output, serialized

    async def continue_quiz(
        self, user_message: str, message_history: list[dict[str, Any]], usage_context: AIUsageContext
    ) -> tuple[str, list[dict[str, Any]]]:
        agent = get_quiz_agent()
        restored = ModelMessagesTypeAdapter.validate_python(message_history)
        result = await agent.run(user_message, message_history=restored)
        usage = result.usage()
        self._save_usage(
            usage_context, result.response.model_name, usage.input_tokens, usage.output_tokens
        )
        serialized = to_jsonable_python(result.all_messages())
        return result.output, serialized
