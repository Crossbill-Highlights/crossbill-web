import structlog

from src.application.batch.protocols.batch_job_repository import (
    BatchJobRepositoryProtocol,
)
from src.application.batch.protocols.batch_queue_service import (
    BatchQueueServiceProtocol,
)
from src.application.batch.protocols.chapter_prereading_provider import (
    ChapterPrereadingProviderProtocol,
)
from src.domain.batch.entities.batch_item import BatchItem
from src.domain.batch.entities.batch_job import BatchJob
from src.domain.common.exceptions import BusinessRuleViolationError, DomainError
from src.domain.common.value_objects.ids import BookId, UserId

logger = structlog.get_logger()


class CreateBatchPrereadingUseCase:
    def __init__(
        self,
        batch_job_repo: BatchJobRepositoryProtocol,
        batch_queue_service: BatchQueueServiceProtocol,
        chapter_provider: ChapterPrereadingProviderProtocol,
    ) -> None:
        self.batch_job_repo = batch_job_repo
        self.batch_queue_service = batch_queue_service
        self.chapter_provider = chapter_provider

    async def execute(self, user_id: UserId, book_id: BookId) -> BatchJob:
        # Check for existing active job
        active_job = await self.batch_job_repo.find_active_job(user_id, book_id, "prereading")
        if active_job is not None:
            raise BusinessRuleViolationError(
                "batch_job_already_active",
                "A prereading batch job is already running for this book",
            )

        # Determine which chapters need prereading
        chapter_ids = await self.chapter_provider.get_chapter_ids_needing_prereading(
            book_id, user_id
        )
        if not chapter_ids:
            raise DomainError("No chapters need prereading generation in this book")

        # Create batch job
        job = BatchJob.create(
            user_id=user_id,
            book_id=book_id,
            job_type="prereading",
            total_items=len(chapter_ids),
        )
        job = await self.batch_job_repo.save_job(job)

        # Create batch items for each chapter
        items = [
            BatchItem.create(
                batch_job_id=job.id,
                entity_type="chapter",
                entity_id=chapter_id.value,
            )
            for chapter_id in chapter_ids
        ]
        await self.batch_job_repo.save_items(items)

        # Enqueue for background processing
        await self.batch_queue_service.enqueue_job(job.id)

        logger.info(
            "batch_prereading_job_created",
            job_id=job.id.value,
            book_id=book_id.value,
            total_items=len(chapter_ids),
        )

        return job
