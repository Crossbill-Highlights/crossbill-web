# Background Job Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a background job queue system using SAQ with Postgres backend, enabling async multi-part jobs like batch prereading generation for all chapters of a book.

**Architecture:** A new `jobs` subdomain follows the existing DDD structure. SAQ handles queue mechanics (enqueue, dequeue, retry, abort) using the existing Postgres database. A `JobBatch` domain entity tracks groups of related SAQ jobs. A separate worker process (same Docker image, different entrypoint) consumes jobs. Task handler classes receive dependencies via DI at worker startup.

**Tech Stack:** SAQ (Postgres backend), dependency-injector, SQLAlchemy async, Alembic, FastAPI

---

## File Structure

### Domain Layer (`src/domain/jobs/`)
- `src/domain/jobs/__init__.py` — module init
- `src/domain/jobs/entities/__init__.py` — entities init
- `src/domain/jobs/entities/job_batch.py` — `JobBatch` entity, `JobBatchStatus` enum, `JobBatchType` enum
- `src/domain/jobs/exceptions.py` — `JobBatchNotFoundError`

### Application Layer (`src/application/jobs/`)
- `src/application/jobs/__init__.py` — module init
- `src/application/jobs/protocols/__init__.py` — protocols init
- `src/application/jobs/protocols/job_batch_repository.py` — `JobBatchRepositoryProtocol`
- `src/application/jobs/protocols/job_queue_service.py` — `JobQueueServiceProtocol`
- `src/application/jobs/use_cases/__init__.py` — use cases init
- `src/application/jobs/use_cases/enqueue_book_prereading_use_case.py` — creates batch + enqueues SAQ jobs
- `src/application/jobs/use_cases/get_job_batch_use_case.py` — fetches batch status
- `src/application/jobs/use_cases/cancel_job_batch_use_case.py` — aborts all jobs in a batch

### Infrastructure Layer (`src/infrastructure/jobs/`)
- `src/infrastructure/jobs/__init__.py` — module init
- `src/infrastructure/jobs/orm/__init__.py` — orm init
- `src/infrastructure/jobs/orm/job_batch_model.py` — SQLAlchemy ORM model
- `src/infrastructure/jobs/repositories/__init__.py` — repositories init
- `src/infrastructure/jobs/repositories/job_batch_repository.py` — implements `JobBatchRepositoryProtocol`
- `src/infrastructure/jobs/mappers/__init__.py` — mappers init
- `src/infrastructure/jobs/mappers/job_batch_mapper.py` — ORM-to-domain mapper
- `src/infrastructure/jobs/saq_queue.py` — SAQ queue factory
- `src/infrastructure/jobs/saq_job_queue_service.py` — implements `JobQueueServiceProtocol`
- `src/infrastructure/jobs/tasks/__init__.py` — tasks init
- `src/infrastructure/jobs/tasks/prereading_task_handler.py` — SAQ task for chapter prereading
- `src/infrastructure/jobs/tasks/job_lifecycle_handler.py` — after_process hook updating JobBatch
- `src/infrastructure/jobs/routers/__init__.py` — routers init
- `src/infrastructure/jobs/routers/job_batches.py` — REST endpoints for job batches
- `src/infrastructure/jobs/schemas/__init__.py` — schemas init
- `src/infrastructure/jobs/schemas/job_batch_schemas.py` — Pydantic response schemas

### DI and Worker
- Modify: `src/domain/common/value_objects/ids.py` — add `JobBatchId`
- Modify: `src/containers/shared.py` — add job batch repository
- Create: `src/containers/jobs.py` — `JobsContainer` with job use cases
- Modify: `src/containers/root.py` — wire `JobsContainer`
- Create: `src/worker.py` — SAQ worker settings and entrypoint
- Modify: `src/main.py` — register job routers, connect/disconnect SAQ queue in lifespan
- Modify: `src/models.py` — add `JobBatchModel` import for alembic metadata

### Migration
- Create: `alembic/versions/049_create_job_batches_table.py`

### Docker
- Modify: `docker-compose.yml` — add worker service

### Dependencies
- Modify: `pyproject.toml` — add `saq[postgres]`

### Tests
- `tests/unit/domain/jobs/__init__.py`
- `tests/unit/domain/jobs/entities/__init__.py`
- `tests/unit/domain/jobs/entities/test_job_batch.py`
- `tests/unit/application/jobs/__init__.py`
- `tests/unit/application/jobs/use_cases/__init__.py`
- `tests/unit/application/jobs/use_cases/test_enqueue_book_prereading_use_case.py`
- `tests/unit/application/jobs/use_cases/test_get_job_batch_use_case.py`
- `tests/unit/application/jobs/use_cases/test_cancel_job_batch_use_case.py`
- `tests/unit/infrastructure/jobs/__init__.py`
- `tests/unit/infrastructure/jobs/tasks/__init__.py`
- `tests/unit/infrastructure/jobs/tasks/test_prereading_task_handler.py`
- `tests/unit/infrastructure/jobs/tasks/test_job_lifecycle_handler.py`

---

## Task 1: Add SAQ Dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add saq[postgres] to dependencies**

In `pyproject.toml`, add to the `dependencies` list:

```toml
  "saq[postgres]>=0.22.0,<1.0.0",
```

Add it after the `dependency-injector` line (line 25).

- [ ] **Step 2: Install dependencies**

Run:
```bash
cd backend && uv lock && uv sync
```

Expected: Lock file updated, saq installed successfully.

- [ ] **Step 3: Verify SAQ is importable**

Run:
```bash
cd backend && uv run python -c "from saq import Queue; print('SAQ OK')"
```

Expected: `SAQ OK`

- [ ] **Step 4: Commit**

```bash
cd backend && git add pyproject.toml uv.lock
git commit -m "chore: add saq[postgres] dependency for background job queue"
```

---

## Task 2: Domain Layer — JobBatchId Value Object

**Files:**
- Modify: `src/domain/common/value_objects/ids.py`
- Test: `tests/unit/domain/jobs/entities/test_job_batch.py` (created in Task 3)

- [ ] **Step 1: Add JobBatchId to ids.py**

Add at the end of `src/domain/common/value_objects/ids.py`:

```python
@dataclass(frozen=True)
class JobBatchId(EntityId):
    """Strongly-typed job batch identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("JobBatchId must be non-negative")

    @classmethod
    def generate(cls) -> "JobBatchId":
        return cls(0)  # Database assigns real ID
```

- [ ] **Step 2: Verify types**

Run:
```bash
cd backend && uv run pyright src/domain/common/value_objects/ids.py
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add src/domain/common/value_objects/ids.py
git commit -m "feat: add JobBatchId value object"
```

---

## Task 3: Domain Layer — JobBatch Entity and Exceptions

**Files:**
- Create: `src/domain/jobs/__init__.py`
- Create: `src/domain/jobs/entities/__init__.py`
- Create: `src/domain/jobs/entities/job_batch.py`
- Create: `src/domain/jobs/exceptions.py`
- Create: `tests/unit/domain/jobs/__init__.py`
- Create: `tests/unit/domain/jobs/entities/__init__.py`
- Test: `tests/unit/domain/jobs/entities/test_job_batch.py`

- [ ] **Step 1: Write the tests**

Create `tests/unit/domain/jobs/__init__.py` and `tests/unit/domain/jobs/entities/__init__.py` as empty files.

Create `tests/unit/domain/jobs/entities/test_job_batch.py`:

