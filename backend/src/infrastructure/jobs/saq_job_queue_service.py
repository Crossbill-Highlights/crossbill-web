"""SAQ-backed implementation of JobQueueServiceProtocol."""

import asyncio
import contextlib
import time

import structlog
from saq import Queue

logger = structlog.get_logger(__name__)


class SaqJobQueueService:
    """Wraps a SAQ Queue with lazy connect and idle auto-disconnect.

    When idle_timeout > 0, the queue connection is closed after that many
    seconds of no enqueue/abort activity and re-established on the next call.
    Set idle_timeout=0 to keep the connection alive indefinitely (use this
    when an embedded worker is running in the same process).
    """

    _MONITOR_INTERVAL = 60  # check for idle every minute

    def __init__(self, queue: Queue, idle_timeout: int = 3600) -> None:
        self._queue = queue
        self._idle_timeout = idle_timeout
        self._connected = False
        self._last_used: float = 0.0
        self._lock = asyncio.Lock()
        self._monitor_task: asyncio.Task[None] | None = None

    async def start(self, *, connect_immediately: bool = False) -> None:
        """Initialise the service. Pass connect_immediately=True when an
        embedded SAQ worker shares this queue and needs it pre-connected."""
        if connect_immediately:
            await self._do_connect()
        if self._idle_timeout > 0:
            self._monitor_task = asyncio.create_task(self._idle_monitor())

    async def stop(self) -> None:
        """Cancel idle monitor and disconnect."""
        if self._monitor_task is not None:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
            self._monitor_task = None
        await self._do_disconnect()

    async def _do_connect(self) -> None:
        await self._queue.connect()
        self._connected = True
        self._last_used = time.monotonic()
        logger.info("saq_queue_connected")

    async def _do_disconnect(self) -> None:
        if self._connected:
            await self._queue.disconnect()
            self._connected = False
            logger.info("saq_queue_disconnected")

    async def _ensure_connected(self) -> None:
        async with self._lock:
            if not self._connected:
                await self._queue.connect()
                self._connected = True
                logger.info("saq_queue_reconnected")
        self._last_used = time.monotonic()

    async def _idle_monitor(self) -> None:
        while True:
            await asyncio.sleep(self._MONITOR_INTERVAL)
            if not self._connected:
                continue
            if time.monotonic() - self._last_used <= self._idle_timeout:
                continue
            async with self._lock:
                if self._connected and time.monotonic() - self._last_used > self._idle_timeout:
                    await self._queue.disconnect()
                    self._connected = False
                    logger.info("saq_queue_idle_disconnect", idle_timeout=self._idle_timeout)

    async def enqueue(
        self,
        function_name: str,
        retries: int = 3,
        timeout_seconds: int = 300,
        **kwargs: object,
    ) -> str:
        await self._ensure_connected()
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
        await self._ensure_connected()
        job = await self._queue.job(job_key)
        if job:
            await job.abort("Cancelled by user")
            logger.info("job_aborted", job_key=job_key)
