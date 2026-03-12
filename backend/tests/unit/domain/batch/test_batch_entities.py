from datetime import UTC, datetime

from src.domain.batch.entities.batch_item import BatchItem, BatchItemStatus
from src.domain.batch.entities.batch_job import BatchJob, BatchJobStatus
from src.domain.common.value_objects.ids import (
    BatchItemId,
    BatchJobId,
    BookId,
    UserId,
)


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
