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