```python
"""Tests for JobBatch domain entity."""

from datetime import UTC, datetime

import pytest

from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType


def _create(**overrides: object) -> JobBatch:
    defaults: dict[str, object] = {
        "user_id": UserId(1),
        "batch_type": JobBatchType.CHAPTER_PREREADING,
        "reference_id": "42",
        "total_jobs": 5,
    }
    defaults.update(overrides)
    return JobBatch.create(**defaults)  # type: ignore[arg-type]


class TestJobBatchCreate:
    def test_creates_with_defaults(self) -> None:
        batch = _create()
        assert batch.id == JobBatchId(0)
        assert batch.user_id == UserId(1)
        assert batch.batch_type == JobBatchType.CHAPTER_PREREADING
        assert batch.reference_id == "42"
        assert batch.total_jobs == 5
        assert batch.completed_jobs == 0
        assert batch.failed_jobs == 0
        assert batch.status == JobBatchStatus.PENDING
        assert batch.job_keys == []

    def test_rejects_zero_total_jobs(self) -> None:
        with pytest.raises(DomainError, match="total_jobs must be positive"):
            _create(total_jobs=0)

    def test_rejects_negative_total_jobs(self) -> None:
        with pytest.raises(DomainError, match="total_jobs must be positive"):
            _create(total_jobs=-1)

    def test_rejects_empty_reference_id(self) -> None:
        with pytest.raises(DomainError, match="reference_id cannot be empty"):
            _create(reference_id="")


class TestJobBatchMarkJobCompleted:
    def test_increments_completed(self) -> None:
        batch = _create(total_jobs=3)
        batch.mark_job_completed()
        assert batch.completed_jobs == 1
        assert batch.status == JobBatchStatus.RUNNING

    def test_transitions_to_completed_when_all_done(self) -> None:
        batch = _create(total_jobs=2)
        batch.mark_job_completed()
        batch.mark_job_completed()
        assert batch.completed_jobs == 2
        assert batch.status == JobBatchStatus.COMPLETED

    def test_completed_with_some_failures(self) -> None:
        batch = _create(total_jobs=3)
        batch.mark_job_completed()
        batch.mark_job_failed()
        batch.mark_job_completed()
        assert batch.status == JobBatchStatus.COMPLETED_WITH_ERRORS


class TestJobBatchMarkJobFailed:
    def test_increments_failed(self) -> None:
        batch = _create(total_jobs=3)
        batch.mark_job_failed()
        assert batch.failed_jobs == 1
        assert batch.status == JobBatchStatus.RUNNING

    def test_all_failed(self) -> None:
        batch = _create(total_jobs=2)
        batch.mark_job_failed()
        batch.mark_job_failed()
        assert batch.status == JobBatchStatus.FAILED


class TestJobBatchCancel:
    def test_cancel_sets_cancelled(self) -> None:
        batch = _create(total_jobs=3)
        batch.cancel()
        assert batch.status == JobBatchStatus.CANCELLED

    def test_cancel_already_completed_raises(self) -> None:
        batch = _create(total_jobs=1)
        batch.mark_job_completed()
        with pytest.raises(DomainError, match="Cannot cancel.*COMPLETED"):
            batch.cancel()


class TestJobBatchAddJobKey:
    def test_adds_key(self) -> None:
        batch = _create()
        batch.add_job_key("saq:job:abc123")
        assert batch.job_keys == ["saq:job:abc123"]

    def test_adds_multiple_keys(self) -> None:
        batch = _create()
        batch.add_job_key("key1")
        batch.add_job_key("key2")
        assert batch.job_keys == ["key1", "key2"]


class TestJobBatchReconstitute:
    def test_create_with_id(self) -> None:
        now = datetime.now(UTC)
        batch = JobBatch.create_with_id(
            id=JobBatchId(10),
            user_id=UserId(1),
            batch_type=JobBatchType.CHAPTER_PREREADING,
            reference_id="42",
            total_jobs=5,
            completed_jobs=2,
            failed_jobs=1,
            status=JobBatchStatus.RUNNING,
            job_keys=["k1", "k2"],
            created_at=now,
            updated_at=now,
        )
        assert batch.id == JobBatchId(10)
        assert batch.completed_jobs == 2
        assert batch.failed_jobs == 1
        assert batch.status == JobBatchStatus.RUNNING
        assert batch.job_keys == ["k1", "k2"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend && uv run pytest tests/unit/domain/jobs/ -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.domain.jobs'`

- [ ] **Step 3: Create the domain module and entity**

Create `src/domain/jobs/__init__.py` as an empty file.

Create `src/domain/jobs/entities/__init__.py` as an empty file.

Create `src/domain/jobs/entities/job_batch.py`:

```python
"""JobBatch domain entity for tracking groups of background jobs."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import JobBatchId, UserId


class JobBatchType(StrEnum):
    """Supported batch job types."""

    CHAPTER_PREREADING = "chapter_prereading"


class JobBatchStatus(StrEnum):
    """Status of a job batch."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobBatch(Entity[JobBatchId]):
    """Tracks a group of related background jobs."""

    id: JobBatchId
    user_id: UserId
    batch_type: JobBatchType
    reference_id: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    status: JobBatchStatus
    job_keys: list[str]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.total_jobs <= 0:
            raise DomainError("total_jobs must be positive")
        if not self.reference_id or not self.reference_id.strip():
            raise DomainError("reference_id cannot be empty")

    def _recompute_status(self) -> None:
        finished = self.completed_jobs + self.failed_jobs
        if finished >= self.total_jobs:
            if self.failed_jobs == self.total_jobs:
                self.status = JobBatchStatus.FAILED
            elif self.failed_jobs > 0:
                self.status = JobBatchStatus.COMPLETED_WITH_ERRORS
            else:
                self.status = JobBatchStatus.COMPLETED
        elif finished > 0:
            self.status = JobBatchStatus.RUNNING
        self.updated_at = datetime.now(UTC)

    def mark_job_completed(self) -> None:
        self.completed_jobs += 1
        self._recompute_status()

    def mark_job_failed(self) -> None:
        self.failed_jobs += 1
        self._recompute_status()

    def cancel(self) -> None:
        terminal = {JobBatchStatus.COMPLETED, JobBatchStatus.FAILED, JobBatchStatus.COMPLETED_WITH_ERRORS}
        if self.status in terminal:
            raise DomainError(f"Cannot cancel batch in {self.status} status")
        self.status = JobBatchStatus.CANCELLED
        self.updated_at = datetime.now(UTC)

    def add_job_key(self, key: str) -> None:
        self.job_keys.append(key)

    @classmethod
    def create(
        cls,
        user_id: UserId,
        batch_type: JobBatchType,
        reference_id: str,
        total_jobs: int,
    ) -> "JobBatch":
        now = datetime.now(UTC)
        return cls(
            id=JobBatchId.generate(),
            user_id=user_id,
            batch_type=batch_type,
            reference_id=reference_id,
            total_jobs=total_jobs,
            completed_jobs=0,
            failed_jobs=0,
            status=JobBatchStatus.PENDING,
            job_keys=[],
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def create_with_id(
        cls,
        id: JobBatchId,
        user_id: UserId,
        batch_type: JobBatchType,
        reference_id: str,
        total_jobs: int,
        completed_jobs: int,
        failed_jobs: int,
        status: JobBatchStatus,
        job_keys: list[str],
        created_at: datetime,
        updated_at: datetime,
    ) -> "JobBatch":
        return cls(
            id=id,
            user_id=user_id,
            batch_type=batch_type,
            reference_id=reference_id,
            total_jobs=total_jobs,
            completed_jobs=completed_jobs,
            failed_jobs=failed_jobs,
            status=status,
            job_keys=list(job_keys),
            created_at=created_at,
            updated_at=updated_at,
        )
```

Create `src/domain/jobs/exceptions.py`:

```python
"""Jobs domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError


class JobBatchNotFoundError(EntityNotFoundError):
    """Raised when a job batch cannot be found."""

    def __init__(self, batch_id: int) -> None:
        super().__init__("JobBatch", batch_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd backend && uv run pytest tests/unit/domain/jobs/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Run type checker**

Run:
```bash
cd backend && uv run pyright src/domain/jobs/
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add src/domain/jobs/ tests/unit/domain/jobs/
git commit -m "feat: add JobBatch domain entity with status tracking"
```

---

## Task 4: Application Layer — Protocols

**Files:**
- Create: `src/application/jobs/__init__.py`
- Create: `src/application/jobs/protocols/__init__.py`
- Create: `src/application/jobs/protocols/job_batch_repository.py`
- Create: `src/application/jobs/protocols/job_queue_service.py`
- Create: `src/application/jobs/use_cases/__init__.py`

- [ ] **Step 1: Create the protocol files**

Create `src/application/jobs/__init__.py`, `src/application/jobs/protocols/__init__.py`, and `src/application/jobs/use_cases/__init__.py` as empty files.

Create `src/application/jobs/protocols/job_batch_repository.py`:

```python
"""Protocol for JobBatch repository."""

