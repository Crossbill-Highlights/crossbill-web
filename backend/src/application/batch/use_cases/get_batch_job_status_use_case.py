from src.application.batch.protocols.batch_job_repository import (
    BatchJobRepositoryProtocol,
)
from src.domain.batch.entities.batch_job import BatchJob
from src.domain.common.exceptions import EntityNotFoundError
from src.domain.common.value_objects.ids import BatchJobId, UserId


class GetBatchJobStatusUseCase:
    def __init__(self, batch_job_repo: BatchJobRepositoryProtocol) -> None:
        self.batch_job_repo = batch_job_repo

    async def execute(self, user_id: UserId, job_id: BatchJobId) -> BatchJob:
        job = await self.batch_job_repo.get_job(job_id)
        if job is None or job.user_id != user_id:
            raise EntityNotFoundError("BatchJob", job_id.value)
        return job
