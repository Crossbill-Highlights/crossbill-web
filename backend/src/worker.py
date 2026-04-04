"""SAQ worker entrypoint.

Start with: saq src.worker.worker_settings
"""

import os

import structlog
from saq.types import Context, SettingsDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (
    GenerateChapterPrereadingUseCase,
)
from src.config import get_settings
from src.database import get_session_factory, initialize_database
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.jobs.repositories.job_batch_repository import JobBatchRepository
from src.infrastructure.jobs.saq_queue import create_queue
from src.infrastructure.jobs.tasks.job_lifecycle_handler import JobLifecycleHandler
from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)

logger = structlog.get_logger(__name__)

app_settings = get_settings()
queue = create_queue(app_settings.DATABASE_URL)

_prereading_handler: PrereadingTaskHandler | None = None
_lifecycle_handler: JobLifecycleHandler | None = None


async def startup(ctx: Context) -> None:
    """Initialize worker resources."""
    logger.info("worker_starting")
    initialize_database(app_settings)

    session_factory = get_session_factory(app_settings)
    db = session_factory()
    ctx["db"] = db  # type: ignore[typeddict-unknown-key]

    ai_usage_repo = AIUsageRepository(db=db)
    ai_service = AIService(usage_repository=ai_usage_repo)
    book_repo = BookRepository(db=db)
    chapter_repo = ChapterRepository(db=db)
    prereading_repo = ChapterPrereadingRepository(db=db)
    file_repo = FileRepository()
    text_extraction = EpubTextExtractionService()
    batch_repo = JobBatchRepository(db=db)

    use_case = GenerateChapterPrereadingUseCase(
        prereading_repo=prereading_repo,
        chapter_repo=chapter_repo,
        text_extraction_service=text_extraction,
        book_repo=book_repo,
        file_repo=file_repo,
        ai_prereading_service=ai_service,
    )

    global _prereading_handler, _lifecycle_handler  # noqa: PLW0603
    _prereading_handler = PrereadingTaskHandler(generate_prereading_use_case=use_case)
    _lifecycle_handler = JobLifecycleHandler(batch_repo=batch_repo)

    logger.info("worker_started")


async def shutdown(ctx: Context) -> None:
    """Cleanup worker resources."""
    logger.info("worker_shutting_down")
    db: AsyncSession | None = ctx.get("db")  # type: ignore[assignment]
    if db:
        await db.close()
    logger.info("worker_stopped")


async def generate_chapter_prereading(
    ctx: Context, *, batch_id: int, book_id: int, chapter_id: int, user_id: int
) -> None:
    """SAQ task: generate prereading for a single chapter."""
    assert _prereading_handler is not None, "Worker not initialized"
    await _prereading_handler.generate(
        ctx, batch_id=batch_id, book_id=book_id, chapter_id=chapter_id, user_id=user_id
    )


async def after_process(ctx: Context) -> None:
    """SAQ after_process hook: update batch progress."""
    assert _lifecycle_handler is not None, "Worker not initialized"
    await _lifecycle_handler.after_process(ctx)


worker_settings: SettingsDict[Context] = {
    "queue": queue,
    "functions": [generate_chapter_prereading],
    "concurrency": int(os.getenv("WORKER_CONCURRENCY", "5")),
    "startup": startup,
    "shutdown": shutdown,
    "after_process": after_process,
}
