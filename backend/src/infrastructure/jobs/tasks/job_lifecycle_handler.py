"""SAQ lifecycle handler for updating JobBatch progress."""

import structlog
from saq import Job
from saq.types import Context

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.domain.common.value_objects.ids import JobBatchId

logger = structlog.get_logger(__name__)

_TERMINAL_COMPLETE = "complete"
_TERMINAL_FAILED = "failed"
_TERMINAL_ABORTED = "aborted"


class JobLifecycleHandler:
    def __init__(self, batch_repo: JobBatchRepositoryProtocol) -> None:
        self._batch_repo = batch_repo

    async def after_process(self, ctx: Context) -> None:
        job: Job | None = ctx.get("job")  # type: ignore[assignment]
        if job is None:
            return
        batch_id = (job.kwargs or {}).get("batch_id")
        if batch_id is None:
            return

        status = job.status
        if status not in (_TERMINAL_COMPLETE, _TERMINAL_FAILED, _TERMINAL_ABORTED):
            return

        bid = JobBatchId(batch_id)
        if status == _TERMINAL_COMPLETE:
            batch = await self._batch_repo.atomic_increment_completed(bid)
        else:
            batch = await self._batch_repo.atomic_increment_failed(bid)

        if not batch:
            logger.warning("batch_not_found_in_after_process", batch_id=batch_id)
            return

        logger.info(
            "batch_progress_updated",
            batch_id=batch_id,
            completed=batch.completed_jobs,
            failed=batch.failed_jobs,
            total=batch.total_jobs,
            status=batch.status,
        )
