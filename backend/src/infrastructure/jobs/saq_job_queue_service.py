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
        timeout_seconds: int = 300,
        **kwargs: object,
    ) -> str:
        job = await self._queue.enqueue(
            function_name,
            retries=retries,
            timeout=timeout_seconds,
            **kwargs,
        )
        if job is None:
            raise RuntimeError(f"Failed to enqueue job: {function_name}")
        logger.info("job_enqueued", function=function_name, job_key=job.key)
        return job.key

    async def abort(self, job_key: str) -> None:
        job = await self._queue.job(job_key)
        if job:
            await job.abort("Cancelled by user")
            logger.info("job_aborted", job_key=job_key)
