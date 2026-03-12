# Batch AI Processing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add background batch processing for AI tasks, starting with batch chapter prereading generation, using SAQ with PostgreSQL backend.

**Architecture:** SAQ worker process runs alongside the FastAPI app, both connecting to the same PostgreSQL database. The application layer defines protocols for batch job management and queue operations. The infrastructure layer implements these using SAQ and SQLAlchemy. Batch processors handle individual task types (prereading first).

**Tech Stack:** SAQ (with PostgreSQL backend), SQLAlchemy (async), FastAPI, dependency-injector, psycopg 3

**Spec:** `docs/superpowers/specs/2026-03-12-batch-ai-processing-design.md`

---

## Chunk 1: Domain Layer + Typed IDs

### Task 1: Add BatchJobId and BatchItemId to typed IDs

**Files:**
- Modify: `backend/src/domain/common/value_objects/ids.py`
- Test: `backend/tests/unit/domain/batch/test_batch_entities.py`

- [ ] **Step 1: Add BatchJobId and BatchItemId to ids.py**

Add to the end of `backend/src/domain/common/value_objects/ids.py`:

```python
@dataclass(frozen=True)
class BatchJobId(EntityId):
    """Strongly-typed batch job identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("BatchJobId must be non-negative")

    @classmethod
    def generate(cls) -> "BatchJobId":
        return cls(0)  # Database assigns real ID


@dataclass(frozen=True)
class BatchItemId(EntityId):
    """Strongly-typed batch item identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("BatchItemId must be non-negative")

    @classmethod
    def generate(cls) -> "BatchItemId":
        return cls(0)  # Database assigns real ID
```

- [ ] **Step 2: Run pyright to verify**

Run: `cd backend && uv run pyright src/domain/common/value_objects/ids.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/src/domain/common/value_objects/ids.py
git commit -m "feat: add BatchJobId and BatchItemId typed identifiers"
```

### Task 2: Create BatchJob domain entity

**Files:**
- Create: `backend/src/domain/batch/__init__.py`
- Create: `backend/src/domain/batch/entities/__init__.py`
- Create: `backend/src/domain/batch/entities/batch_job.py`
- Test: `backend/tests/unit/domain/batch/test_batch_entities.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/src/domain/batch/entities
touch backend/src/domain/batch/__init__.py
touch backend/src/domain/batch/entities/__init__.py
```

- [ ] **Step 2: Write the failing test for BatchJob**

Create `backend/tests/unit/domain/batch/__init__.py` and `backend/tests/unit/domain/batch/test_batch_entities.py`:

```bash
mkdir -p backend/tests/unit/domain/batch
touch backend/tests/unit/domain/batch/__init__.py
```

```python
# backend/tests/unit/domain/batch/test_batch_entities.py
from datetime import UTC, datetime

from src.domain.batch.entities.batch_job import BatchJob, BatchJobStatus
from src.domain.common.value_objects.ids import BatchJobId, BookId, UserId


def test_create_batch_job() -> None:
    """Test creating a batch job via factory."""
    job = BatchJob.create(
        user_id=UserId(1),
        book_id=BookId(5),
        job_type="prereading",
        total_items=10,
    )

    assert job.id == BatchJobId(0)  # placeholder
    assert job.user_id == UserId(1)
    assert job.book_id == BookId(5)
    assert job.job_type == "prereading"
    assert job.status == BatchJobStatus.PENDING
    assert job.total_items == 10
    assert job.completed_items == 0
    assert job.failed_items == 0
    assert job.completed_at is None


def test_batch_job_status_values() -> None:
    """Test BatchJobStatus enum values."""
    assert BatchJobStatus.PENDING.value == "pending"
    assert BatchJobStatus.PROCESSING.value == "processing"
    assert BatchJobStatus.COMPLETED.value == "completed"
    assert BatchJobStatus.FAILED.value == "failed"
    assert BatchJobStatus.CANCELLED.value == "cancelled"


def test_create_batch_job_with_id() -> None:
    """Test reconstituting from persistence."""
    now = datetime.now(UTC)
    job = BatchJob.create_with_id(
        id=BatchJobId(42),
        user_id=UserId(1),
        book_id=BookId(5),
        job_type="prereading",
        status=BatchJobStatus.PROCESSING,
        total_items=10,
        completed_items=3,
        failed_items=1,
        created_at=now,
        completed_at=None,
    )

    assert job.id == BatchJobId(42)
    assert job.status == BatchJobStatus.PROCESSING
    assert job.completed_items == 3
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/domain/batch/test_batch_entities.py -v`
Expected: FAIL (module not found)

- [ ] **Step 4: Write BatchJob entity**

Create `backend/src/domain/batch/entities/batch_job.py`:

```python
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Self

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import BatchJobId, BookId, UserId


class BatchJobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob(Entity[BatchJobId]):
    """Represents a batch AI processing job."""

    id: BatchJobId
    user_id: UserId
    book_id: BookId
    job_type: str
    status: BatchJobStatus
    total_items: int
    completed_items: int
    failed_items: int
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        job_type: str,
        total_items: int,
    ) -> Self:
        return cls(
            id=BatchJobId.generate(),
            user_id=user_id,
            book_id=book_id,
            job_type=job_type,
            status=BatchJobStatus.PENDING,
            total_items=total_items,
            completed_items=0,
            failed_items=0,
            created_at=datetime.now(UTC),
            completed_at=None,
        )

    @classmethod
    def create_with_id(
        cls,
        id: BatchJobId,
        user_id: UserId,
        book_id: BookId,
        job_type: str,
        status: BatchJobStatus,
        total_items: int,
        completed_items: int,
        failed_items: int,
        created_at: datetime,
        completed_at: datetime | None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            job_type=job_type,
            status=status,
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            created_at=created_at,
            completed_at=completed_at,
        )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/unit/domain/batch/test_batch_entities.py -v`
Expected: PASS

- [ ] **Step 6: Run pyright**

Run: `cd backend && uv run pyright src/domain/batch/`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/batch/ backend/tests/unit/domain/batch/
git commit -m "feat: add BatchJob domain entity"
```

### Task 3: Create BatchItem domain entity

**Files:**
- Create: `backend/src/domain/batch/entities/batch_item.py`
- Modify: `backend/tests/unit/domain/batch/test_batch_entities.py`

- [ ] **Step 1: Add failing tests for BatchItem**

Append to `backend/tests/unit/domain/batch/test_batch_entities.py`:

```python
from src.domain.batch.entities.batch_item import BatchItem, BatchItemStatus
from src.domain.common.value_objects.ids import BatchItemId


def test_create_batch_item() -> None:
    """Test creating a batch item via factory."""
    item = BatchItem.create(
        batch_job_id=BatchJobId(1),
        entity_type="chapter",
        entity_id=42,
    )

    assert item.id == BatchItemId(0)  # placeholder
    assert item.batch_job_id == BatchJobId(1)
    assert item.entity_type == "chapter"
    assert item.entity_id == 42
    assert item.status == BatchItemStatus.PENDING
    assert item.attempts == 0
    assert item.error_message is None
    assert item.completed_at is None


def test_batch_item_status_values() -> None:
    """Test BatchItemStatus enum values."""
    assert BatchItemStatus.PENDING.value == "pending"
    assert BatchItemStatus.PROCESSING.value == "processing"
    assert BatchItemStatus.SUCCEEDED.value == "succeeded"
    assert BatchItemStatus.FAILED.value == "failed"


