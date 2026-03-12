"""SAQ worker for batch AI processing.

Run with:
    uv run saq src.infrastructure.batch.worker.settings
"""

import asyncio
from datetime import UTC, datetime

import structlog
from saq import Queue
from saq.types import Context, SettingsDict
from sqlalchemy import select, update

from src.config import get_settings
from src.database import dispose_engine, get_session_factory, initialize_database
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import BatchItemId, BatchJobId, BookId, ChapterId, UserId
from src.infrastructure.batch.processors.prereading_batch_processor import (
    ChapterPrereadingProcessError,
    PrereadingBatchProcessor,
)
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM

logger = structlog.get_logger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Global semaphore — initialised in startup
# ──────────────────────────────────────────────────────────────────────────────

_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    if _semaphore is None:
        raise RuntimeError("Worker not started; semaphore not initialised")
    return _semaphore


# ──────────────────────────────────────────────────────────────────────────────
# Lifecycle hooks
# ──────────────────────────────────────────────────────────────────────────────


async def startup(ctx: Context) -> None:
    """Initialise database and semaphore once on worker start."""
    global _semaphore  # noqa: PLW0603
    settings = get_settings()
    initialize_database(settings)
    _semaphore = asyncio.Semaphore(settings.BATCH_MAX_CONCURRENCY)
    logger.info(
        "batch_worker_started",
        concurrency=settings.BATCH_MAX_CONCURRENCY,
    )


async def shutdown(ctx: Context) -> None:
    """Tear down database connections on worker stop."""
    dispose_engine()
    logger.info("batch_worker_stopped")


# ──────────────────────────────────────────────────────────────────────────────
# Task: process_prereading_job
# ──────────────────────────────────────────────────────────────────────────────

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 5.0


async def _process_single_item(
    chapter_id: ChapterId,
    book_id: BookId,
    user_id: UserId,
    item_id: BatchItemId,
    job_id: BatchJobId,
) -> bool:
    """Process a single prereading item. Returns True on success, False on failure."""
    settings = get_settings()
    session_factory = get_session_factory(settings)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session_factory() as db:
                # Mark item as processing
                await db.execute(
                    update(BatchItemORM)
                    .where(BatchItemORM.id == item_id.value)
                    .values(
                        status=BatchItemStatus.PROCESSING.value,
                        attempts=attempt,
                    )
                )
                await db.commit()

            async with session_factory() as db:
                processor = PrereadingBatchProcessor(db)
                await processor.process_chapter(
                    chapter_id=chapter_id,
                    book_id=book_id,
                    user_id=user_id,
                    batch_item_id=item_id,
                )

            async with session_factory() as db:
                # Mark item as succeeded and atomically increment completed_items
                await db.execute(
                    update(BatchItemORM)
                    .where(BatchItemORM.id == item_id.value)
                    .values(
                        status=BatchItemStatus.SUCCEEDED.value,
                        completed_at=datetime.now(UTC),
                    )
                )
                await db.execute(
                    update(BatchJobORM)
                    .where(BatchJobORM.id == job_id.value)
                    .values(
                        completed_items=BatchJobORM.completed_items + 1,  # type: ignore[operator]
                    )
                )
                await db.commit()

            logger.info(
                "batch_item_succeeded",
                item_id=item_id.value,
                chapter_id=chapter_id.value,
                attempt=attempt,
            )
            return True

        except ChapterPrereadingProcessError as exc:
            # Non-retryable domain error — mark failed immediately
            logger.warning(
                "batch_item_failed_domain",
                item_id=item_id.value,
                chapter_id=chapter_id.value,
                error=str(exc),
            )
            async with session_factory() as db:
                await db.execute(
                    update(BatchItemORM)
                    .where(BatchItemORM.id == item_id.value)
                    .values(
                        status=BatchItemStatus.FAILED.value,
                        error_message=str(exc),
                        completed_at=datetime.now(UTC),
                    )
                )
                await db.execute(
                    update(BatchJobORM)
                    .where(BatchJobORM.id == job_id.value)
                    .values(
                        failed_items=BatchJobORM.failed_items + 1,  # type: ignore[operator]
                    )
                )
                await db.commit()
            return False

        except Exception as exc:
            if attempt < MAX_RETRIES:
                backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "batch_item_retrying",
                    item_id=item_id.value,
                    chapter_id=chapter_id.value,
                    attempt=attempt,
                    backoff=backoff,
                    error=str(exc),
                )
                await asyncio.sleep(backoff)
            else:
                logger.error(
                    "batch_item_failed_exhausted",
                    item_id=item_id.value,
                    chapter_id=chapter_id.value,
                    error=str(exc),
                )
                async with session_factory() as db:
                    await db.execute(
                        update(BatchItemORM)
                        .where(BatchItemORM.id == item_id.value)
                        .values(
                            status=BatchItemStatus.FAILED.value,
                            error_message=str(exc),
                            completed_at=datetime.now(UTC),
                        )
                    )
                    await db.execute(
                        update(BatchJobORM)
                        .where(BatchJobORM.id == job_id.value)
                        .values(
                            failed_items=BatchJobORM.failed_items + 1,  # type: ignore[operator]
                        )
                    )
                    await db.commit()
                return False

    return False  # unreachable, but satisfies type checker