from typing import Protocol

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch


class JobBatchRepositoryProtocol(Protocol):
    async def save(self, batch: JobBatch) -> JobBatch: ...

    async def find_by_id(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch | None: ...

    async def find_by_reference(
        self, batch_type: str, reference_id: str, user_id: UserId
    ) -> list[JobBatch]: ...
```

Create `src/application/jobs/protocols/job_queue_service.py`:

```python
"""Protocol for job queue service wrapping SAQ."""

from typing import Protocol


class JobQueueServiceProtocol(Protocol):
    async def enqueue(
        self,
        function_name: str,
        retries: int = 3,
        timeout: int = 300,
        **kwargs: object,
    ) -> str:
        """Enqueue a job. Returns the SAQ job key."""
        ...

    async def abort(self, job_key: str) -> None:
        """Abort a job by key."""
        ...
```

- [ ] **Step 2: Run type checker**

Run:
```bash
cd backend && uv run pyright src/application/jobs/
```

Expected: 0 errors.

- [ ] **Step 3: Commit**

```bash
git add src/application/jobs/
git commit -m "feat: add job batch repository and queue service protocols"
```

---

## Task 5: Application Layer — EnqueueBookPrereadingUseCase

**Files:**
- Create: `src/application/jobs/use_cases/enqueue_book_prereading_use_case.py`
- Create: `tests/unit/application/jobs/__init__.py`
- Create: `tests/unit/application/jobs/use_cases/__init__.py`
- Test: `tests/unit/application/jobs/use_cases/test_enqueue_book_prereading_use_case.py`

- [ ] **Step 1: Write the tests**

Create `tests/unit/application/jobs/__init__.py` and `tests/unit/application/jobs/use_cases/__init__.py` as empty files.

Create `tests/unit/application/jobs/use_cases/test_enqueue_book_prereading_use_case.py`:

```python
"""Tests for EnqueueBookPrereadingUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.jobs.entities.job_batch import JobBatchStatus, JobBatchType
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.exceptions import BookNotFoundError


def _make_chapter(chapter_id: int, book_id: int = 1) -> Chapter:
    from datetime import UTC, datetime

    return Chapter.create_with_id(
        id=ChapterId(chapter_id),
        book_id=BookId(book_id),
        name=f"Chapter {chapter_id}",
        created_at=datetime.now(UTC),
        start_xpoint=f"/body/chapter[{chapter_id}]",
    )


@pytest.fixture
def chapter_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def book_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def batch_repo() -> AsyncMock:
    repo = AsyncMock()
    # save returns the batch it receives (simulating DB assign)
    repo.save.side_effect = lambda b: b
    return repo


@pytest.fixture
def queue_service() -> AsyncMock:
    service = AsyncMock()
    service.enqueue = AsyncMock(side_effect=lambda fn, **kw: f"saq:job:{kw.get('chapter_id', 0)}")
    return service


@pytest.fixture
def use_case(
    chapter_repo: AsyncMock,
    book_repo: AsyncMock,
    batch_repo: AsyncMock,
    queue_service: AsyncMock,
) -> EnqueueBookPrereadingUseCase:
    return EnqueueBookPrereadingUseCase(
        chapter_repo=chapter_repo,
        book_repo=book_repo,
        batch_repo=batch_repo,
        queue_service=queue_service,
    )


class TestEnqueueBookPrereading:
    async def test_enqueues_one_job_per_chapter(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        book_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        chapters = [_make_chapter(1), _make_chapter(2), _make_chapter(3)]
        chapter_repo.find_all_by_book.return_value = chapters
        book_repo.find_by_id.return_value = MagicMock()

        batch = await use_case.execute(BookId(1), UserId(1))

        assert batch.total_jobs == 3
        assert batch.batch_type == JobBatchType.CHAPTER_PREREADING
        assert batch.reference_id == "1"
        assert len(batch.job_keys) == 3
        assert queue_service.enqueue.call_count == 3

    async def test_skips_chapters_without_xpoint(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        book_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        ch_with = _make_chapter(1)
        ch_without = Chapter.create_with_id(
            id=ChapterId(2),
            book_id=BookId(1),
            name="No XPoint",
            created_at=ch_with.created_at,
            start_xpoint=None,
        )
        chapter_repo.find_all_by_book.return_value = [ch_with, ch_without]
        book_repo.find_by_id.return_value = MagicMock()

        batch = await use_case.execute(BookId(1), UserId(1))

        assert batch.total_jobs == 1
        assert queue_service.enqueue.call_count == 1

    async def test_raises_when_book_not_found(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        book_repo: AsyncMock,
    ) -> None:
        book_repo.find_by_id.return_value = None

        with pytest.raises(BookNotFoundError):
            await use_case.execute(BookId(999), UserId(1))

    async def test_raises_when_no_eligible_chapters(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        book_repo: AsyncMock,
    ) -> None:
        from src.domain.common.exceptions import DomainError

        chapter_repo.find_all_by_book.return_value = []
        book_repo.find_by_id.return_value = MagicMock()

        with pytest.raises(DomainError, match="No eligible chapters"):
            await use_case.execute(BookId(1), UserId(1))
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd backend && uv run pytest tests/unit/application/jobs/ -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write the use case**

Create `src/application/jobs/use_cases/enqueue_book_prereading_use_case.py`:

```python
"""Use case for enqueuing batch prereading generation for a book."""

import structlog

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.application.jobs.protocols.job_queue_service import JobQueueServiceProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchType
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)


class EnqueueBookPrereadingUseCase:
    def __init__(
        self,
        chapter_repo: ChapterRepositoryProtocol,
        book_repo: BookRepositoryProtocol,
        batch_repo: JobBatchRepositoryProtocol,
        queue_service: JobQueueServiceProtocol,
    ) -> None:
        self._chapter_repo = chapter_repo
        self._book_repo = book_repo
        self._batch_repo = batch_repo
        self._queue_service = queue_service

    async def execute(self, book_id: BookId, user_id: UserId) -> JobBatch:
        book = await self._book_repo.find_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id.value)

        chapters = await self._chapter_repo.find_all_by_book(book_id, user_id)
        eligible = [ch for ch in chapters if ch.start_xpoint]

        if not eligible:
            raise DomainError("No eligible chapters found for prereading generation")

        batch = JobBatch.create(
            user_id=user_id,
            batch_type=JobBatchType.CHAPTER_PREREADING,
            reference_id=str(book_id.value),
            total_jobs=len(eligible),
        )
        batch = await self._batch_repo.save(batch)

        for chapter in eligible:
            job_key = await self._queue_service.enqueue(
                "generate_chapter_prereading",
                retries=3,
                timeout=300,
                batch_id=batch.id.value,
                book_id=book_id.value,
                chapter_id=chapter.id.value,
                user_id=user_id.value,
            )
            batch.add_job_key(job_key)

        await self._batch_repo.save(batch)

        logger.info(
            "book_prereading_batch_enqueued",
            batch_id=batch.id.value,
            book_id=book_id.value,
            total_jobs=batch.total_jobs,
        )
        return batch
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd backend && uv run pytest tests/unit/application/jobs/ -v
```

Expected: All tests PASS.

- [ ] **Step 5: Run type checker**

Run:
```bash
cd backend && uv run pyright src/application/jobs/
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add src/application/jobs/use_cases/enqueue_book_prereading_use_case.py tests/unit/application/jobs/
git commit -m "feat: add EnqueueBookPrereadingUseCase"
```

---

## Task 6: Application Layer — GetJobBatchUseCase and CancelJobBatchUseCase

**Files:**
- Create: `src/application/jobs/use_cases/get_job_batch_use_case.py`
- Create: `src/application/jobs/use_cases/cancel_job_batch_use_case.py`
- Test: `tests/unit/application/jobs/use_cases/test_get_job_batch_use_case.py`
- Test: `tests/unit/application/jobs/use_cases/test_cancel_job_batch_use_case.py`

- [ ] **Step 1: Write tests for GetJobBatchUseCase**

Create `tests/unit/application/jobs/use_cases/test_get_job_batch_use_case.py`:

```python
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
```

- [ ] **Step 2: Write tests for CancelJobBatchUseCase**

Create `tests/unit/application/jobs/use_cases/test_cancel_job_batch_use_case.py`:

```python
"""Tests for CancelJobBatchUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.jobs.use_cases.cancel_job_batch_use_case import CancelJobBatchUseCase
from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType
from src.domain.jobs.exceptions import JobBatchNotFoundError


def _make_batch(
    batch_id: int = 1,
    status: JobBatchStatus = JobBatchStatus.RUNNING,
    job_keys: list[str] | None = None,
) -> JobBatch:
    now = datetime.now(UTC)
    return JobBatch.create_with_id(
        id=JobBatchId(batch_id),
        user_id=UserId(1),
        batch_type=JobBatchType.CHAPTER_PREREADING,
        reference_id="42",
        total_jobs=3,
        completed_jobs=1,
        failed_jobs=0,
        status=status,
        job_keys=job_keys or ["k1", "k2", "k3"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def batch_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save.side_effect = lambda b: b
    return repo


@pytest.fixture
def queue_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def use_case(batch_repo: AsyncMock, queue_service: AsyncMock) -> CancelJobBatchUseCase:
    return CancelJobBatchUseCase(batch_repo=batch_repo, queue_service=queue_service)


class TestCancelJobBatch:
    async def test_aborts_all_jobs_and_cancels_batch(
        self,
        use_case: CancelJobBatchUseCase,
        batch_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        batch_repo.find_by_id.return_value = _make_batch()
        result = await use_case.execute(JobBatchId(1), UserId(1))
        assert result.status == JobBatchStatus.CANCELLED
        assert queue_service.abort.call_count == 3
        batch_repo.save.assert_called_once()

    async def test_raises_when_not_found(
        self, use_case: CancelJobBatchUseCase, batch_repo: AsyncMock
    ) -> None:
        batch_repo.find_by_id.return_value = None
        with pytest.raises(JobBatchNotFoundError):
            await use_case.execute(JobBatchId(999), UserId(1))
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
cd backend && uv run pytest tests/unit/application/jobs/use_cases/test_get_job_batch_use_case.py tests/unit/application/jobs/use_cases/test_cancel_job_batch_use_case.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write GetJobBatchUseCase**

Create `src/application/jobs/use_cases/get_job_batch_use_case.py`:

```python
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
```

- [ ] **Step 5: Write CancelJobBatchUseCase**

Create `src/application/jobs/use_cases/cancel_job_batch_use_case.py`:

```python
"""Use case for cancelling a job batch."""

import structlog

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.application.jobs.protocols.job_queue_service import JobQueueServiceProtocol
from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch
from src.domain.jobs.exceptions import JobBatchNotFoundError

logger = structlog.get_logger(__name__)


class CancelJobBatchUseCase:
    def __init__(
        self,
        batch_repo: JobBatchRepositoryProtocol,
        queue_service: JobQueueServiceProtocol,
    ) -> None:
        self._batch_repo = batch_repo
        self._queue_service = queue_service

    async def execute(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch:
        batch = await self._batch_repo.find_by_id(batch_id, user_id)
        if not batch:
            raise JobBatchNotFoundError(batch_id.value)

        for key in batch.job_keys:
            await self._queue_service.abort(key)

        batch.cancel()
        batch = await self._batch_repo.save(batch)

        logger.info("job_batch_cancelled", batch_id=batch_id.value)
        return batch
```

- [ ] **Step 6: Run tests to verify they pass**

Run:
```bash
cd backend && uv run pytest tests/unit/application/jobs/ -v
```

Expected: All tests PASS.

- [ ] **Step 7: Run type checker**

Run:
```bash
cd backend && uv run pyright src/application/jobs/
```

Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add src/application/jobs/use_cases/get_job_batch_use_case.py src/application/jobs/use_cases/cancel_job_batch_use_case.py tests/unit/application/jobs/use_cases/test_get_job_batch_use_case.py tests/unit/application/jobs/use_cases/test_cancel_job_batch_use_case.py
git commit -m "feat: add GetJobBatch and CancelJobBatch use cases"
```

---

## Task 7: Infrastructure Layer — ORM Model, Mapper, Repository

**Files:**
- Create: `src/infrastructure/jobs/__init__.py`
- Create: `src/infrastructure/jobs/orm/__init__.py`
- Create: `src/infrastructure/jobs/orm/job_batch_model.py`
- Create: `src/infrastructure/jobs/mappers/__init__.py`
- Create: `src/infrastructure/jobs/mappers/job_batch_mapper.py`
- Create: `src/infrastructure/jobs/repositories/__init__.py`
- Create: `src/infrastructure/jobs/repositories/job_batch_repository.py`
- Modify: `src/models.py`

- [ ] **Step 1: Create the ORM model**

Create `src/infrastructure/jobs/__init__.py`, `src/infrastructure/jobs/orm/__init__.py`, `src/infrastructure/jobs/mappers/__init__.py`, and `src/infrastructure/jobs/repositories/__init__.py` as empty files.

Create `src/infrastructure/jobs/orm/job_batch_model.py`:

```python
"""SQLAlchemy ORM model for job batches."""

from datetime import datetime as dt

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.database import Base


class JobBatchModel(Base):
    __tablename__ = "job_batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    batch_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    total_jobs: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    job_keys: Mapped[list[str]] = mapped_column(
        JSON().with_variant(PG_JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
    created_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<JobBatchModel(id={self.id}, type={self.batch_type}, status={self.status})>"
```

- [ ] **Step 2: Register the model in models.py**

Add at the end of `src/models.py`:

```python
from src.infrastructure.jobs.orm.job_batch_model import JobBatchModel  # noqa: F401
```

This ensures Alembic picks up the model metadata.

- [ ] **Step 3: Create the mapper**

Create `src/infrastructure/jobs/mappers/job_batch_mapper.py`:

```python
"""Mapper between JobBatch domain entity and ORM model."""

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchStatus, JobBatchType
from src.infrastructure.jobs.orm.job_batch_model import JobBatchModel


class JobBatchMapper:
    @staticmethod
    def to_domain(model: JobBatchModel) -> JobBatch:
        return JobBatch.create_with_id(
            id=JobBatchId(model.id),
            user_id=UserId(model.user_id),
            batch_type=JobBatchType(model.batch_type),
            reference_id=model.reference_id,
            total_jobs=model.total_jobs,
            completed_jobs=model.completed_jobs,
            failed_jobs=model.failed_jobs,
            status=JobBatchStatus(model.status),
            job_keys=list(model.job_keys),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_orm(entity: JobBatch, existing: JobBatchModel | None = None) -> JobBatchModel:
        model = existing or JobBatchModel()
        model.user_id = entity.user_id.value
        model.batch_type = entity.batch_type.value
        model.reference_id = entity.reference_id
        model.total_jobs = entity.total_jobs
        model.completed_jobs = entity.completed_jobs
        model.failed_jobs = entity.failed_jobs
        model.status = entity.status.value
        model.job_keys = list(entity.job_keys)
        return model
```

- [ ] **Step 4: Create the repository**

Create `src/infrastructure/jobs/repositories/job_batch_repository.py`:

```python
"""SQLAlchemy repository for job batches."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch
from src.infrastructure.jobs.mappers.job_batch_mapper import JobBatchMapper
from src.infrastructure.jobs.orm.job_batch_model import JobBatchModel


class JobBatchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save(self, batch: JobBatch) -> JobBatch:
        existing_model: JobBatchModel | None = None
        if batch.id.value > 0:
            existing_model = await self._db.get(JobBatchModel, batch.id.value)

        model = JobBatchMapper.to_orm(batch, existing_model)
        if not existing_model:
            self._db.add(model)

        await self._db.commit()
        await self._db.refresh(model)
        return JobBatchMapper.to_domain(model)

    async def find_by_id(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch | None:
        result = await self._db.execute(
            select(JobBatchModel).where(
                JobBatchModel.id == batch_id.value,
                JobBatchModel.user_id == user_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return JobBatchMapper.to_domain(model) if model else None

    async def find_by_reference(
        self, batch_type: str, reference_id: str, user_id: UserId
    ) -> list[JobBatch]:
        result = await self._db.execute(
            select(JobBatchModel)
            .where(
                JobBatchModel.batch_type == batch_type,
                JobBatchModel.reference_id == reference_id,
                JobBatchModel.user_id == user_id.value,
            )
            .order_by(JobBatchModel.created_at.desc())
        )
        return [JobBatchMapper.to_domain(m) for m in result.scalars().all()]
```

- [ ] **Step 5: Run type checker**

Run:
```bash
cd backend && uv run pyright src/infrastructure/jobs/
```

Expected: 0 errors.

- [ ] **Step 6: Commit**

```bash
git add src/infrastructure/jobs/ src/models.py
git commit -m "feat: add JobBatch ORM model, mapper, and repository"
```

---

## Task 8: Alembic Migration

**Files:**
- Create: `alembic/versions/049_create_job_batches_table.py`

- [ ] **Step 1: Create the migration**

Create `alembic/versions/049_create_job_batches_table.py`:

```python
"""Create job_batches table.

Revision ID: 049
Revises: 048
Create Date: 2026-04-04

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "049"
down_revision: str | None = "048"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("batch_type", sa.String(50), nullable=False),
        sa.Column("reference_id", sa.String(255), nullable=False),
        sa.Column("total_jobs", sa.Integer(), nullable=False),
        sa.Column("completed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("job_keys", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_batches_id"), "job_batches", ["id"], unique=False)
    op.create_index(op.f("ix_job_batches_user_id"), "job_batches", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_job_batches_reference_id"), "job_batches", ["reference_id"], unique=False
    )
    op.create_index(op.f("ix_job_batches_status"), "job_batches", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_batches_status"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_reference_id"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_user_id"), table_name="job_batches")
    op.drop_index(op.f("ix_job_batches_id"), table_name="job_batches")
    op.drop_table("job_batches")
```

- [ ] **Step 2: Verify migration head is correct**

Run:
```bash
cd backend && uv run alembic heads
```

Expected: Shows `049` as the head (or verify it matches the chain).

- [ ] **Step 3: Commit**

```bash
git add alembic/versions/049_create_job_batches_table.py
git commit -m "feat: add alembic migration for job_batches table"
```

---

## Task 9: Infrastructure Layer — SAQ Queue and Job Queue Service

**Files:**
- Create: `src/infrastructure/jobs/saq_queue.py`
- Create: `src/infrastructure/jobs/saq_job_queue_service.py`

- [ ] **Step 1: Create the SAQ queue factory**

Create `src/infrastructure/jobs/saq_queue.py`:

```python
"""SAQ queue instance factory."""

from saq import Queue


def create_queue(database_url: str) -> Queue:
    """Create a SAQ queue backed by PostgreSQL."""
    return Queue.from_url(database_url)
```

- [ ] **Step 2: Create the job queue service**

Create `src/infrastructure/jobs/saq_job_queue_service.py`:

```python
"""SAQ-backed implementation of JobQueueServiceProtocol."""

import structlog
from saq import Queue

logger = structlog.get_logger(__name__)


class SaqJobQueueService:
    def __init__(self, queue: Queue) -> None:
        self._queue = queue

    async def enqueue(
        self,
        function_name: str,
        retries: int = 3,
        timeout: int = 300,
        **kwargs: object,
    ) -> str:
        job = await self._queue.enqueue(
            function_name,
            retries=retries,
            timeout=timeout,
            **kwargs,
        )
        logger.info("job_enqueued", function=function_name, job_key=job.key)
        return job.key

    async def abort(self, job_key: str) -> None:
        job = await self._queue.job(job_key)
        if job:
            await job.abort("Cancelled by user")
            logger.info("job_aborted", job_key=job_key)
```

- [ ] **Step 3: Run type checker**

Run:
```bash
cd backend && uv run pyright src/infrastructure/jobs/saq_queue.py src/infrastructure/jobs/saq_job_queue_service.py
```

Expected: 0 errors (or only SAQ library stub issues which can be ignored).

- [ ] **Step 4: Commit**

```bash
git add src/infrastructure/jobs/saq_queue.py src/infrastructure/jobs/saq_job_queue_service.py
git commit -m "feat: add SAQ queue factory and job queue service"
```

---

## Task 10: Infrastructure Layer — Task Handlers

**Files:**
- Create: `src/infrastructure/jobs/tasks/__init__.py`
- Create: `src/infrastructure/jobs/tasks/prereading_task_handler.py`
- Create: `src/infrastructure/jobs/tasks/job_lifecycle_handler.py`
- Test: `tests/unit/infrastructure/jobs/__init__.py`
- Test: `tests/unit/infrastructure/jobs/tasks/__init__.py`
- Test: `tests/unit/infrastructure/jobs/tasks/test_prereading_task_handler.py`
- Test: `tests/unit/infrastructure/jobs/tasks/test_job_lifecycle_handler.py`

- [ ] **Step 1: Write tests for PrereadingTaskHandler**

Create `tests/unit/infrastructure/jobs/__init__.py` and `tests/unit/infrastructure/jobs/tasks/__init__.py` as empty files.

Create `tests/unit/infrastructure/jobs/tasks/test_prereading_task_handler.py`:

```python
"""Tests for PrereadingTaskHandler."""

from unittest.mock import AsyncMock

import pytest

from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler


@pytest.fixture
def generate_use_case() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def handler(generate_use_case: AsyncMock) -> PrereadingTaskHandler:
    return PrereadingTaskHandler(generate_prereading_use_case=generate_use_case)


class TestPrereadingTaskHandler:
    async def test_calls_use_case_with_correct_ids(
        self, handler: PrereadingTaskHandler, generate_use_case: AsyncMock
    ) -> None:
        ctx: dict[str, object] = {}
        await handler.generate(ctx, batch_id=1, book_id=42, chapter_id=7, user_id=1)

        generate_use_case.generate_prereading_content.assert_called_once()
        call_args = generate_use_case.generate_prereading_content.call_args
        assert call_args.kwargs["chapter_id"].value == 7
        assert call_args.kwargs["user_id"].value == 1
```

- [ ] **Step 2: Write tests for JobLifecycleHandler**

Create `tests/unit/infrastructure/jobs/tasks/test_job_lifecycle_handler.py`:

```python
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
        batch_repo.find_by_id.return_value = batch
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
        batch_repo.find_by_id.return_value = batch
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

        batch_repo.find_by_id.assert_not_called()

    async def test_skips_non_terminal_status(
        self, handler: JobLifecycleHandler, batch_repo: AsyncMock
    ) -> None:
        job = MagicMock()
        job.status = "active"
        job.kwargs = {"batch_id": 1}

        await handler.after_process({}, job)

        batch_repo.find_by_id.assert_not_called()
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
cd backend && uv run pytest tests/unit/infrastructure/jobs/ -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write PrereadingTaskHandler**

Create `src/infrastructure/jobs/tasks/__init__.py` as an empty file.

Create `src/infrastructure/jobs/tasks/prereading_task_handler.py`:

```python
"""SAQ task handler for chapter prereading generation."""

import structlog

from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (
    GenerateChapterPrereadingUseCase,
)
from src.domain.common.value_objects.ids import ChapterId, UserId

logger = structlog.get_logger(__name__)


class PrereadingTaskHandler:
    def __init__(
        self,
        generate_prereading_use_case: GenerateChapterPrereadingUseCase,
    ) -> None:
        self._generate_use_case = generate_prereading_use_case

    async def generate(
        self,
        _ctx: dict[str, object],
        *,
        batch_id: int,
        book_id: int,
        chapter_id: int,
        user_id: int,
    ) -> None:
        logger.info(
            "prereading_task_started",
            batch_id=batch_id,
            book_id=book_id,
            chapter_id=chapter_id,
        )
        await self._generate_use_case.generate_prereading_content(
            chapter_id=ChapterId(chapter_id),
            user_id=UserId(user_id),
        )
        logger.info(
            "prereading_task_completed",
            batch_id=batch_id,
            chapter_id=chapter_id,
        )
```

- [ ] **Step 5: Write JobLifecycleHandler**

Create `src/infrastructure/jobs/tasks/job_lifecycle_handler.py`:

```python
"""SAQ lifecycle handler for updating JobBatch progress."""

from typing import Any

import structlog

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.domain.common.value_objects.ids import JobBatchId, UserId

logger = structlog.get_logger(__name__)

# SAQ job statuses that indicate a terminal state
_TERMINAL_COMPLETE = "complete"
_TERMINAL_FAILED = "failed"
_TERMINAL_ABORTED = "aborted"


class JobLifecycleHandler:
    def __init__(self, batch_repo: JobBatchRepositoryProtocol) -> None:
        self._batch_repo = batch_repo

    async def after_process(self, _ctx: dict[str, object], job: Any) -> None:
        batch_id = job.kwargs.get("batch_id")
        if batch_id is None:
            return

        status = job.status
        if status not in (_TERMINAL_COMPLETE, _TERMINAL_FAILED, _TERMINAL_ABORTED):
            return

        # Use UserId(0) as a system-level lookup — the batch_id is the primary filter.
        # The repository find_by_id filters by user_id for security, but the worker
        # is a trusted internal process. We look up without user restriction.
        batch = await self._batch_repo.find_by_id_internal(JobBatchId(batch_id))
        if not batch:
            logger.warning("batch_not_found_in_after_process", batch_id=batch_id)
            return

        if status == _TERMINAL_COMPLETE:
            batch.mark_job_completed()
        else:
            batch.mark_job_failed()

        await self._batch_repo.save(batch)
        logger.info(
            "batch_progress_updated",
            batch_id=batch_id,
            completed=batch.completed_jobs,
            failed=batch.failed_jobs,
            total=batch.total_jobs,
            status=batch.status,
        )
```

- [ ] **Step 6: Update the repository protocol to add find_by_id_internal**

The lifecycle handler runs in the worker process without a user context. Add to `src/application/jobs/protocols/job_batch_repository.py`:

```python
    async def find_by_id_internal(self, batch_id: JobBatchId) -> JobBatch | None:
        """Find batch by ID without user ownership check. For internal worker use only."""
        ...
```

And add the implementation in `src/infrastructure/jobs/repositories/job_batch_repository.py`. Add this method to the `JobBatchRepository` class:

```python
    async def find_by_id_internal(self, batch_id: JobBatchId) -> JobBatch | None:
        result = await self._db.execute(
            select(JobBatchModel).where(JobBatchModel.id == batch_id.value)
        )
        model = result.scalar_one_or_none()
        return JobBatchMapper.to_domain(model) if model else None
```

- [ ] **Step 7: Update lifecycle handler test to use find_by_id_internal**

In the test file `tests/unit/infrastructure/jobs/tasks/test_job_lifecycle_handler.py`, the `batch_repo` mock's `find_by_id` calls should be `find_by_id_internal` instead. Update:

- `batch_repo.find_by_id.return_value` → `batch_repo.find_by_id_internal.return_value`
- `batch_repo.find_by_id.assert_not_called()` → `batch_repo.find_by_id_internal.assert_not_called()`

- [ ] **Step 8: Run tests to verify they pass**

Run:
```bash
cd backend && uv run pytest tests/unit/infrastructure/jobs/ -v
```

Expected: All tests PASS.

- [ ] **Step 9: Run type checker**

Run:
```bash
cd backend && uv run pyright src/infrastructure/jobs/tasks/
```

Expected: 0 errors (or only SAQ library stub issues).

- [ ] **Step 10: Commit**

```bash
git add src/infrastructure/jobs/tasks/ src/application/jobs/protocols/job_batch_repository.py src/infrastructure/jobs/repositories/job_batch_repository.py tests/unit/infrastructure/jobs/
git commit -m "feat: add SAQ task handlers for prereading and batch lifecycle"
```

---

## Task 11: DI Containers and Wiring

**Files:**
- Create: `src/containers/jobs.py`
- Modify: `src/containers/shared.py`
- Modify: `src/containers/root.py`

- [ ] **Step 1: Add job batch repository to SharedContainer**

In `src/containers/shared.py`, add the import at the top:

```python
from src.infrastructure.jobs.repositories.job_batch_repository import JobBatchRepository
```

Add at the end of the `SharedContainer` class (after `ai_chat_session_repository`):

```python
    # Jobs
    job_batch_repository = providers.Factory(JobBatchRepository, db=db)
```

- [ ] **Step 2: Create JobsContainer**

Create `src/containers/jobs.py`:

```python
"""DI container for jobs module."""

from dependency_injector import containers, providers

from src.application.jobs.use_cases.cancel_job_batch_use_case import CancelJobBatchUseCase
from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.application.jobs.use_cases.get_job_batch_use_case import GetJobBatchUseCase


class JobsContainer(containers.DeclarativeContainer):
    """Container for job-related use cases."""

    # External dependencies (injected by root container)
    job_batch_repository = providers.Dependency()
    job_queue_service = providers.Dependency()
    chapter_repository = providers.Dependency()
    book_repository = providers.Dependency()

    # Use cases
    enqueue_book_prereading_use_case = providers.Factory(
        EnqueueBookPrereadingUseCase,
        chapter_repo=chapter_repository,
        book_repo=book_repository,
        batch_repo=job_batch_repository,
        queue_service=job_queue_service,
    )

    get_job_batch_use_case = providers.Factory(
        GetJobBatchUseCase,
        batch_repo=job_batch_repository,
    )

    cancel_job_batch_use_case = providers.Factory(
        CancelJobBatchUseCase,
        batch_repo=job_batch_repository,
        queue_service=job_queue_service,
    )
```

- [ ] **Step 3: Wire JobsContainer into RootContainer**

Read `src/containers/root.py` to see the current structure, then add:

Import at the top:
```python
from src.containers.jobs import JobsContainer
```

Add the `jobs` sub-container in the `RootContainer` class. The `job_queue_service` dependency will be provided at runtime (it needs the SAQ queue instance which is created in the lifespan). For now, declare it as a `Dependency()`:

```python
    job_queue_service = providers.Dependency()

    jobs = providers.Container(
        JobsContainer,
        job_batch_repository=shared.job_batch_repository,
        job_queue_service=job_queue_service,
        chapter_repository=shared.chapter_repository,
        book_repository=shared.book_repository,
    )
```

- [ ] **Step 4: Run type checker**

Run:
```bash
cd backend && uv run pyright src/containers/jobs.py src/containers/root.py src/containers/shared.py
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add src/containers/jobs.py src/containers/shared.py src/containers/root.py
git commit -m "feat: wire job batch repository and use cases into DI containers"
```

---

## Task 12: API Router and Schemas

**Files:**
- Create: `src/infrastructure/jobs/schemas/__init__.py`
- Create: `src/infrastructure/jobs/schemas/job_batch_schemas.py`
- Create: `src/infrastructure/jobs/routers/__init__.py`
- Create: `src/infrastructure/jobs/routers/job_batches.py`
- Modify: `src/main.py`

- [ ] **Step 1: Create Pydantic schemas**

Create `src/infrastructure/jobs/schemas/__init__.py` as an empty file.

Create `src/infrastructure/jobs/schemas/job_batch_schemas.py`:

```python
"""Pydantic schemas for job batch API responses."""

from datetime import datetime

from pydantic import BaseModel


class JobBatchResponse(BaseModel):
    id: int
    batch_type: str
    reference_id: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    status: str
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: Create the router**

Create `src/infrastructure/jobs/routers/__init__.py` as an empty file.

Create `src/infrastructure/jobs/routers/job_batches.py`:

```python
"""API router for job batch management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.application.jobs.use_cases.cancel_job_batch_use_case import CancelJobBatchUseCase
from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.application.jobs.use_cases.get_job_batch_use_case import GetJobBatchUseCase
from src.core import container
from src.domain.common.value_objects.ids import BookId, JobBatchId, UserId
from src.domain.identity import User
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.jobs.schemas.job_batch_schemas import JobBatchResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(batch: object) -> JobBatchResponse:
    from src.domain.jobs.entities.job_batch import JobBatch

    assert isinstance(batch, JobBatch)
    return JobBatchResponse(
        id=batch.id.value,
        batch_type=batch.batch_type.value,
        reference_id=batch.reference_id,
        total_jobs=batch.total_jobs,
        completed_jobs=batch.completed_jobs,
        failed_jobs=batch.failed_jobs,
        status=batch.status.value,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.post(
    "/books/{book_id}/prereading",
    response_model=JobBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@require_ai_enabled
async def enqueue_book_prereading(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: EnqueueBookPrereadingUseCase = Depends(
        inject_use_case(container.jobs.enqueue_book_prereading_use_case)
    ),
) -> JobBatchResponse:
    """Enqueue prereading generation for all chapters of a book."""
    batch = await use_case.execute(
        BookId(book_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)


@router.get(
    "/batches/{batch_id}",
    response_model=JobBatchResponse,
    status_code=status.HTTP_200_OK,
)
async def get_job_batch(
    batch_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetJobBatchUseCase = Depends(
        inject_use_case(container.jobs.get_job_batch_use_case)
    ),
) -> JobBatchResponse:
    """Get job batch status."""
    batch = await use_case.execute(
        JobBatchId(batch_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)


@router.delete(
    "/batches/{batch_id}",
    response_model=JobBatchResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_job_batch(
    batch_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CancelJobBatchUseCase = Depends(
        inject_use_case(container.jobs.cancel_job_batch_use_case)
    ),
) -> JobBatchResponse:
    """Cancel a job batch and abort all pending/active jobs."""
    batch = await use_case.execute(
        JobBatchId(batch_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)
```

- [ ] **Step 3: Register router and SAQ queue in main.py**

In `src/main.py`, add imports:

```python
from src.infrastructure.jobs.routers import job_batches
from src.infrastructure.jobs.saq_job_queue_service import SaqJobQueueService
from src.infrastructure.jobs.saq_queue import create_queue
```

In the `lifespan` async context manager, after `initialize_database(settings)` and before `yield`:

```python
    # Initialize SAQ queue for job enqueueing
    saq_queue = create_queue(settings.DATABASE_URL)
    await saq_queue.connect()
    queue_service = SaqJobQueueService(saq_queue)
    container.job_queue_service.override(queue_service)
```

After `yield` (in the shutdown section):

```python
    await saq_queue.disconnect()
    container.job_queue_service.reset_override()
```

In the router registration block, add:

```python
# Jobs
app.include_router(job_batches.router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 4: Run type checker**

Run:
```bash
cd backend && uv run pyright src/infrastructure/jobs/routers/ src/infrastructure/jobs/schemas/
```

Expected: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add src/infrastructure/jobs/routers/ src/infrastructure/jobs/schemas/ src/main.py
git commit -m "feat: add job batch API endpoints and SAQ queue lifecycle in app"
```

---

## Task 13: Worker Entrypoint

**Files:**
- Create: `src/worker.py`

- [ ] **Step 1: Create the worker module**

Create `src/worker.py`:

```python
"""SAQ worker entrypoint.

Start with: uv run saq src.worker.settings
"""

import asyncio

import structlog
from dependency_injector import containers, providers
from saq import Queue
from saq.types import Context, SettingsDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_session_factory, initialize_database
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.jobs.repositories.job_batch_repository import JobBatchRepository
from src.infrastructure.jobs.saq_queue import create_queue
from src.infrastructure.jobs.tasks.job_lifecycle_handler import JobLifecycleHandler
from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)

logger = structlog.get_logger(__name__)

settings = get_settings()
queue = create_queue(settings.DATABASE_URL)

# Module-level holders for handler instances (set during startup)
_prereading_handler: PrereadingTaskHandler | None = None
_lifecycle_handler: JobLifecycleHandler | None = None


class WorkerContainer(containers.DeclarativeContainer):
    """Lightweight DI container for worker dependencies."""

    db = providers.Dependency(instance_of=AsyncSession)

    # Repositories
    book_repository = providers.Factory(BookRepository, db=db)
    chapter_repository = providers.Factory(ChapterRepository, db=db)
    chapter_prereading_repository = providers.Factory(ChapterPrereadingRepository, db=db)
    file_repository = providers.Factory(FileRepository)
    job_batch_repository = providers.Factory(JobBatchRepository, db=db)
    ai_usage_repository = providers.Factory(AIUsageRepository, db=db)

    # Services
    ai_service = providers.Factory(AIService, usage_repository=ai_usage_repository)
    text_extraction_service = providers.Factory(EpubTextExtractionService)


async def startup(ctx: Context) -> None:
    """Initialize worker resources."""
    logger.info("worker_starting")
    initialize_database(settings)

    session_factory = get_session_factory()
    db = session_factory()
    ctx["db"] = db

    worker_container = WorkerContainer()
    worker_container.db.override(db)
    ctx["container"] = worker_container

    # Build handlers with injected dependencies
    from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (
        GenerateChapterPrereadingUseCase,
    )

    prereading_handler = PrereadingTaskHandler(
        generate_prereading_use_case=GenerateChapterPrereadingUseCase(
            prereading_repo=worker_container.chapter_prereading_repository(),
            chapter_repo=worker_container.chapter_repository(),
            text_extraction_service=worker_container.text_extraction_service(),
            book_repo=worker_container.book_repository(),
            file_repo=worker_container.file_repository(),
            ai_prereading_service=worker_container.ai_service(),
        ),
    )

    lifecycle_handler = JobLifecycleHandler(
        batch_repo=worker_container.job_batch_repository(),
    )

    global _prereading_handler, _lifecycle_handler  # noqa: PLW0603
    _prereading_handler = prereading_handler
    _lifecycle_handler = lifecycle_handler

    ctx["prereading_handler"] = prereading_handler
    ctx["lifecycle_handler"] = lifecycle_handler

    logger.info("worker_started")


async def shutdown(ctx: Context) -> None:
    """Cleanup worker resources."""
    logger.info("worker_shutting_down")
    db: AsyncSession | None = ctx.get("db")  # type: ignore[assignment]
    if db:
        await db.close()
    logger.info("worker_stopped")


async def generate_chapter_prereading(
    ctx: Context, *, batch_id: int, book_id: int, chapter_id: int, user_id: int
) -> None:
    """SAQ task function that delegates to the handler."""
    assert _prereading_handler is not None, "Worker not initialized"
    await _prereading_handler.generate(
        ctx, batch_id=batch_id, book_id=book_id, chapter_id=chapter_id, user_id=user_id
    )


async def after_process(ctx: Context, job: object) -> None:
    """SAQ after_process hook that delegates to the lifecycle handler."""
    assert _lifecycle_handler is not None, "Worker not initialized"
    await _lifecycle_handler.after_process(ctx, job)


worker_settings: SettingsDict = {
    "queue": queue,
    "functions": [generate_chapter_prereading],
    "concurrency": int(settings.get("WORKER_CONCURRENCY", 5)) if hasattr(settings, "get") else 5,
    "startup": startup,
    "shutdown": shutdown,
    "after_process": after_process,
}

# Allow overriding concurrency via env var
import os

_concurrency = int(os.getenv("WORKER_CONCURRENCY", "5"))
worker_settings["concurrency"] = _concurrency

settings_export = worker_settings
```

**Note:** The `settings` variable name is reserved by SAQ CLI. SAQ looks for a module-level `settings` dict. However, we already use `settings` for the app config. Rename to avoid collision. The SAQ CLI command will be: `saq src.worker.settings_export`.

Wait — SAQ CLI expects the variable to be named as the last segment of the dotted path. So `saq src.worker.settings_export` looks for `settings_export` in `src.worker`. Let me simplify:

Actually, the SAQ CLI syntax is `saq module.path.variable_name`, so `saq src.worker.worker_settings` will work if the variable is `worker_settings`. But the convention from SAQ docs uses just `settings`. Since we have a name conflict with our config `settings`, let's use `worker_settings` and reference it as `saq src.worker.worker_settings` in the CLI command.

Remove the `settings_export` line and the redundant concurrency override. Clean version:

```python
"""SAQ worker entrypoint.

Start with: uv run saq src.worker.worker_settings
"""

import os

import structlog
from saq.types import Context, SettingsDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.database import get_session_factory, initialize_database
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.jobs.repositories.job_batch_repository import JobBatchRepository
from src.infrastructure.jobs.saq_queue import create_queue
from src.infrastructure.jobs.tasks.job_lifecycle_handler import JobLifecycleHandler
from src.infrastructure.jobs.tasks.prereading_task_handler import PrereadingTaskHandler
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)

logger = structlog.get_logger(__name__)

app_settings = get_settings()
queue = create_queue(app_settings.DATABASE_URL)

_prereading_handler: PrereadingTaskHandler | None = None
_lifecycle_handler: JobLifecycleHandler | None = None


async def startup(ctx: Context) -> None:
    """Initialize worker resources."""
    logger.info("worker_starting")
    initialize_database(app_settings)

    session_factory = get_session_factory()
    db = session_factory()
    ctx["db"] = db

    # Build dependencies manually (lightweight, no full DI container needed)
    ai_usage_repo = AIUsageRepository(db=db)
    ai_service = AIService(usage_repository=ai_usage_repo)
    book_repo = BookRepository(db=db)
    chapter_repo = ChapterRepository(db=db)
    prereading_repo = ChapterPrereadingRepository(db=db)
    file_repo = FileRepository()
    text_extraction = EpubTextExtractionService()
    batch_repo = JobBatchRepository(db=db)

    from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (
        GenerateChapterPrereadingUseCase,
    )

    use_case = GenerateChapterPrereadingUseCase(
        prereading_repo=prereading_repo,
        chapter_repo=chapter_repo,
        text_extraction_service=text_extraction,
        book_repo=book_repo,
        file_repo=file_repo,
        ai_prereading_service=ai_service,
    )

    global _prereading_handler, _lifecycle_handler  # noqa: PLW0603
    _prereading_handler = PrereadingTaskHandler(generate_prereading_use_case=use_case)
    _lifecycle_handler = JobLifecycleHandler(batch_repo=batch_repo)

    logger.info("worker_started")


async def shutdown(ctx: Context) -> None:
    """Cleanup worker resources."""
    logger.info("worker_shutting_down")
    db: AsyncSession | None = ctx.get("db")  # type: ignore[assignment]
    if db:
        await db.close()
    logger.info("worker_stopped")


async def generate_chapter_prereading(
    ctx: Context, *, batch_id: int, book_id: int, chapter_id: int, user_id: int
) -> None:
    """SAQ task: generate prereading for a single chapter."""
    assert _prereading_handler is not None, "Worker not initialized"
    await _prereading_handler.generate(
        ctx, batch_id=batch_id, book_id=book_id, chapter_id=chapter_id, user_id=user_id
    )


async def after_process(ctx: Context, job: object) -> None:
    """SAQ after_process hook: update batch progress."""
    assert _lifecycle_handler is not None, "Worker not initialized"
    await _lifecycle_handler.after_process(ctx, job)


worker_settings: SettingsDict = {
    "queue": queue,
    "functions": [generate_chapter_prereading],
    "concurrency": int(os.getenv("WORKER_CONCURRENCY", "5")),
    "startup": startup,
    "shutdown": shutdown,
    "after_process": after_process,
}
```

- [ ] **Step 2: Run type checker**

Run:
```bash
cd backend && uv run pyright src/worker.py
```

Expected: 0 errors (or only SAQ library type stub issues).

- [ ] **Step 3: Commit**

```bash
git add src/worker.py
git commit -m "feat: add SAQ worker entrypoint with prereading task"
```

---

## Task 14: Docker Compose — Worker Service

**Files:**
- Modify: `docker-compose.yml` (project root)

- [ ] **Step 1: Add worker service**

Add after the `app` service in `docker-compose.yml`:

```yaml
  worker:
    image: tumetsu/crossbill:latest
    container_name: crossbill-worker
    restart: unless-stopped
    pull_policy: always
    command: ["uv", "run", "saq", "src.worker.worker_settings"]
    environment:
      DATABASE_URL: postgresql://crossbill:${POSTGRES_PASSWORD:-crossbill_secure_password}@postgres:5432/crossbill
      ENVIRONMENT: production
      AI_PROVIDER: ${AI_PROVIDER:-}
      AI_MODEL_NAME: ${AI_MODEL_NAME:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      GOOGLE_API_KEY: ${GOOGLE_API_KEY:-}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-}
      WORKER_CONCURRENCY: ${WORKER_CONCURRENCY:-5}
    volumes:
      - type: bind
        source: /path/on/host/for/crossbill/book-files
        target: /app/book-files
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - crossbill-network
```

- [ ] **Step 2: Verify the Dockerfile has uv available**

The existing Dockerfile installs `uv` at line 37 (`RUN pip install --no-cache-dir uv`). However, it then runs `uv pip install --system` and does not install `saq` as a CLI tool. The `saq` CLI is installed as part of the `saq[postgres]` package, so it should be available in the system Python path after `uv pip install --system -r requirements.txt`.

The worker command `uv run saq src.worker.worker_settings` may not work since `uv` is in system install mode. Instead, use the direct `saq` command:

```yaml
    command: ["saq", "src.worker.worker_settings"]
```

Update the command in the docker-compose.yml accordingly.

- [ ] **Step 3: Commit**

```bash
cd .. && git add docker-compose.yml
git commit -m "feat: add SAQ worker service to docker-compose"
```

---

## Task 15: Run Full Test Suite and Fix Issues

**Files:**
- Various (depends on what breaks)

- [ ] **Step 1: Run all tests**

Run:
```bash
cd backend && uv run pytest -v
```

Expected: All existing tests still pass, new tests pass.

- [ ] **Step 2: Run full type check**

Run:
```bash
cd backend && uv run pyright
```

Expected: No new errors introduced.

- [ ] **Step 3: Run linter**

Run:
```bash
cd backend && uv run ruff check .
```

Expected: No new linting errors.

- [ ] **Step 4: Fix any issues found in steps 1-3**

If any tests fail or type/lint errors appear, fix them before proceeding.

- [ ] **Step 5: Final commit if fixes were needed**

```bash
git add -A
git commit -m "fix: resolve test/type/lint issues from job queue implementation"
```

---

## Summary of API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/jobs/books/{book_id}/prereading` | Enqueue batch prereading for a book |
| GET | `/api/v1/jobs/batches/{batch_id}` | Get batch status |
| DELETE | `/api/v1/jobs/batches/{batch_id}` | Cancel a batch |

## Worker Command

```bash
# Development
cd backend && uv run saq src.worker.worker_settings

# Production (Docker)
saq src.worker.worker_settings
```
