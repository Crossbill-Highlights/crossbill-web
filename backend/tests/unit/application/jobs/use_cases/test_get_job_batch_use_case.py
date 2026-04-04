"""Tests for GetJobBatchUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.jobs.use_cases.get_job_batch_use_case import GetJobBatchUseCase
from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType
from src.domain.jobs.exceptions import JobBatchNotFoundError


def _make_batch(batch_id: int = 1) -> JobBatch:
    now = datetime.now(UTC)
    return JobBatch.create_with_id(
        id=JobBatchId(batch_id),
        user_id=UserId(1),
        batch_type=JobBatchType.CHAPTER_PREREADING,
        reference_id="42",
        total_jobs=5,
        completed_jobs=2,
        failed_jobs=0,
        status=JobBatchStatus.RUNNING,
        job_keys=["k1", "k2"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def batch_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(batch_repo: AsyncMock) -> GetJobBatchUseCase:
    return GetJobBatchUseCase(batch_repo=batch_repo)


class TestGetJobBatch:
    async def test_returns_batch(
        self, use_case: GetJobBatchUseCase, batch_repo: AsyncMock
    ) -> None:
        batch_repo.find_by_id.return_value = _make_batch(1)
        result = await use_case.execute(JobBatchId(1), UserId(1))
        assert result.id == JobBatchId(1)

    async def test_raises_when_not_found(
        self, use_case: GetJobBatchUseCase, batch_repo: AsyncMock
    ) -> None:
        batch_repo.find_by_id.return_value = None
        with pytest.raises(JobBatchNotFoundError):
            await use_case.execute(JobBatchId(999), UserId(1))
