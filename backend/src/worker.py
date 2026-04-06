"""SAQ worker entrypoint.

Start with: saq src.worker.worker_settings
"""

import os

import boto3
import structlog
from saq.types import Context, SettingsDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

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
from src.infrastructure.library.repositories.s3_file_repository import S3FileRepository
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)

logger = structlog.get_logger(__name__)

app_settings = get_settings()
queue = create_queue(app_settings.DATABASE_URL)

_session_factory: async_sessionmaker[AsyncSession] | None = None


def _build_file_repo() -> S3FileRepository | FileRepository:
    """Build the appropriate file repository based on config."""
    if app_settings.s3_enabled:
        client = boto3.client(
            "s3",
            endpoint_url=app_settings.S3_ENDPOINT_URL,
            aws_access_key_id=app_settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=app_settings.S3_SECRET_ACCESS_KEY,
            region_name=app_settings.S3_REGION,
        )
        return S3FileRepository(s3_client=client, bucket_name=app_settings.S3_BUCKET_NAME)  # type: ignore[arg-type]
    return FileRepository()


def _build_prereading_handler(db: AsyncSession) -> PrereadingTaskHandler:
    """Build a PrereadingTaskHandler with a fresh session."""
    from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (  # noqa: PLC0415
        GenerateChapterPrereadingUseCase,
    )

    use_case = GenerateChapterPrereadingUseCase(
        prereading_repo=ChapterPrereadingRepository(db=db),
        chapter_repo=ChapterRepository(db=db),
        text_extraction_service=EpubTextExtractionService(),
        book_repo=BookRepository(db=db),
        file_repo=_build_file_repo(),
        ai_prereading_service=AIService(usage_repository=AIUsageRepository(db=db)),
    )
    return PrereadingTaskHandler(generate_prereading_use_case=use_case)


async def startup(ctx: Context) -> None:
    """Initialize worker resources."""
    logger.info("worker_starting")
    initialize_database(app_settings)

    global _session_factory  # noqa: PLW0603
    _session_factory = get_session_factory(app_settings)

    logger.info("worker_started")


async def shutdown(ctx: Context) -> None:
    """Cleanup worker resources."""
    logger.info("worker_shutting_down")
    logger.info("worker_stopped")


async def generate_chapter_prereading(
    ctx: Context, *, batch_id: int, book_id: int, chapter_id: int, user_id: int
) -> None:
    """SAQ task: generate prereading for a single chapter.

    Creates a fresh DB session per task invocation to avoid sharing
    sessions across concurrent coroutines.
    """
    if _session_factory is None:
        raise RuntimeError("Worker not initialized")

    async with _session_factory() as db:
        handler = _build_prereading_handler(db)
        await handler.generate(
            ctx, batch_id=batch_id, book_id=book_id, chapter_id=chapter_id, user_id=user_id
        )


async def after_process(ctx: Context) -> None:
    """SAQ after_process hook: update batch progress.

    Creates a fresh DB session to avoid sharing with task coroutines.
    """
    if _session_factory is None:
        raise RuntimeError("Worker not initialized")

    async with _session_factory() as db:
        handler = JobLifecycleHandler(batch_repo=JobBatchRepository(db=db))
        await handler.after_process(ctx)


worker_settings: SettingsDict[Context] = {
    "queue": queue,
    "functions": [generate_chapter_prereading],
    "concurrency": int(os.getenv("WORKER_CONCURRENCY", "5")),
    "startup": startup,
    "shutdown": shutdown,
    "after_process": after_process,
}
