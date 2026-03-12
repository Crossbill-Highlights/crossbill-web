from dataclasses import dataclass, field

import pytest

from src.application.batch.use_cases.create_batch_prereading_use_case import (
    CreateBatchPrereadingUseCase,
)
from src.domain.batch.entities.batch_item import BatchItem
from src.domain.batch.entities.batch_job import BatchJob, BatchJobStatus
from src.domain.common.exceptions import BusinessRuleViolationError, DomainError
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    ChapterId,
    UserId,
)


# Fake repository for testing
@dataclass
class FakeBatchJobRepository:
    saved_jobs: list[BatchJob] = field(default_factory=list)
    saved_items: list[BatchItem] = field(default_factory=list)
    active_job: BatchJob | None = None
    _next_job_id: int = 1
    _next_item_id: int = 1

    async def save_job(self, job: BatchJob) -> BatchJob:
        if job.id.value == 0:
            job.id = BatchJobId(self._next_job_id)
            self._next_job_id += 1
        self.saved_jobs.append(job)
        return job

    async def save_item(self, item: BatchItem) -> BatchItem:
        if item.id.value == 0:
            item.id = BatchItemId(self._next_item_id)
            self._next_item_id += 1
        self.saved_items.append(item)
        return item

    async def save_items(self, items: list[BatchItem]) -> list[BatchItem]:
        result = []
        for item in items:
            result.append(await self.save_item(item))
        return result

    async def get_job(self, job_id: BatchJobId) -> BatchJob | None:
        return next((j for j in self.saved_jobs if j.id == job_id), None)

    async def get_job_items(self, job_id: BatchJobId) -> list[BatchItem]:
        return [i for i in self.saved_items if i.batch_job_id == job_id]

    async def get_pending_items(self, job_id: BatchJobId) -> list[BatchItem]:
        return [
            i for i in self.saved_items if i.batch_job_id == job_id and i.status.value == "pending"
        ]

    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> BatchJob | None:
        return self.active_job


@dataclass
class FakeBatchQueueService:
    enqueued_jobs: list[BatchJobId] = field(default_factory=list)
    cancelled_jobs: list[BatchJobId] = field(default_factory=list)

    async def enqueue_job(self, job_id: BatchJobId) -> None:
        self.enqueued_jobs.append(job_id)

    async def cancel_job(self, job_id: BatchJobId) -> None:
        self.cancelled_jobs.append(job_id)


@dataclass
class FakeChapterInfo:
    """Minimal chapter info for testing."""

    chapter_id: ChapterId
    has_prereading: bool


@dataclass
class FakeChapterProvider:
    """Provides chapter IDs that need prereading."""

    chapters: list[FakeChapterInfo] = field(default_factory=list)

    async def get_chapter_ids_needing_prereading(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterId]:
        return [c.chapter_id for c in self.chapters if not c.has_prereading]


async def test_creates_job_and_items_for_chapters_needing_prereading() -> None:
    repo = FakeBatchJobRepository()
    queue = FakeBatchQueueService()
    chapter_provider = FakeChapterProvider(
        chapters=[
            FakeChapterInfo(ChapterId(1), has_prereading=False),
            FakeChapterInfo(ChapterId(2), has_prereading=True),  # already has prereading
            FakeChapterInfo(ChapterId(3), has_prereading=False),
        ]
    )

    use_case = CreateBatchPrereadingUseCase(
        batch_job_repo=repo,
        batch_queue_service=queue,
        chapter_provider=chapter_provider,
    )

    job = await use_case.execute(user_id=UserId(1), book_id=BookId(5))

    assert job.status == BatchJobStatus.PENDING
    assert job.job_type == "prereading"
    assert job.total_items == 2  # only 2 chapters need prereading
    assert job.book_id == BookId(5)
    assert len(repo.saved_items) == 2
    assert repo.saved_items[0].entity_type == "chapter"
    assert repo.saved_items[0].entity_id == 1
    assert repo.saved_items[1].entity_id == 3
    assert len(queue.enqueued_jobs) == 1


async def test_raises_error_when_active_job_exists() -> None:
    repo = FakeBatchJobRepository()
    repo.active_job = BatchJob.create(
        user_id=UserId(1), book_id=BookId(5), job_type="prereading", total_items=5
    )
    queue = FakeBatchQueueService()
    chapter_provider = FakeChapterProvider()

    use_case = CreateBatchPrereadingUseCase(
        batch_job_repo=repo,
        batch_queue_service=queue,
        chapter_provider=chapter_provider,
    )

    with pytest.raises(BusinessRuleViolationError, match="already running"):
        await use_case.execute(user_id=UserId(1), book_id=BookId(5))


async def test_raises_error_when_no_chapters_need_prereading() -> None:
    repo = FakeBatchJobRepository()
    queue = FakeBatchQueueService()
    chapter_provider = FakeChapterProvider(
        chapters=[
            FakeChapterInfo(ChapterId(1), has_prereading=True),
            FakeChapterInfo(ChapterId(2), has_prereading=True),
        ]
    )

    use_case = CreateBatchPrereadingUseCase(
        batch_job_repo=repo,
        batch_queue_service=queue,
        chapter_provider=chapter_provider,
    )

    with pytest.raises(DomainError, match="No chapters"):
        await use_case.execute(user_id=UserId(1), book_id=BookId(5))
