from dataclasses import dataclass, field

import pytest

from src.application.batch.use_cases.cancel_batch_job_use_case import (
    CancelBatchJobUseCase,
)
from src.application.batch.use_cases.get_batch_job_status_use_case import (
    GetBatchJobStatusUseCase,
)
from src.domain.batch.entities.batch_item import BatchItem
from src.domain.batch.entities.batch_job import BatchJob, BatchJobStatus
from src.domain.common.exceptions import BusinessRuleViolationError, EntityNotFoundError
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    UserId,
)


@dataclass
class FakeBatchJobRepository:
    jobs: dict[int, BatchJob] = field(default_factory=dict)

    async def save_job(self, job: BatchJob) -> BatchJob:
        self.jobs[job.id.value] = job
        return job

    async def save_item(self, item: BatchItem) -> BatchItem:
        return item

    async def save_items(self, items: list[BatchItem]) -> list[BatchItem]:
        return items

    async def get_job(self, job_id: BatchJobId) -> BatchJob | None:
        return self.jobs.get(job_id.value)

    async def get_job_items(self, job_id: BatchJobId) -> list[BatchItem]:
        return []

    async def get_pending_items(self, job_id: BatchJobId) -> list[BatchItem]:
        return []

    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> BatchJob | None:
        return None


@dataclass
class FakeBatchQueueService:
    cancelled_jobs: list[BatchJobId] = field(default_factory=list)

    async def enqueue_job(self, job_id: BatchJobId) -> None:
        pass

    async def cancel_job(self, job_id: BatchJobId) -> None:
        self.cancelled_jobs.append(job_id)


def _make_job(
    job_id: int = 1,
    user_id: int = 1,
    status: BatchJobStatus = BatchJobStatus.PROCESSING,
) -> BatchJob:
    job = BatchJob.create(
        user_id=UserId(user_id),
        book_id=BookId(5),
        job_type="prereading",
        total_items=10,
    )
    job.id = BatchJobId(job_id)
    job.status = status
    return job


class TestGetBatchJobStatus:
    async def test_returns_job_status(self) -> None:
        repo = FakeBatchJobRepository()
        job = _make_job()
        await repo.save_job(job)

        use_case = GetBatchJobStatusUseCase(batch_job_repo=repo)
        result = await use_case.execute(user_id=UserId(1), job_id=BatchJobId(1))

        assert result.id == BatchJobId(1)
        assert result.status == BatchJobStatus.PROCESSING

    async def test_raises_not_found_for_missing_job(self) -> None:
        repo = FakeBatchJobRepository()
        use_case = GetBatchJobStatusUseCase(batch_job_repo=repo)

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(user_id=UserId(1), job_id=BatchJobId(999))

    async def test_raises_not_found_for_other_users_job(self) -> None:
        repo = FakeBatchJobRepository()
        job = _make_job(user_id=2)  # belongs to user 2
        await repo.save_job(job)

        use_case = GetBatchJobStatusUseCase(batch_job_repo=repo)

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                user_id=UserId(1),
                job_id=BatchJobId(1),  # user 1 asking
            )


class TestCancelBatchJob:
    async def test_cancels_processing_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.PROCESSING)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(batch_job_repo=repo, batch_queue_service=queue)
        result = await use_case.execute(user_id=UserId(1), job_id=BatchJobId(1))

        assert result.status == BatchJobStatus.CANCELLED
        assert len(queue.cancelled_jobs) == 1

    async def test_cancels_pending_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.PENDING)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(batch_job_repo=repo, batch_queue_service=queue)
        result = await use_case.execute(user_id=UserId(1), job_id=BatchJobId(1))

        assert result.status == BatchJobStatus.CANCELLED

    async def test_raises_error_for_already_completed_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.COMPLETED)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(batch_job_repo=repo, batch_queue_service=queue)

        with pytest.raises(BusinessRuleViolationError, match="already completed|Cannot cancel"):
            await use_case.execute(user_id=UserId(1), job_id=BatchJobId(1))
