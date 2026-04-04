"""SAQ task handler for chapter prereading generation."""

import structlog
from saq.types import Context

from src.application.reading.use_cases.chapter_prereading.generate_prereading_from_text_use_case import (
    GeneratePrereadingFromTextUseCase,
)
from src.domain.common.value_objects.ids import ChapterId, UserId

logger = structlog.get_logger(__name__)


class PrereadingTaskHandler:
    def __init__(
        self,
        generate_from_text_use_case: GeneratePrereadingFromTextUseCase,
    ) -> None:
        self._use_case = generate_from_text_use_case

    async def generate(
        self,
        _ctx: Context,
        *,
        batch_id: int,
        chapter_id: int,
        user_id: int,
        chapter_text: str,
    ) -> None:
        logger.info(
            "prereading_task_started",
            batch_id=batch_id,
            chapter_id=chapter_id,
        )
        await self._use_case.execute(
            chapter_id=ChapterId(chapter_id),
            user_id=UserId(user_id),
            chapter_text=chapter_text,
        )
        logger.info(
            "prereading_task_completed",
            batch_id=batch_id,
            chapter_id=chapter_id,
        )
