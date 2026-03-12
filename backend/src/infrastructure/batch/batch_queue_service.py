from saq import Queue

from src.domain.common.value_objects.ids import BatchJobId


class BatchQueueService:
    """Implements BatchQueueServiceProtocol using SAQ."""

    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    async def enqueue_job(self, job_id: BatchJobId) -> None:
        await self.queue.enqueue(
            "process_prereading_job",
            batch_job_id=job_id.value,
        )

    async def cancel_job(self, job_id: BatchJobId) -> None:
        # SAQ doesn't have direct job cancellation by custom ID.
        # The worker checks job status before processing each item,
        # so setting status to CANCELLED in the DB is sufficient.
        pass