def test_create_batch_item_with_id() -> None:
    """Test reconstituting from persistence."""
    now = datetime.now(UTC)
    item = BatchItem.create_with_id(
        id=BatchItemId(99),
        batch_job_id=BatchJobId(1),
        entity_type="chapter",
        entity_id=42,
        status=BatchItemStatus.SUCCEEDED,
        attempts=2,
        error_message=None,
        created_at=now,
        completed_at=now,
    )

    assert item.id == BatchItemId(99)
    assert item.attempts == 2
    assert item.status == BatchItemStatus.SUCCEEDED
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/unit/domain/batch/test_batch_entities.py::test_create_batch_item -v`
Expected: FAIL

- [ ] **Step 3: Write BatchItem entity**

Create `backend/src/domain/batch/entities/batch_item.py`:

```python
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Self

from src.domain.common.entity import Entity
from src.domain.common.value_objects.ids import BatchItemId, BatchJobId


class BatchItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class BatchItem(Entity[BatchItemId]):
    """Represents a single unit of work within a batch job."""

    id: BatchItemId
    batch_job_id: BatchJobId
    entity_type: str
    entity_id: int  # polymorphic reference — raw int intentionally
    status: BatchItemStatus
    attempts: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def create(
        cls,
        batch_job_id: BatchJobId,
        entity_type: str,
        entity_id: int,
    ) -> Self:
        return cls(
            id=BatchItemId.generate(),
            batch_job_id=batch_job_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=BatchItemStatus.PENDING,
            attempts=0,
            error_message=None,
            created_at=datetime.now(UTC),
            completed_at=None,
        )

    @classmethod
    def create_with_id(
        cls,
        id: BatchItemId,
        batch_job_id: BatchJobId,
        entity_type: str,
        entity_id: int,
        status: BatchItemStatus,
        attempts: int,
        error_message: str | None,
        created_at: datetime,
        completed_at: datetime | None,
    ) -> Self:
        return cls(
            id=id,
            batch_job_id=batch_job_id,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status,
            attempts=attempts,
            error_message=error_message,
            created_at=created_at,
            completed_at=completed_at,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/domain/batch/test_batch_entities.py -v`
Expected: ALL PASS

- [ ] **Step 5: Run pyright**

Run: `cd backend && uv run pyright src/domain/batch/`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/domain/batch/entities/batch_item.py backend/tests/unit/domain/batch/test_batch_entities.py
git commit -m "feat: add BatchItem domain entity"
```

---

## Chunk 2: Application Layer — Protocols and Use Cases

### Task 4: Create application layer protocols

**Files:**
- Create: `backend/src/application/batch/__init__.py`
- Create: `backend/src/application/batch/protocols/__init__.py`
- Create: `backend/src/application/batch/protocols/batch_job_repository.py`
- Create: `backend/src/application/batch/protocols/batch_queue_service.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/src/application/batch/protocols
touch backend/src/application/batch/__init__.py
touch backend/src/application/batch/protocols/__init__.py
```

- [ ] **Step 2: Write BatchJobRepositoryProtocol**

Create `backend/src/application/batch/protocols/batch_job_repository.py`:

```python
from typing import Protocol

from src.domain.batch.entities.batch_item import BatchItem
from src.domain.batch.entities.batch_job import BatchJob
from src.domain.common.value_objects.ids import BatchItemId, BatchJobId, BookId, UserId


class BatchJobRepositoryProtocol(Protocol):
    async def save_job(self, job: BatchJob) -> BatchJob: ...
    async def save_item(self, item: BatchItem) -> BatchItem: ...
    async def save_items(self, items: list[BatchItem]) -> list[BatchItem]: ...
    async def get_job(self, job_id: BatchJobId) -> BatchJob | None: ...
    async def get_job_items(self, job_id: BatchJobId) -> list[BatchItem]: ...
    async def get_pending_items(self, job_id: BatchJobId) -> list[BatchItem]: ...
    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> BatchJob | None: ...
```

- [ ] **Step 3: Write BatchQueueServiceProtocol**

Create `backend/src/application/batch/protocols/batch_queue_service.py`:

```python
from typing import Protocol

from src.domain.common.value_objects.ids import BatchJobId


class BatchQueueServiceProtocol(Protocol):
    async def enqueue_job(self, job_id: BatchJobId) -> None: ...
    async def cancel_job(self, job_id: BatchJobId) -> None: ...
```

- [ ] **Step 4: Run pyright**

Run: `cd backend && uv run pyright src/application/batch/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/batch/
git commit -m "feat: add batch job repository and queue service protocols"
```

### Task 5: Create CreateBatchPrereadingUseCase

**Files:**
- Create: `backend/src/application/batch/use_cases/__init__.py`
- Create: `backend/src/application/batch/use_cases/create_batch_prereading_use_case.py`
- Test: `backend/tests/unit/application/batch/test_create_batch_prereading_use_case.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p backend/src/application/batch/use_cases
touch backend/src/application/batch/use_cases/__init__.py
mkdir -p backend/tests/unit/application/batch
touch backend/tests/unit/application/batch/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `backend/tests/unit/application/batch/test_create_batch_prereading_use_case.py`:

```python
from dataclasses import dataclass, field
from datetime import UTC, datetime

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
            i for i in self.saved_items
            if i.batch_job_id == job_id and i.status.value == "pending"
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/application/batch/ -v`
Expected: FAIL (import error)

- [ ] **Step 4: Write the ChapterPrereadingProviderProtocol**

This protocol abstracts the "which chapters need prereading" query. The application layer shouldn't know how to query this — it's a repository concern.

Create `backend/src/application/batch/protocols/chapter_prereading_provider.py`:

```python
from typing import Protocol

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId


class ChapterPrereadingProviderProtocol(Protocol):
    async def get_chapter_ids_needing_prereading(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterId]: ...
```

- [ ] **Step 5: Write CreateBatchPrereadingUseCase**

Create `backend/src/application/batch/use_cases/create_batch_prereading_use_case.py`:

```python
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
        active_job = await self.batch_job_repo.find_active_job(
            user_id, book_id, "prereading"
        )
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
            raise DomainError(
                "No chapters need prereading generation in this book"
            )

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
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/application/batch/ -v`
Expected: ALL PASS

- [ ] **Step 7: Run pyright**

Run: `cd backend && uv run pyright src/application/batch/`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/src/application/batch/ backend/tests/unit/application/batch/
git commit -m "feat: add CreateBatchPrereadingUseCase with protocols"
```

### Task 6: Create GetBatchJobStatusUseCase and CancelBatchJobUseCase

**Files:**
- Create: `backend/src/application/batch/use_cases/get_batch_job_status_use_case.py`
- Create: `backend/src/application/batch/use_cases/cancel_batch_job_use_case.py`
- Test: `backend/tests/unit/application/batch/test_batch_job_use_cases.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/unit/application/batch/test_batch_job_use_cases.py`:

```python
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
from src.domain.common.exceptions import DomainError, EntityNotFoundError
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    UserId,
)


# Reuse FakeBatchJobRepository and FakeBatchQueueService from test_create_batch_prereading_use_case.py
# For simplicity, define inline here:

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
        result = await use_case.execute(
            user_id=UserId(1), job_id=BatchJobId(1)
        )

        assert result.id == BatchJobId(1)
        assert result.status == BatchJobStatus.PROCESSING

    async def test_raises_not_found_for_missing_job(self) -> None:
        repo = FakeBatchJobRepository()
        use_case = GetBatchJobStatusUseCase(batch_job_repo=repo)

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                user_id=UserId(1), job_id=BatchJobId(999)
            )

    async def test_raises_not_found_for_other_users_job(self) -> None:
        repo = FakeBatchJobRepository()
        job = _make_job(user_id=2)  # belongs to user 2
        await repo.save_job(job)

        use_case = GetBatchJobStatusUseCase(batch_job_repo=repo)

        with pytest.raises(EntityNotFoundError):
            await use_case.execute(
                user_id=UserId(1), job_id=BatchJobId(1)  # user 1 asking
            )


class TestCancelBatchJob:
    async def test_cancels_processing_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.PROCESSING)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(
            batch_job_repo=repo, batch_queue_service=queue
        )
        result = await use_case.execute(
            user_id=UserId(1), job_id=BatchJobId(1)
        )

        assert result.status == BatchJobStatus.CANCELLED
        assert len(queue.cancelled_jobs) == 1

    async def test_cancels_pending_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.PENDING)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(
            batch_job_repo=repo, batch_queue_service=queue
        )
        result = await use_case.execute(
            user_id=UserId(1), job_id=BatchJobId(1)
        )

        assert result.status == BatchJobStatus.CANCELLED

    async def test_raises_error_for_already_completed_job(self) -> None:
        repo = FakeBatchJobRepository()
        queue = FakeBatchQueueService()
        job = _make_job(status=BatchJobStatus.COMPLETED)
        await repo.save_job(job)

        use_case = CancelBatchJobUseCase(
            batch_job_repo=repo, batch_queue_service=queue
        )

        with pytest.raises(BusinessRuleViolationError, match="already completed|Cannot cancel"):
            await use_case.execute(
                user_id=UserId(1), job_id=BatchJobId(1)
            )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/unit/application/batch/test_batch_job_use_cases.py -v`
Expected: FAIL

- [ ] **Step 3: Write GetBatchJobStatusUseCase**

Create `backend/src/application/batch/use_cases/get_batch_job_status_use_case.py`:

```python
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
```

- [ ] **Step 4: Write CancelBatchJobUseCase**

Create `backend/src/application/batch/use_cases/cancel_batch_job_use_case.py`:

```python
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
    DomainError,
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/unit/application/batch/ -v`
Expected: ALL PASS

- [ ] **Step 6: Run pyright**

Run: `cd backend && uv run pyright src/application/batch/`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/src/application/batch/use_cases/ backend/tests/unit/application/batch/
git commit -m "feat: add GetBatchJobStatus and CancelBatchJob use cases"
```

---

## Chunk 3: Infrastructure — Database Layer (ORM, Migration, Mappers, Repository)

### Task 7: Add SAQ dependency to pyproject.toml

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Add saq[postgres] dependency**

Add `"saq[postgres]>=0.26.0,<1.0.0"` to the dependencies list in `backend/pyproject.toml`.

- [ ] **Step 2: Install dependencies**

Run: `cd backend && uv sync`
Expected: installs saq and its postgres extras

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "feat: add saq[postgres] dependency for batch processing"
```

### Task 8: Create Alembic migration for batch tables

**Files:**
- Create: `backend/alembic/versions/046_add_batch_processing_tables.py`

- [ ] **Step 1: Write the migration**

Create `backend/alembic/versions/046_add_batch_processing_tables.py`:

```python
"""Add batch processing tables.

Revision ID: 046
Revises: 045
Create Date: 2026-03-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "046"
down_revision: str | Sequence[str] | None = "045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            sa.Integer(),
            sa.ForeignKey("books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_items", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_batch_jobs_active_lookup",
        "batch_jobs",
        ["user_id", "book_id", "job_type", "status"],
    )

    op.create_table(
        "batch_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "batch_job_id",
            sa.Integer(),
            sa.ForeignKey("batch_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_batch_items_job_id",
        "batch_items",
        ["batch_job_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_batch_items_job_id", table_name="batch_items")
    op.drop_table("batch_items")
    op.drop_index("ix_batch_jobs_active_lookup", table_name="batch_jobs")
    op.drop_table("batch_jobs")
```

- [ ] **Step 2: Run migration against dev database**

Run: `cd backend && uv run alembic upgrade head`
Expected: applies migration 046

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/046_add_batch_processing_tables.py
git commit -m "feat: add batch_jobs and batch_items database migration"
```

### Task 9: Create ORM models for batch tables

**Files:**
- Modify: `backend/src/models.py`

Note: The spec lists `infrastructure/batch/models.py` for ORM models, but the existing codebase places ALL ORM models in `src/models.py`. We follow the existing convention for consistency.

- [ ] **Step 1: Add BatchJob and BatchItem ORM models**

Add to the end of `backend/src/models.py` (before any final comments):

```python
class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    total_items: Mapped[int] = mapped_column(nullable=False, default=0)
    completed_items: Mapped[int] = mapped_column(nullable=False, default=0)
    failed_items: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[dt] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[dt | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_batch_jobs_active_lookup", "user_id", "book_id", "job_type", "status"),
    )

    user: Mapped["User"] = relationship()
    book: Mapped["Book"] = relationship()
    items: Mapped[list["BatchItem"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"BatchJob(id={self.id}, type={self.job_type}, status={self.status})"


class BatchItem(Base):
    __tablename__ = "batch_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    batch_job_id: Mapped[int] = mapped_column(
        ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    attempts: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[dt | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    job: Mapped["BatchJob"] = relationship(back_populates="items")

    def __repr__(self) -> str:
        return f"BatchItem(id={self.id}, type={self.entity_type}, status={self.status})"
```

Note: ensure `Text` is imported at the top of `models.py` (from `sqlalchemy import Text`). Check existing imports first.

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/models.py`
Expected: PASS

- [ ] **Step 3: Run existing tests to ensure no regression**

Run: `cd backend && uv run pytest -x`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add backend/src/models.py
git commit -m "feat: add BatchJob and BatchItem ORM models"
```

### Task 10: Create mappers for batch entities

**Files:**
- Create: `backend/src/infrastructure/batch/__init__.py`
- Create: `backend/src/infrastructure/batch/mappers.py`

- [ ] **Step 1: Create directory**

```bash
mkdir -p backend/src/infrastructure/batch
touch backend/src/infrastructure/batch/__init__.py
```

- [ ] **Step 2: Write batch mappers**

Create `backend/src/infrastructure/batch/mappers.py`:

```python
from src.domain.batch.entities.batch_item import BatchItem as DomainBatchItem
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJob as DomainBatchJob
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    UserId,
)
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM


class BatchJobMapper:
    def to_domain(self, orm: BatchJobORM) -> DomainBatchJob:
        return DomainBatchJob.create_with_id(
            id=BatchJobId(orm.id),
            user_id=UserId(orm.user_id),
            book_id=BookId(orm.book_id),
            job_type=orm.job_type,
            status=BatchJobStatus(orm.status),
            total_items=orm.total_items,
            completed_items=orm.completed_items,
            failed_items=orm.failed_items,
            created_at=orm.created_at,
            completed_at=orm.completed_at,
        )

    def to_orm(
        self, entity: DomainBatchJob, orm: BatchJobORM | None = None
    ) -> BatchJobORM:
        if orm is not None:
            orm.status = entity.status.value
            orm.total_items = entity.total_items
            orm.completed_items = entity.completed_items
            orm.failed_items = entity.failed_items
            orm.completed_at = entity.completed_at
            return orm

        return BatchJobORM(
            id=entity.id.value if entity.id.value != 0 else None,
            user_id=entity.user_id.value,
            book_id=entity.book_id.value,
            job_type=entity.job_type,
            status=entity.status.value,
            total_items=entity.total_items,
            completed_items=entity.completed_items,
            failed_items=entity.failed_items,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )


class BatchItemMapper:
    def to_domain(self, orm: BatchItemORM) -> DomainBatchItem:
        return DomainBatchItem.create_with_id(
            id=BatchItemId(orm.id),
            batch_job_id=BatchJobId(orm.batch_job_id),
            entity_type=orm.entity_type,
            entity_id=orm.entity_id,
            status=BatchItemStatus(orm.status),
            attempts=orm.attempts,
            error_message=orm.error_message,
            created_at=orm.created_at,
            completed_at=orm.completed_at,
        )

    def to_orm(
        self, entity: DomainBatchItem, orm: BatchItemORM | None = None
    ) -> BatchItemORM:
        if orm is not None:
            orm.status = entity.status.value
            orm.attempts = entity.attempts
            orm.error_message = entity.error_message
            orm.completed_at = entity.completed_at
            return orm

        return BatchItemORM(
            id=entity.id.value if entity.id.value != 0 else None,
            batch_job_id=entity.batch_job_id.value,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            status=entity.status.value,
            attempts=entity.attempts,
            error_message=entity.error_message,
            created_at=entity.created_at,
            completed_at=entity.completed_at,
        )
```

- [ ] **Step 3: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/mappers.py`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/batch/
git commit -m "feat: add batch job and item ORM mappers"
```

### Task 11: Create BatchJobRepository implementation

**Files:**
- Create: `backend/src/infrastructure/batch/repositories/__init__.py`
- Create: `backend/src/infrastructure/batch/repositories/batch_job_repository.py`

- [ ] **Step 1: Create directory**

```bash
mkdir -p backend/src/infrastructure/batch/repositories
touch backend/src/infrastructure/batch/repositories/__init__.py
```

- [ ] **Step 2: Write BatchJobRepository**

Create `backend/src/infrastructure/batch/repositories/batch_job_repository.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.batch.entities.batch_item import BatchItem as DomainBatchItem
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJob as DomainBatchJob
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import BatchJobId, BookId, UserId
from src.infrastructure.batch.mappers import BatchItemMapper, BatchJobMapper
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM


class BatchJobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.job_mapper = BatchJobMapper()
        self.item_mapper = BatchItemMapper()

    async def save_job(self, job: DomainBatchJob) -> DomainBatchJob:
        if job.id.value != 0:
            # Update existing
            result = await self.db.execute(
                select(BatchJobORM).where(BatchJobORM.id == job.id.value)
            )
            existing_orm = result.scalar_one_or_none()
            if existing_orm is not None:
                self.job_mapper.to_orm(job, existing_orm)
                await self.db.commit()
                await self.db.refresh(existing_orm)
                return self.job_mapper.to_domain(existing_orm)

        # Insert new
        orm = self.job_mapper.to_orm(job)
        self.db.add(orm)
        await self.db.commit()
        await self.db.refresh(orm)
        return self.job_mapper.to_domain(orm)

    async def save_item(self, item: DomainBatchItem) -> DomainBatchItem:
        if item.id.value != 0:
            result = await self.db.execute(
                select(BatchItemORM).where(BatchItemORM.id == item.id.value)
            )
            existing_orm = result.scalar_one_or_none()
            if existing_orm is not None:
                self.item_mapper.to_orm(item, existing_orm)
                await self.db.commit()
                await self.db.refresh(existing_orm)
                return self.item_mapper.to_domain(existing_orm)

        orm = self.item_mapper.to_orm(item)
        self.db.add(orm)
        await self.db.commit()
        await self.db.refresh(orm)
        return self.item_mapper.to_domain(orm)

    async def save_items(self, items: list[DomainBatchItem]) -> list[DomainBatchItem]:
        orms = [self.item_mapper.to_orm(item) for item in items]
        self.db.add_all(orms)
        await self.db.commit()
        for orm in orms:
            await self.db.refresh(orm)
        return [self.item_mapper.to_domain(orm) for orm in orms]

    async def get_job(self, job_id: BatchJobId) -> DomainBatchJob | None:
        result = await self.db.execute(
            select(BatchJobORM).where(BatchJobORM.id == job_id.value)
        )
        orm = result.scalar_one_or_none()
        return self.job_mapper.to_domain(orm) if orm else None

    async def get_job_items(self, job_id: BatchJobId) -> list[DomainBatchItem]:
        result = await self.db.execute(
            select(BatchItemORM).where(BatchItemORM.batch_job_id == job_id.value)
        )
        return [self.item_mapper.to_domain(orm) for orm in result.scalars().all()]

    async def get_pending_items(self, job_id: BatchJobId) -> list[DomainBatchItem]:
        result = await self.db.execute(
            select(BatchItemORM).where(
                BatchItemORM.batch_job_id == job_id.value,
                BatchItemORM.status == BatchItemStatus.PENDING.value,
            )
        )
        return [self.item_mapper.to_domain(orm) for orm in result.scalars().all()]

    async def find_active_job(
        self, user_id: UserId, book_id: BookId, job_type: str
    ) -> DomainBatchJob | None:
        result = await self.db.execute(
            select(BatchJobORM).where(
                BatchJobORM.user_id == user_id.value,
                BatchJobORM.book_id == book_id.value,
                BatchJobORM.job_type == job_type,
                BatchJobORM.status.in_([
                    BatchJobStatus.PENDING.value,
                    BatchJobStatus.PROCESSING.value,
                ]),
            )
        )
        orm = result.scalar_one_or_none()
        return self.job_mapper.to_domain(orm) if orm else None
```

- [ ] **Step 3: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/repositories/`
Expected: PASS

- [ ] **Step 4: Run full test suite**

Run: `cd backend && uv run pytest -x`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/batch/repositories/
git commit -m "feat: add BatchJobRepository SQLAlchemy implementation"
```

---

## Chunk 4: Infrastructure — SAQ Worker and Batch Processor

### Task 12: Create batch AI model configuration

**Files:**
- Modify: `backend/src/config.py`

- [ ] **Step 1: Add batch AI settings to config**

Add the following fields to the `Settings` class in `backend/src/config.py`, after the existing AI settings:

```python
    # Batch AI settings (infrastructure concern)
    BATCH_AI_PROVIDER: Literal["ollama", "openai", "anthropic", "google"] | None = None
    BATCH_AI_MODEL_NAME: str | None = None
    BATCH_MAX_CONCURRENCY: int = 5
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/config.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/src/config.py
git commit -m "feat: add batch AI configuration settings"
```

### Task 13: Create batch AI model factory

**Files:**
- Create: `backend/src/infrastructure/batch/batch_ai_model.py`

- [ ] **Step 1: Write the batch model factory**

This follows the same pattern as `ai_model.py` but reads from batch-specific settings with fallback to main settings.

Create `backend/src/infrastructure/batch/batch_ai_model.py`:

```python
"""AI model factory for batch processing.

Reads batch-specific settings (BATCH_AI_PROVIDER, BATCH_AI_MODEL_NAME)
with fallback to the main AI settings (AI_PROVIDER, AI_MODEL_NAME).
"""

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.config import get_settings


def get_batch_ai_model() -> Model:
    """Get the AI model configured for batch processing.

    Resolution order:
    1. BATCH_AI_PROVIDER / BATCH_AI_MODEL_NAME (batch-specific)
    2. AI_PROVIDER / AI_MODEL_NAME (main app settings, fallback)
    """
    settings = get_settings()

    provider = settings.BATCH_AI_PROVIDER or settings.AI_PROVIDER
    model_name = settings.BATCH_AI_MODEL_NAME or settings.AI_MODEL_NAME

    if provider is None or model_name is None:
        raise RuntimeError(
            "Batch AI model not configured. Set BATCH_AI_PROVIDER/BATCH_AI_MODEL_NAME "
            "or AI_PROVIDER/AI_MODEL_NAME."
        )

    if provider == "ollama":
        return OpenAIChatModel(
            model_name, provider=OllamaProvider(base_url=settings.OPENAI_BASE_URL)
        )
    elif provider == "openai":
        return OpenAIChatModel(
            model_name, provider=OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        )
    elif provider == "anthropic":
        return AnthropicModel(
            model_name, provider=AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        )
    elif provider == "google":
        return GoogleModel(
            model_name, provider=GoogleProvider(api_key=settings.GEMINI_API_KEY)
        )
    else:
        raise RuntimeError(f"Unknown batch AI provider: {provider}")
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/batch_ai_model.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/batch/batch_ai_model.py
git commit -m "feat: add batch AI model factory with fallback to main config"
```

### Task 14: Create ChapterPrereadingProvider

**Files:**
- Create: `backend/src/infrastructure/batch/providers/__init__.py`
- Create: `backend/src/infrastructure/batch/providers/chapter_prereading_provider.py`

This implements the `ChapterPrereadingProviderProtocol` — queries which chapters in a book don't yet have prereading content.

- [ ] **Step 1: Create directory**

```bash
mkdir -p backend/src/infrastructure/batch/providers
touch backend/src/infrastructure/batch/providers/__init__.py
```

- [ ] **Step 2: Write ChapterPrereadingProvider**

Create `backend/src/infrastructure/batch/providers/chapter_prereading_provider.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.models import Chapter, ChapterPrereadingContent


class ChapterPrereadingProvider:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_chapter_ids_needing_prereading(
        self, book_id: BookId, user_id: UserId
    ) -> list[ChapterId]:
        """Return chapter IDs that belong to the book and don't have prereading yet."""
        # Subquery: chapters that already have prereading
        has_prereading = (
            select(ChapterPrereadingContent.chapter_id)
            .where(ChapterPrereadingContent.chapter_id == Chapter.id)
            .correlate(Chapter)
            .exists()
        )

        result = await self.db.execute(
            select(Chapter.id)
            .join(Chapter.book)
            .where(
                Chapter.book_id == book_id.value,
                ~has_prereading,
            )
            .order_by(Chapter.id)
        )

        return [ChapterId(row[0]) for row in result.all()]
```

- [ ] **Step 3: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/providers/`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/batch/providers/
git commit -m "feat: add ChapterPrereadingProvider for batch prereading"
```

### Task 15: Create PrereadingBatchProcessor

**Files:**
- Create: `backend/src/infrastructure/batch/processors/__init__.py`
- Create: `backend/src/infrastructure/batch/processors/prereading_batch_processor.py`

- [ ] **Step 1: Create directory**

```bash
mkdir -p backend/src/infrastructure/batch/processors
touch backend/src/infrastructure/batch/processors/__init__.py
```

- [ ] **Step 2: Write PrereadingBatchProcessor**

This processor reuses the existing prereading generation logic from `GenerateChapterPrereadingUseCase` but adapted for batch context — it receives an item, extracts chapter text, calls AI, and saves the result.

Create `backend/src/infrastructure/batch/processors/prereading_batch_processor.py`:

```python
import structlog
from datetime import UTC, datetime
from pydantic_ai.models import Model
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ai.ai_usage_context import AIUsageContext
from src.config import get_settings
from src.domain.batch.entities.batch_item import BatchItem
from src.domain.common.value_objects.ids import ChapterId, UserId
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.ai.repositories.ai_usage_repository import AIUsageRepository
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
)
from src.infrastructure.reading.services.ebook_text_extraction_service import (
    EbookTextExtractionService,
)
from src.models import Book as BookORM
from src.models import Chapter as ChapterORM
from src.models import File as FileORM

logger = structlog.get_logger()


class PrereadingBatchProcessor:
    """Processes a single chapter prereading generation task."""

    def __init__(self, db: AsyncSession, ai_model: Model) -> None:
        self.db = db
        self.ai_service = AIService(
            usage_repository=AIUsageRepository(db=db),
        )
        # Override the model used by the prereading agent
        self._ai_model = ai_model
        self.prereading_repo = ChapterPrereadingRepository(db=db)
        self.text_extraction = EbookTextExtractionService()

    async def process_item(self, item: BatchItem, user_id: UserId) -> None:
        """Generate prereading content for the chapter referenced by this item."""
        chapter_id = ChapterId(item.entity_id)

        # Load chapter and book info
        result = await self.db.execute(
            select(ChapterORM).where(ChapterORM.id == chapter_id.value)
        )
        chapter_orm = result.scalar_one_or_none()
        if chapter_orm is None:
            raise ValueError(f"Chapter {chapter_id.value} not found")

        # Get book's EPUB file path
        book_result = await self.db.execute(
            select(BookORM).where(BookORM.id == chapter_orm.book_id)
        )
        book_orm = book_result.scalar_one_or_none()
        if book_orm is None:
            raise ValueError(f"Book for chapter {chapter_id.value} not found")

        file_result = await self.db.execute(
            select(FileORM).where(
                FileORM.book_id == book_orm.id,
                FileORM.format == "epub",
            )
        )
        file_orm = file_result.scalar_one_or_none()
        if file_orm is None:
            raise ValueError(f"EPUB file not found for book {book_orm.id}")

        # Extract chapter text
        if not chapter_orm.start_xpoint or not chapter_orm.end_xpoint:
            raise ValueError(
                f"Chapter {chapter_id.value} missing position data (XPoints)"
            )

        from src.domain.reading.value_objects.xpoint import XPoint

        chapter_text = self.text_extraction.extract_chapter_text(
            epub_path=file_orm.file_path,
            start_xpoint=XPoint(chapter_orm.start_xpoint),
            end_xpoint=XPoint(chapter_orm.end_xpoint),
        )

        if len(chapter_text) < 50:
            raise ValueError(
                f"Chapter {chapter_id.value} text too short ({len(chapter_text)} chars)"
            )

        # Generate prereading via AI
        usage_context = AIUsageContext(
            user_id=user_id,
            task_type="prereading",
            entity_type="chapter",
            entity_id=chapter_id.value,
        )

        prereading_result = await self.ai_service.generate_prereading(
            content=chapter_text,
            usage_context=usage_context,
        )

        # Save result
        # PrereadingResult only has summary + keypoints.
        # generated_at and ai_model come from context, not the result.
        settings = get_settings()
        model_name = settings.BATCH_AI_MODEL_NAME or settings.AI_MODEL_NAME or "unknown"

        prereading_entity = ChapterPrereadingContent.create(
            chapter_id=chapter_id,
            summary=prereading_result.summary,
            keypoints=prereading_result.keypoints,
            generated_at=datetime.now(UTC),
            ai_model=model_name,
        )

        await self.prereading_repo.save(prereading_entity)

        logger.info(
            "batch_prereading_item_completed",
            chapter_id=chapter_id.value,
            item_id=item.id.value,
        )
```

Note: This processor constructs its own dependencies (AI service, repos) from the database session, since it runs in the worker process outside FastAPI's DI container. The `ai_model` override for batch-specific model will be wired in the worker setup.

- [ ] **Step 3: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/processors/`
Expected: PASS (may need minor fixes based on actual imports — follow pyright guidance)

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/batch/processors/
git commit -m "feat: add PrereadingBatchProcessor for batch chapter prereading"
```

### Task 16: Create SAQ worker

**Files:**
- Create: `backend/src/infrastructure/batch/worker.py`

- [ ] **Step 1: Write the SAQ worker**

Create `backend/src/infrastructure/batch/worker.py`:

```python
"""SAQ worker for batch AI processing.

Runs as a separate process alongside the FastAPI app.
Start with: uv run saq src.infrastructure.batch.worker.settings

IMPORTANT: This module should NOT be imported during testing or in the
FastAPI app. It runs at module level to configure SAQ.
"""

import asyncio
from datetime import UTC, datetime

import structlog
from saq import Queue
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import get_settings
from src.database import get_session_factory, initialize_database
from src.domain.batch.entities.batch_item import BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJobStatus
from src.domain.common.value_objects.ids import BatchJobId
from src.infrastructure.batch.batch_ai_model import get_batch_ai_model
from src.infrastructure.batch.processors.prereading_batch_processor import (
    PrereadingBatchProcessor,
)
from src.infrastructure.batch.repositories.batch_job_repository import (
    BatchJobRepository,
)
from src.models import BatchItem as BatchItemORM
from src.models import BatchJob as BatchJobORM

logger = structlog.get_logger()


async def startup(ctx: dict) -> None:  # type: ignore[type-arg]
    """Initialize database and AI model on worker startup."""
    settings = get_settings()
    settings.configure_logging()
    initialize_database(settings)
    ctx["session_factory"] = get_session_factory()
    ctx["ai_model"] = get_batch_ai_model()
    logger.info("batch_worker_started")


async def shutdown(ctx: dict) -> None:  # type: ignore[type-arg]
    """Clean up on worker shutdown."""
    from src.database import dispose_engine

    dispose_engine()
    logger.info("batch_worker_stopped")


async def _increment_job_counter(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: int,
    counter: str,
) -> None:
    """Atomically increment a job counter using SQL-level +1."""
    async with session_factory() as db:
        column = getattr(BatchJobORM, counter)
        await db.execute(
            update(BatchJobORM)
            .where(BatchJobORM.id == job_id)
            .values({counter: column + 1})
        )
        await db.commit()


async def _update_item_status(
    session_factory: async_sessionmaker[AsyncSession],
    item_id: int,
    status: str,
    attempts: int,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> None:
    """Update a batch item's status in its own session."""
    async with session_factory() as db:
        values: dict[str, object] = {
            "status": status,
            "attempts": attempts,
        }
        if error_message is not None:
            values["error_message"] = error_message
        if completed_at is not None:
            values["completed_at"] = completed_at
        await db.execute(
            update(BatchItemORM)
            .where(BatchItemORM.id == item_id)
            .values(**values)
        )
        await db.commit()


async def _is_job_cancelled(
    session_factory: async_sessionmaker[AsyncSession],
    job_id: int,
) -> bool:
    """Check if a job has been cancelled."""
    async with session_factory() as db:
        repo = BatchJobRepository(db=db)
        job = await repo.get_job(BatchJobId(job_id))
        return job is not None and job.status == BatchJobStatus.CANCELLED


async def process_batch_job(ctx: dict, *, batch_job_id: int) -> None:  # type: ignore[type-arg]
    """Main SAQ task: process all items in a batch job.

    Each item gets its own database session to avoid concurrent session issues.
    Job counters are updated with SQL-level atomic increments.
    """
    session_factory: async_sessionmaker[AsyncSession] = ctx["session_factory"]
    ai_model = ctx["ai_model"]
    settings = get_settings()
    max_concurrency = settings.BATCH_MAX_CONCURRENCY

    # Load job and items in a dedicated session
    async with session_factory() as db:
        repo = BatchJobRepository(db=db)
        job = await repo.get_job(BatchJobId(batch_job_id))
        if job is None:
            logger.error("batch_job_not_found", job_id=batch_job_id)
            return

        if job.status == BatchJobStatus.CANCELLED:
            logger.info("batch_job_already_cancelled", job_id=batch_job_id)
            return

        # Mark as processing
        job.status = BatchJobStatus.PROCESSING
        await repo.save_job(job)

        items = await repo.get_pending_items(job.id)

    user_id = job.user_id
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _process_item(item_id: int, entity_id: int) -> None:
        """Process a single item with retries. Each attempt uses its own session."""
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            # Check cancellation before acquiring semaphore
            if await _is_job_cancelled(session_factory, batch_job_id):
                return

            async with semaphore:
                try:
                    await _update_item_status(
                        session_factory, item_id,
                        status=BatchItemStatus.PROCESSING.value,
                        attempts=attempt,
                    )

                    # Each item gets its own session for AI processing
                    async with session_factory() as item_db:
                        from src.domain.batch.entities.batch_item import BatchItem
                        processor = PrereadingBatchProcessor(
                            db=item_db, ai_model=ai_model
                        )
                        # Create a minimal BatchItem for the processor
                        item_for_processor = BatchItem.create_with_id(
                            id=__import__("src.domain.common.value_objects.ids", fromlist=["BatchItemId"]).BatchItemId(item_id),
                            batch_job_id=BatchJobId(batch_job_id),
                            entity_type="chapter",
                            entity_id=entity_id,
                            status=BatchItemStatus.PROCESSING,
                            attempts=attempt,
                            error_message=None,
                            created_at=datetime.now(UTC),
                            completed_at=None,
                        )
                        await processor.process_item(item_for_processor, user_id=user_id)

                    # Success
                    await _update_item_status(
                        session_factory, item_id,
                        status=BatchItemStatus.SUCCEEDED.value,
                        attempts=attempt,
                        completed_at=datetime.now(UTC),
                    )
                    await _increment_job_counter(
                        session_factory, batch_job_id, "completed_items"
                    )
                    return  # Done with this item

                except Exception as e:
                    logger.warning(
                        "batch_item_failed",
                        item_id=item_id,
                        attempt=attempt,
                        error=str(e),
                    )

            # Semaphore released here — backoff happens outside the semaphore
            if attempt < max_retries:
                backoff = 2 ** (attempt - 1)  # 1s, 2s
                await asyncio.sleep(backoff)
            else:
                # All retries exhausted
                await _update_item_status(
                    session_factory, item_id,
                    status=BatchItemStatus.FAILED.value,
                    attempts=attempt,
                    error_message=str(e)[:500],  # noqa: F821 — e is from the except block
                    completed_at=datetime.now(UTC),
                )
                await _increment_job_counter(
                    session_factory, batch_job_id, "failed_items"
                )

    # Process items concurrently
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(_process_item(item.id.value, item.entity_id))

    # Mark job as completed
    async with session_factory() as db:
        repo = BatchJobRepository(db=db)
        final_job = await repo.get_job(BatchJobId(batch_job_id))
        if final_job and final_job.status != BatchJobStatus.CANCELLED:
            final_job.status = BatchJobStatus.COMPLETED
            final_job.completed_at = datetime.now(UTC)
            await repo.save_job(final_job)

    logger.info(
        "batch_job_finished",
        job_id=batch_job_id,
        status=final_job.status.value if final_job else "unknown",
    )


# SAQ configuration — runs at module import time (only by SAQ runner)
_settings = get_settings()
_queue_url = _settings.DATABASE_URL.replace("postgresql://", "postgres://")

settings = {
    "queue": Queue.from_url(_queue_url),
    "functions": [process_batch_job],
    "concurrency": 2,
    "startup": startup,
    "shutdown": shutdown,
}
```

Note: The `before_process`/`after_process` hooks are removed — each item creates its own session. The job-level session is used only for initial loading and final status update.

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/worker.py`
Expected: PASS (may need type ignore comments for SAQ's dict context pattern)

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/batch/worker.py
git commit -m "feat: add SAQ worker for batch AI processing"
```

---

## Chunk 5: Infrastructure — Queue Service, Router, DI Wiring, and Deployment

### Task 17: Add DomainError exception handlers to main.py

**Files:**
- Modify: `backend/src/main.py`

The existing codebase only handles `CrossbillError` and its subclasses (from `src.exceptions`). Domain layer exceptions (`DomainError`, `EntityNotFoundError`, `BusinessRuleViolationError` from `src.domain.common.exceptions`) have no handlers and would result in 500 errors. Add handlers for these.

- [ ] **Step 1: Add exception handlers for domain exceptions**

Add to `backend/src/main.py`, after the existing exception handlers:

```python
from src.domain.common.exceptions import (
    BusinessRuleViolationError,
    DomainError,
    EntityNotFoundError,
)


@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(
    request: Request, exc: EntityNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": exc.message},
    )


@app.exception_handler(BusinessRuleViolationError)
async def business_rule_violation_handler(
    request: Request, exc: BusinessRuleViolationError
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": exc.message},
    )


@app.exception_handler(DomainError)
async def domain_error_handler(
    request: Request, exc: DomainError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message},
    )
```

Note: Handler ordering matters — more specific handlers (`EntityNotFoundError`, `BusinessRuleViolationError`) must be registered before the generic `DomainError` handler.

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/main.py`
Expected: PASS

- [ ] **Step 3: Run existing tests**

Run: `cd backend && uv run pytest -x`
Expected: ALL PASS (no existing behavior changes)

- [ ] **Step 4: Commit**

```bash
git add backend/src/main.py
git commit -m "feat: add exception handlers for domain errors (404, 409, 400)"
```

### Task 18: Create BatchQueueService implementation

**Files:**
- Create: `backend/src/infrastructure/batch/batch_queue_service.py`

- [ ] **Step 1: Write BatchQueueService**

Create `backend/src/infrastructure/batch/batch_queue_service.py`:

```python
from saq import Queue

from src.domain.common.value_objects.ids import BatchJobId


class BatchQueueService:
    """Implements BatchQueueServiceProtocol using SAQ."""

    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    async def enqueue_job(self, job_id: BatchJobId) -> None:
        await self.queue.enqueue(
            "process_batch_job",
            batch_job_id=job_id.value,
        )

    async def cancel_job(self, job_id: BatchJobId) -> None:
        # SAQ doesn't have direct job cancellation by custom ID.
        # The worker checks job status before processing each item,
        # so setting status to CANCELLED in the DB is sufficient.
        pass
```

- [ ] **Step 2: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/batch_queue_service.py`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add backend/src/infrastructure/batch/batch_queue_service.py
git commit -m "feat: add BatchQueueService SAQ implementation"
```

### Task 19: Create batch jobs router

**Files:**
- Create: `backend/src/infrastructure/batch/routers/__init__.py`
- Create: `backend/src/infrastructure/batch/routers/batch_jobs.py`
- Create: `backend/src/infrastructure/batch/schemas.py`

- [ ] **Step 1: Create directory and schemas**

```bash
mkdir -p backend/src/infrastructure/batch/routers
touch backend/src/infrastructure/batch/routers/__init__.py
```

Create `backend/src/infrastructure/batch/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class BatchJobResponse(BaseModel):
    job_id: int
    job_type: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: datetime
    completed_at: datetime | None


class BatchJobCreatedResponse(BaseModel):
    job_id: int
    status: str
    total_items: int
```

- [ ] **Step 2: Write the router**

Create `backend/src/infrastructure/batch/routers/batch_jobs.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.batch.use_cases.cancel_batch_job_use_case import (
    CancelBatchJobUseCase,
)
from src.application.batch.use_cases.create_batch_prereading_use_case import (
    CreateBatchPrereadingUseCase,
)
from src.application.batch.use_cases.get_batch_job_status_use_case import (
    GetBatchJobStatusUseCase,
)
from src.core import container
from src.domain.common.value_objects.ids import BatchJobId, BookId
from src.domain.identity.entities.user import User
from src.infrastructure.batch.schemas import BatchJobCreatedResponse, BatchJobResponse
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity.dependencies import get_current_user

router = APIRouter(tags=["batch"])


@router.post("/books/{book_id}/batch/prereading", status_code=201)
@require_ai_enabled
async def create_batch_prereading(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        CreateBatchPrereadingUseCase,
        Depends(inject_use_case(container.create_batch_prereading_use_case)),
    ],
) -> BatchJobCreatedResponse:
    """Create a batch job to generate prereading for all chapters in a book."""
    job = await use_case.execute(
        user_id=current_user.id,
        book_id=BookId(book_id),
    )

    return BatchJobCreatedResponse(
        job_id=job.id.value,
        status=job.status.value,
        total_items=job.total_items,
    )


@router.get("/batch-jobs/{job_id}")
@require_ai_enabled
async def get_batch_job_status(
    job_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        GetBatchJobStatusUseCase,
        Depends(inject_use_case(container.get_batch_job_status_use_case)),
    ],
) -> BatchJobResponse:
    """Get the status of a batch job."""
    job = await use_case.execute(
        user_id=current_user.id,
        job_id=BatchJobId(job_id),
    )

    return BatchJobResponse(
        job_id=job.id.value,
        job_type=job.job_type,
        status=job.status.value,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/batch-jobs/{job_id}/cancel")
@require_ai_enabled
async def cancel_batch_job(
    job_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: Annotated[
        CancelBatchJobUseCase,
        Depends(inject_use_case(container.cancel_batch_job_use_case)),
    ],
) -> BatchJobResponse:
    """Cancel a running batch job."""
    job = await use_case.execute(
        user_id=current_user.id,
        job_id=BatchJobId(job_id),
    )

    return BatchJobResponse(
        job_id=job.id.value,
        job_type=job.job_type,
        status=job.status.value,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
```

- [ ] **Step 3: Run pyright**

Run: `cd backend && uv run pyright src/infrastructure/batch/routers/ src/infrastructure/batch/schemas.py`
Expected: PASS (will fail until DI wiring is done — that's expected, proceed to next step)

- [ ] **Step 4: Commit**

```bash
git add backend/src/infrastructure/batch/routers/ backend/src/infrastructure/batch/schemas.py
git commit -m "feat: add batch jobs API router and schemas"
```

### Task 20: Wire DI container and register router

**Files:**
- Modify: `backend/src/core.py`
- Modify: `backend/src/main.py`

- [ ] **Step 1: Add batch providers to DI container**

Add the following imports and provider definitions to `backend/src/core.py`:

Imports to add:
```python
from src.application.batch.use_cases.cancel_batch_job_use_case import (
    CancelBatchJobUseCase,
)
from src.application.batch.use_cases.create_batch_prereading_use_case import (
    CreateBatchPrereadingUseCase,
)
from src.application.batch.use_cases.get_batch_job_status_use_case import (
    GetBatchJobStatusUseCase,
)
from src.infrastructure.batch.batch_queue_service import BatchQueueService
from src.infrastructure.batch.providers.chapter_prereading_provider import (
    ChapterPrereadingProvider,
)
from src.infrastructure.batch.repositories.batch_job_repository import (
    BatchJobRepository,
)
```

Provider definitions to add inside the `Container` class (after existing repository/service definitions):

```python
    # Batch processing
    batch_job_repository = providers.Factory(BatchJobRepository, db=db)
    chapter_prereading_provider = providers.Factory(ChapterPrereadingProvider, db=db)
    # batch_queue_service needs SAQ Queue instance — provided via Dependency
    batch_queue = providers.Dependency()
    batch_queue_service = providers.Factory(BatchQueueService, queue=batch_queue)

    create_batch_prereading_use_case = providers.Factory(
        CreateBatchPrereadingUseCase,
        batch_job_repo=batch_job_repository,
        batch_queue_service=batch_queue_service,
        chapter_provider=chapter_prereading_provider,
    )
    get_batch_job_status_use_case = providers.Factory(
        GetBatchJobStatusUseCase,
        batch_job_repo=batch_job_repository,
    )
    cancel_batch_job_use_case = providers.Factory(
        CancelBatchJobUseCase,
        batch_job_repo=batch_job_repository,
        batch_queue_service=batch_queue_service,
    )
```

- [ ] **Step 2: Register batch router in main.py**

Add to the router registration section in `backend/src/main.py`:

```python
from src.infrastructure.batch.routers.batch_jobs import router as batch_router

# In the router registration block:
app.include_router(batch_router, prefix=API_V1_PREFIX)
```

- [ ] **Step 3: Initialize SAQ queue in app lifespan**

Add SAQ queue initialization to the lifespan function in `backend/src/main.py`. After `initialize_database(settings)`:

```python
    # Initialize SAQ queue for batch processing (if AI is enabled)
    if settings.ai_enabled:
        from saq import Queue
        queue_url = settings.DATABASE_URL.replace("postgresql://", "postgres://")
        batch_queue = Queue.from_url(queue_url)
        container.batch_queue.override(batch_queue)
```

- [ ] **Step 4: Run pyright**

Run: `cd backend && uv run pyright src/core.py src/main.py`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `cd backend && uv run pytest -x`
Expected: ALL PASS

- [ ] **Step 6: Commit**

```bash
git add backend/src/core.py backend/src/main.py
git commit -m "feat: wire batch processing DI and register router"
```

### Task 21: Add worker to Docker Compose

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add worker service**

Add the following service to `docker-compose.yml` after the `app` service:

```yaml
  worker:
    image: tumetsu/crossbill:latest
    command: uv run saq src.infrastructure.batch.worker.settings
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://crossbill:${POSTGRES_PASSWORD}@postgres:5432/crossbill
      - AI_PROVIDER=${AI_PROVIDER:-}
      - AI_MODEL_NAME=${AI_MODEL_NAME:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - GEMINI_API_KEY=${GEMINI_API_KEY:-}
      - BATCH_AI_PROVIDER=${BATCH_AI_PROVIDER:-}
      - BATCH_AI_MODEL_NAME=${BATCH_AI_MODEL_NAME:-}
      - BATCH_MAX_CONCURRENCY=${BATCH_MAX_CONCURRENCY:-5}
    networks:
      - crossbill-network
    restart: unless-stopped
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add batch worker service to docker-compose"
```

---

## Chunk 6: Integration Tests

### Task 22: Write integration tests for batch endpoints

**Files:**
- Create: `backend/tests/test_batch_jobs.py`

- [ ] **Step 1: Write integration tests**

Create `backend/tests/test_batch_jobs.py`:

```python
"""Integration tests for batch job endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import BatchJob, BatchItem, Book, Chapter, User


async def _create_book_with_chapters(
    db_session: AsyncSession,
    user_id: int,
    num_chapters: int,
    with_xpoints: bool = True,
) -> tuple[Book, list[Chapter]]:
    """Helper to create a book with chapters."""
    from tests.conftest import create_test_book

    book = await create_test_book(db_session, user_id, "Test Book", "Author")
    chapters = []
    for i in range(num_chapters):
        chapter = Chapter(
            book_id=book.id,
            name=f"Chapter {i + 1}",
            start_xpoint=f"/1/2/{i*2}" if with_xpoints else None,
            end_xpoint=f"/1/2/{i*2 + 1}" if with_xpoints else None,
        )
        db_session.add(chapter)
        chapters.append(chapter)
    await db_session.commit()
    for ch in chapters:
        await db_session.refresh(ch)
    return book, chapters


class TestCreateBatchPrereading:
    async def test_creates_batch_job(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ) -> None:
        book, chapters = await _create_book_with_chapters(db_session, test_user.id, 3)

        # Mock the queue service to avoid actual SAQ enqueue
        with patch(
            "src.infrastructure.batch.batch_queue_service.BatchQueueService.enqueue_job",
            new_callable=AsyncMock,
        ):
            response = await client.post(
                f"/api/v1/books/{book.id}/batch/prereading"
            )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_items"] == 3
        assert "job_id" in data

    async def test_409_when_active_job_exists(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ) -> None:
        book, chapters = await _create_book_with_chapters(db_session, test_user.id, 2)

        # Create an active job
        active_job = BatchJob(
            user_id=test_user.id,
            book_id=book.id,
            job_type="prereading",
            status="processing",
            total_items=2,
            completed_items=0,
            failed_items=0,
            created_at=datetime.now(UTC),
        )
        db_session.add(active_job)
        await db_session.commit()

        response = await client.post(
            f"/api/v1/books/{book.id}/batch/prereading"
        )

        assert response.status_code == 409  # BusinessRuleViolationError -> 409


class TestGetBatchJobStatus:
    async def test_returns_job_status(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ) -> None:
        book, _ = await _create_book_with_chapters(db_session, test_user.id, 1)

        job = BatchJob(
            user_id=test_user.id,
            book_id=book.id,
            job_type="prereading",
            status="processing",
            total_items=5,
            completed_items=2,
            failed_items=1,
            created_at=datetime.now(UTC),
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        response = await client.get(f"/api/v1/batch-jobs/{job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_type"] == "prereading"
        assert data["status"] == "processing"
        assert data["total_items"] == 5
        assert data["completed_items"] == 2
        assert data["failed_items"] == 1

    async def test_404_for_other_users_job(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        # Create another user
        other_user = User(id=2, email="other@test.com")
        db_session.add(other_user)
        await db_session.commit()

        from tests.conftest import create_test_book

        book = await create_test_book(db_session, other_user.id, "Other Book")

        job = BatchJob(
            user_id=other_user.id,
            book_id=book.id,
            job_type="prereading",
            status="processing",
            total_items=5,
            completed_items=0,
            failed_items=0,
            created_at=datetime.now(UTC),
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        response = await client.get(f"/api/v1/batch-jobs/{job.id}")
        assert response.status_code == 404


class TestCancelBatchJob:
    async def test_cancels_active_job(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ) -> None:
        book, _ = await _create_book_with_chapters(db_session, test_user.id, 1)

        job = BatchJob(
            user_id=test_user.id,
            book_id=book.id,
            job_type="prereading",
            status="processing",
            total_items=5,
            completed_items=2,
            failed_items=0,
            created_at=datetime.now(UTC),
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        with patch(
            "src.infrastructure.batch.batch_queue_service.BatchQueueService.cancel_job",
            new_callable=AsyncMock,
        ):
            response = await client.post(f"/api/v1/batch-jobs/{job.id}/cancel")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"

    async def test_409_for_completed_job(
        self, client: AsyncClient, db_session: AsyncSession, test_user: User
    ) -> None:
        book, _ = await _create_book_with_chapters(db_session, test_user.id, 1)

        job = BatchJob(
            user_id=test_user.id,
            book_id=book.id,
            job_type="prereading",
            status="completed",
            total_items=5,
            completed_items=5,
            failed_items=0,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(job)

        response = await client.post(f"/api/v1/batch-jobs/{job.id}/cancel")
        assert response.status_code == 409  # BusinessRuleViolationError -> 409
```

- [ ] **Step 2: Run integration tests**

Run: `cd backend && uv run pytest tests/test_batch_jobs.py -v`
Expected: ALL PASS

- [ ] **Step 3: Run full test suite**

Run: `cd backend && uv run pytest -x`
Expected: ALL PASS

- [ ] **Step 4: Run pyright on all new files**

Run: `cd backend && uv run pyright src/infrastructure/batch/ src/application/batch/ src/domain/batch/`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_batch_jobs.py
git commit -m "test: add integration tests for batch job endpoints"
```

### Task 23: Final verification

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 2: Run pyright on entire backend**

Run: `cd backend && uv run pyright`
Expected: PASS

- [ ] **Step 3: Run ruff**

Run: `cd backend && uv run ruff check src/ tests/`
Expected: PASS

- [ ] **Step 4: Verify worker starts locally (smoke test)**

Start dev PostgreSQL: `cd backend && docker compose up -d`

Run worker: `cd backend && uv run saq src.infrastructure.batch.worker.settings`

Expected: Worker starts, logs "batch_worker_started", connects to PostgreSQL. Press Ctrl+C to stop.

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: address pyright/ruff/test issues from final verification"
```
