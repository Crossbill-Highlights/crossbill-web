"""Tests for JobLifecycleHandler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType
from src.infrastructure.jobs.tasks.job_lifecycle_handler import JobLifecycleHandler


def _make_batch(batch_id: int = 1, total: int = 3) -> JobBatch:
    now = datetime.now(UTC)
    return JobBatch.create_with_id(
        id=JobBatchId(batch_id),
        user_id=UserId(1),
        batch_type=JobBatchType.CHAPTER_PREREADING,
        reference_id="42",
        total_jobs=total,
        completed_jobs=0,
        failed_jobs=0,
        status=JobBatchStatus.PENDING,
        job_keys=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def batch_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(batch_repo: AsyncMock) -> JobLifecycleHandler:
    return JobLifecycleHandler(batch_repo=batch_repo)


class TestAfterProcess:
    async def test_marks_completed_on_success(
        self, handler: JobLifecycleHandler, batch_repo: AsyncMock
    ) -> None:
        batch = _make_batch()
        batch_repo.find_by_id_internal.return_value = batch
        batch_repo.save.side_effect = lambda b: b

        job = MagicMock()
        job.status = "complete"
        job.kwargs = {"batch_id": 1}

        await handler.after_process({}, job)

        assert batch.completed_jobs == 1
        batch_repo.save.assert_called_once()

    async def test_marks_failed_on_failure(
        self, handler: JobLifecycleHandler, batch_repo: AsyncMock
    ) -> None:
        batch = _make_batch()
        batch_repo.find_by_id_internal.return_value = batch
        batch_repo.save.side_effect = lambda b: b

        job = MagicMock()
        job.status = "failed"
        job.kwargs = {"batch_id": 1}

        await handler.after_process({}, job)

        assert batch.failed_jobs == 1
        batch_repo.save.assert_called_once()

    async def test_skips_jobs_without_batch_id(
        self, handler: JobLifecycleHandler, batch_repo: AsyncMock
    ) -> None:
        job = MagicMock()
        job.kwargs = {"some_other_key": "value"}

        await handler.after_process({}, job)

        batch_repo.find_by_id_internal.assert_not_called()

    async def test_skips_non_terminal_status(
        self, handler: JobLifecycleHandler, batch_repo: AsyncMock
    ) -> None:
        job = MagicMock()
        job.status = "active"
        job.kwargs = {"batch_id": 1}

        await handler.after_process({}, job)

        batch_repo.find_by_id_internal.assert_not_called()
