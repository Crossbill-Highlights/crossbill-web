"""Use case for retrieving a job batch."""

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch
from src.domain.jobs.exceptions import JobBatchNotFoundError


class GetJobBatchUseCase:
    def __init__(self, batch_repo: JobBatchRepositoryProtocol) -> None:
        self._batch_repo = batch_repo

    async def execute(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch:
        batch = await self._batch_repo.find_by_id(batch_id, user_id)
        if not batch:
            raise JobBatchNotFoundError(batch_id.value)
        return batch
