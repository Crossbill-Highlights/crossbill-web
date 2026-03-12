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
