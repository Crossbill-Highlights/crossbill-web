"""API router for job batch management."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.application.jobs.use_cases.cancel_job_batch_use_case import CancelJobBatchUseCase
from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.application.jobs.use_cases.get_active_book_batch_use_case import (
    GetActiveBookBatchUseCase,
)
from src.application.jobs.use_cases.get_job_batch_use_case import GetJobBatchUseCase
from src.core import container
from src.domain.common.value_objects.ids import BookId, JobBatchId, UserId
from src.domain.identity import User
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchType
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user
from src.infrastructure.jobs.schemas.job_batch_schemas import JobBatchResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(batch: JobBatch) -> JobBatchResponse:
    return JobBatchResponse(
        id=batch.id.value,
        batch_type=batch.batch_type.value,
        reference_id=batch.reference_id,
        total_jobs=batch.total_jobs,
        completed_jobs=batch.completed_jobs,
        failed_jobs=batch.failed_jobs,
        status=batch.status.value,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
    )


@router.post(
    "/books/{book_id}/prereading",
    response_model=JobBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@require_ai_enabled
async def enqueue_book_prereading(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: EnqueueBookPrereadingUseCase = Depends(
        inject_use_case(container.jobs.enqueue_book_prereading_use_case)
    ),
) -> JobBatchResponse:
    """Enqueue prereading generation for all chapters of a book."""
    batch = await use_case.execute(
        BookId(book_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)


@router.get(
    "/books/{book_id}/prereading",
    response_model=JobBatchResponse | None,
    status_code=status.HTTP_200_OK,
)
async def get_active_book_prereading_batch(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetActiveBookBatchUseCase = Depends(
        inject_use_case(container.jobs.get_active_book_batch_use_case)
    ),
) -> JobBatchResponse | None:
    """Get the active prereading batch for a book, if any."""
    batch = await use_case.execute(
        BookId(book_id),
        UserId(current_user.id.value),
        JobBatchType.CHAPTER_PREREADING,
    )
    return _to_response(batch) if batch else None


@router.get(
    "/batches/{batch_id}",
    response_model=JobBatchResponse,
    status_code=status.HTTP_200_OK,
)
async def get_job_batch(
    batch_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetJobBatchUseCase = Depends(inject_use_case(container.jobs.get_job_batch_use_case)),
) -> JobBatchResponse:
    """Get job batch status."""
    batch = await use_case.execute(
        JobBatchId(batch_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)


@router.delete(
    "/batches/{batch_id}",
    response_model=JobBatchResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_job_batch(
    batch_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CancelJobBatchUseCase = Depends(
        inject_use_case(container.jobs.cancel_job_batch_use_case)
    ),
) -> JobBatchResponse:
    """Cancel a job batch and abort all pending/active jobs."""
    batch = await use_case.execute(
        JobBatchId(batch_id),
        UserId(current_user.id.value),
    )
    return _to_response(batch)
