from typing import Protocol

from src.domain.common.value_objects.ids import BatchJobId


class BatchQueueServiceProtocol(Protocol):
    async def enqueue_job(self, job_id: BatchJobId) -> None: ...
    async def cancel_job(self, job_id: BatchJobId) -> None: ...
