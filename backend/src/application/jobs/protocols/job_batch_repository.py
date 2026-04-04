"""Protocol for JobBatch repository."""

from typing import Protocol

from src.domain.common.value_objects.ids import JobBatchId, UserId
from src.domain.jobs.entities.job_batch import JobBatch


class JobBatchRepositoryProtocol(Protocol):
    async def save(self, batch: JobBatch) -> JobBatch: ...

    async def find_by_id(self, batch_id: JobBatchId, user_id: UserId) -> JobBatch | None: ...

    async def find_by_id_internal(self, batch_id: JobBatchId) -> JobBatch | None:
        """Find batch by ID without user ownership check. For internal worker use only."""
        ...

    async def atomic_increment_completed(self, batch_id: JobBatchId) -> JobBatch | None:
        """Atomically increment completed_jobs and recompute status. Race-condition safe."""
        ...

    async def atomic_increment_failed(self, batch_id: JobBatchId) -> JobBatch | None:
        """Atomically increment failed_jobs and recompute status. Race-condition safe."""
        ...

    async def find_by_reference(
        self, batch_type: str, reference_id: str, user_id: UserId
    ) -> list[JobBatch]: ...
