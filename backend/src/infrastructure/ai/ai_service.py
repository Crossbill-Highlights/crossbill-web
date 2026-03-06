from datetime import UTC, datetime

import structlog

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.ai.protocols.ai_usage_repository import AIUsageRepositoryProtocol
from src.application.learning.protocols.ai_flashcard_service import AIFlashcardSuggestion
from src.application.reading.protocols.ai_prereading_service import PrereadingResult
from src.domain.ai.entities.ai_usage_record import AIUsageRecord
from src.infrastructure.ai.ai_agents import (
    get_flashcard_agent,
    get_prereading_agent,
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
