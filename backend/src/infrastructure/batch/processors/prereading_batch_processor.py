"""Batch processor for generating chapter prereading content."""

from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ai.ai_usage_context import AIUsageContext
from src.domain.ai.entities.ai_usage_record import AIUsageRecord
from src.domain.common.value_objects.ids import BatchItemId, BookId, ChapterId, UserId
from src.domain.reading.entities.chapter_prereading_content import ChapterPrereadingContent
from src.infrastructure.ai.ai_agents import PrereadingContent
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.batch.batch_ai_model import get_batch_ai_model
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.models import Book as BookORM
from src.models import Chapter as ChapterORM
from pydantic_ai import Agent

logger = structlog.get_logger(__name__)

MIN_CHAPTER_LENGTH = 50


class ChapterPrereadingProcessError(Exception):
    """Raised when processing a chapter fails."""


class PrereadingBatchProcessor:
    """Processes individual chapters to generate prereading content."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.prereading_repo = ChapterPrereadingRepository(db)
        self.file_repo = FileRepository()
        self.text_extraction = EpubTextExtractionService()
        self.usage_repo = AIUsageRepository(db)

    async def process_chapter(
        self,
        chapter_id: ChapterId,
        book_id: BookId,
        user_id: UserId,
        batch_item_id: BatchItemId,
    ) -> ChapterPrereadingContent:
        """Generate prereading content for a single chapter.

        Args:
            chapter_id: The chapter to process.
            book_id: The book this chapter belongs to.
            user_id: The user who owns the book.
            batch_item_id: The batch item tracking this operation (for context).

        Returns:
            The saved ChapterPrereadingContent entity.

        Raises:
            ChapterPrereadingProcessError: If processing fails for any reason.
        """
        log = logger.bind(
            chapter_id=chapter_id.value,
            book_id=book_id.value,
            user_id=user_id.value,
            batch_item_id=batch_item_id.value,
        )

        # 1. Load chapter ORM
        chapter_result = await self.db.execute(
            select(ChapterORM).where(
                ChapterORM.id == chapter_id.value,
                ChapterORM.book_id == book_id.value,
            )
        )
        chapter_orm = chapter_result.scalar_one_or_none()
        if chapter_orm is None:
            raise ChapterPrereadingProcessError(
                f"Chapter {chapter_id.value} not found in book {book_id.value}"
            )

        if not chapter_orm.start_xpoint:
            raise ChapterPrereadingProcessError(
                f"Chapter {chapter_id.value} has no XPoint data; cannot extract text"
            )

        # 2. Load book ORM to verify ownership and file type
        book_result = await self.db.execute(
            select(BookORM).where(
                BookORM.id == book_id.value,
                BookORM.user_id == user_id.value,
            )
        )
        book_orm = book_result.scalar_one_or_none()
        if book_orm is None:
            raise ChapterPrereadingProcessError(
                f"Book {book_id.value} not found for user {user_id.value}"
            )

        if book_orm.file_type != "epub":
            raise ChapterPrereadingProcessError(
                f"Book {book_id.value} is not an EPUB (file_type={book_orm.file_type!r})"
            )

        # 3. Resolve EPUB path
        epub_path = self.file_repo.find_epub(book_id)
        if epub_path is None or not epub_path.exists():
            raise ChapterPrereadingProcessError(
                f"EPUB file not found on disk for book {book_id.value}"
            )

        # 4. Extract chapter text
        try:
            chapter_text = self.text_extraction.extract_chapter_text(
                epub_path=epub_path,
                start_xpoint=chapter_orm.start_xpoint,
                end_xpoint=chapter_orm.end_xpoint,
            )
        except Exception as exc:
            log.error("chapter_text_extraction_failed", error=str(exc))
            raise ChapterPrereadingProcessError(
                f"Failed to extract text for chapter {chapter_id.value}: {exc}"
            ) from exc

        if not chapter_text or len(chapter_text.strip()) < MIN_CHAPTER_LENGTH:
            raise ChapterPrereadingProcessError(
                f"Chapter {chapter_id.value} text is too short for prereading generation"
            )

        # 5. Call AI using the batch model
        try:
            batch_model = get_batch_ai_model()
            agent: Agent[None, PrereadingContent] = Agent(
                batch_model,
                output_type=PrereadingContent,
                instructions="""
                You are helping a reader prepare to read a book chapter.
                Generate pre-reading content to help the reader set expectations and think about
                what they are going to read before they start.

                Generate:
                1. A brief summary (2-3 sentences) of what this chapter covers
                2. 3-5 key points or concepts the reader should watch for in markdown format. Bold the key point name. Do not use bullet points or list markers.

                Focus on helping the reader understand what to expect from the chapter.
                Be concise and specific.
                """,
            )
            ai_result = await agent.run(chapter_text[:10000])
        except Exception as exc:
            log.error("ai_prereading_failed", error=str(exc))
            raise ChapterPrereadingProcessError(
                f"AI generation failed for chapter {chapter_id.value}: {exc}"
            ) from exc

        # 6. Record AI usage
        usage = ai_result.usage()
        model_name = ai_result.response.model_name or "unknown"
        usage_context = AIUsageContext(
            user_id=user_id,
            task_type="prereading",
            entity_type="chapter",
            entity_id=chapter_id.value,
        )
        try:
            await self.usage_repo.save(
                AIUsageRecord.create(
                    user_id=usage_context.user_id,
                    task_type=usage_context.task_type,
                    entity_type=usage_context.entity_type,
                    entity_id=usage_context.entity_id,
                    model_name=model_name,
                    input_tokens=usage.input_tokens or 0,
                    output_tokens=usage.output_tokens or 0,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception as exc:
            # Usage tracking failure is non-fatal
            log.warning("ai_usage_tracking_failed", error=str(exc))

        # 7. Create and save prereading entity
        entity = ChapterPrereadingContent.create(
            chapter_id=chapter_id,
            summary=ai_result.output.summary,
            keypoints=ai_result.output.keypoints,
            generated_at=datetime.now(UTC),
            ai_model=model_name,
        )

        saved = await self.prereading_repo.save(entity)
        log.info(
            "chapter_prereading_generated",
            keypoints_count=len(ai_result.output.keypoints),
            model=model_name,
        )
        return saved
