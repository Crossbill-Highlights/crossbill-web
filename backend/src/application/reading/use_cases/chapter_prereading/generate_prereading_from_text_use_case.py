"""Use case for generating chapter prereading from pre-extracted text."""

from datetime import UTC, datetime

import structlog

from src.application.ai.ai_usage_context import AIUsageContext
from src.application.reading.protocols.ai_prereading_service import (
    AIPrereadingServiceProtocol,
)
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import ChapterId, UserId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)

logger = structlog.get_logger(__name__)


class GeneratePrereadingFromTextUseCase:
    """Generate prereading content from already-extracted chapter text.

    Used by the background worker where the text was extracted at enqueue
    time (on the app server which has filesystem access).
    """

    def __init__(
        self,
        prereading_repo: ChapterPrereadingRepositoryProtocol,
        ai_prereading_service: AIPrereadingServiceProtocol,
    ) -> None:
        self._prereading_repo = prereading_repo
        self._ai_prereading_service = ai_prereading_service

    async def execute(
        self, chapter_id: ChapterId, user_id: UserId, chapter_text: str
    ) -> ChapterPrereadingContent:
        try:
            usage_context = AIUsageContext(
                user_id=user_id,
                task_type="prereading",
                entity_type="chapter",
                entity_id=chapter_id.value,
            )
            ai_result = await self._ai_prereading_service.generate_prereading(
                chapter_text, usage_context
            )
        except Exception as e:
            logger.error("ai_service_failed", error=str(e))
            raise DomainError(f"Failed to generate prereading content: {e}") from e

        entity = ChapterPrereadingContent.create(
            chapter_id=chapter_id,
            summary=ai_result.summary,
            keypoints=ai_result.keypoints,
            questions=ai_result.questions,
            generated_at=datetime.now(UTC),
            ai_model="ai-configured-model",
        )

        logger.info(
            "prereading_content_generated",
            chapter_id=chapter_id.value,
            keypoints_count=len(ai_result.keypoints),
        )
        return await self._prereading_repo.save(entity)
