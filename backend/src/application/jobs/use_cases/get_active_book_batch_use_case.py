"""Use case for finding an active job batch for a book."""

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType

_ACTIVE_STATUSES = {JobBatchStatus.PENDING, JobBatchStatus.RUNNING}


class GetActiveBookBatchUseCase:
    def __init__(self, batch_repo: JobBatchRepositoryProtocol) -> None:
        self._batch_repo = batch_repo

    async def execute(
        self, book_id: BookId, user_id: UserId, batch_type: JobBatchType
    ) -> JobBatch | None:
        batches = await self._batch_repo.find_by_reference(
            batch_type=batch_type.value,
            reference_id=str(book_id.value),
            user_id=user_id,
        )
        for batch in batches:
            if batch.status in _ACTIVE_STATUSES:
                return batch
        return None
