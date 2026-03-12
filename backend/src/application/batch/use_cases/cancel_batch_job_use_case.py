import structlog

from src.application.batch.protocols.batch_job_repository import (
    BatchJobRepositoryProtocol,
)
from src.application.batch.protocols.batch_queue_service import (
    BatchQueueServiceProtocol,
)
from src.domain.batch.entities.batch_job import BatchJob, BatchJobStatus
from src.domain.common.exceptions import (
    BusinessRuleViolationError,
    EntityNotFoundError,
)
from src.domain.common.value_objects.ids import BatchJobId, UserId

logger = structlog.get_logger()


class CancelBatchJobUseCase:
    def __init__(
        self,
        batch_job_repo: BatchJobRepositoryProtocol,
        batch_queue_service: BatchQueueServiceProtocol,
    ) -> None:
        self.batch_job_repo = batch_job_repo
        self.batch_queue_service = batch_queue_service

    async def execute(self, user_id: UserId, job_id: BatchJobId) -> BatchJob:
        job = await self.batch_job_repo.get_job(job_id)
        if job is None or job.user_id != user_id:
            raise EntityNotFoundError("BatchJob", job_id.value)

        if job.status not in (BatchJobStatus.PENDING, BatchJobStatus.PROCESSING):
            raise BusinessRuleViolationError(
                "job_already_terminal",
                "Cannot cancel a job that is already completed or cancelled",
            )

        job.status = BatchJobStatus.CANCELLED
        job = await self.batch_job_repo.save_job(job)
        await self.batch_queue_service.cancel_job(job_id)

        logger.info("batch_job_cancelled", job_id=job_id.value)

        return job