async def process_prereading_job(ctx: Context, *, job_id: int) -> None:
    """SAQ task: process all pending items for a batch prereading job.

    Args:
        ctx: SAQ context (not used directly).
        job_id: The BatchJob primary key.
    """
    settings = get_settings()
    session_factory = get_session_factory(settings)
    batch_job_id = BatchJobId(job_id)

    log = logger.bind(job_id=job_id)
    log.info("batch_job_processing_started")

    # Mark job as processing
    async with session_factory() as db:
        result = await db.execute(
            update(BatchJobORM)
            .where(BatchJobORM.id == job_id)
            .values(status=BatchJobStatus.PROCESSING.value)
            .returning(BatchJobORM.user_id, BatchJobORM.book_id)
        )
        row = result.one_or_none()
        await db.commit()

    if row is None:
        log.error("batch_job_not_found")
        return

    user_id = UserId(row.user_id)
    book_id = BookId(row.book_id)

    # Load all pending items
    async with session_factory() as db:
        items_result = await db.execute(
            select(BatchItemORM).where(
                BatchItemORM.batch_job_id == job_id,
                BatchItemORM.status == BatchItemStatus.PENDING.value,
            )
        )
        pending_items = items_result.scalars().all()

    log.info("batch_job_items_loaded", total_pending=len(pending_items))

    semaphore = _get_semaphore()

    async def process_with_semaphore(item: BatchItemORM) -> None:
        chapter_id = ChapterId(item.entity_id)
        item_id = BatchItemId(item.id)

        # Acquire semaphore then process
        async with semaphore:
            await _process_single_item(
                chapter_id=chapter_id,
                book_id=book_id,
                user_id=user_id,
                item_id=item_id,
                job_id=batch_job_id,
            )

    # Run all items concurrently, bounded by semaphore
    await asyncio.gather(*[process_with_semaphore(item) for item in pending_items])

    # Determine final job status
    async with session_factory() as db:
        job_result = await db.execute(select(BatchJobORM).where(BatchJobORM.id == job_id))
        job_orm = job_result.scalar_one_or_none()

    if job_orm is None:
        log.error("batch_job_missing_after_processing")
        return

    if job_orm.failed_items == job_orm.total_items:
        final_status = BatchJobStatus.FAILED.value
    else:
        final_status = BatchJobStatus.COMPLETED.value

    async with session_factory() as db:
        await db.execute(
            update(BatchJobORM)
            .where(BatchJobORM.id == job_id)
            .values(
                status=final_status,
                completed_at=datetime.now(UTC),
            )
        )
        await db.commit()

    log.info(
        "batch_job_processing_finished",
        final_status=final_status,
        completed_items=job_orm.completed_items,
        failed_items=job_orm.failed_items,
    )


# ──────────────────────────────────────────────────────────────────────────────
# SAQ settings dict (used by `saq src.infrastructure.batch.worker.settings`)
# ──────────────────────────────────────────────────────────────────────────────


def _build_queue() -> Queue:
    _settings = get_settings()
    # SAQ Postgres queue uses psycopg3; it accepts standard postgresql:// URLs
    db_url = _settings.DATABASE_URL
    return Queue.from_url(db_url, name="batch")


settings: SettingsDict[Context] = {
    "queue": _build_queue(),
    "functions": [process_prereading_job],
    "concurrency": 1,  # SAQ-level concurrency (we handle our own via semaphore)
    "startup": startup,
    "shutdown": shutdown,
}
