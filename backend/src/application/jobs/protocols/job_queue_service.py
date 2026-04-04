"""Protocol for job queue service wrapping SAQ."""

from typing import Protocol


class JobQueueServiceProtocol(Protocol):
    async def enqueue(
        self,
        function_name: str,
        retries: int = 3,
        timeout_seconds: int = 300,
        **kwargs: object,
    ) -> str:
        """Enqueue a job. Returns the SAQ job key."""
        ...

    async def abort(self, job_key: str) -> None:
        """Abort a job by key."""
        ...
