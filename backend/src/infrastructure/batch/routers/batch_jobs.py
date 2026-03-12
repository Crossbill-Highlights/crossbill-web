"""API router for batch job processing."""

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from src.application.batch.use_cases.cancel_batch_job_use_case import CancelBatchJobUseCase
from src.application.batch.use_cases.create_batch_prereading_use_case import (
    CreateBatchPrereadingUseCase,
)
from src.application.batch.use_cases.get_batch_job_status_use_case import GetBatchJobStatusUseCase
from src.core import container
from src.domain.common.value_objects.ids import BatchJobId, BookId
from src.domain.identity import User
from src.infrastructure.batch.schemas import BatchJobCreatedResponse, BatchJobResponse
from src.infrastructure.common.dependencies import require_ai_enabled
from src.infrastructure.common.di import inject_use_case
from src.infrastructure.identity import get_current_user

router = APIRouter(tags=["batch"])


@router.post(
    "/books/{book_id}/batch/prereading",
    response_model=BatchJobCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_ai_enabled
async def create_batch_prereading_job(
    book_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CreateBatchPrereadingUseCase = Depends(
        inject_use_case(container.create_batch_prereading_use_case)
    ),
) -> BatchJobCreatedResponse:
    """Create a batch prereading job for all chapters in a book."""
    job = await use_case.execute(
        user_id=current_user.id,
        book_id=BookId(book_id),
    )
    return BatchJobCreatedResponse(
        job_id=job.id.value,
        status=job.status.value,
        total_items=job.total_items,
    )


@router.get(
    "/batch-jobs/{job_id}",
    response_model=BatchJobResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def get_batch_job_status(
    job_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: GetBatchJobStatusUseCase = Depends(
        inject_use_case(container.get_batch_job_status_use_case)
    ),
) -> BatchJobResponse:
    """Get the status of a batch job."""
    job = await use_case.execute(
        user_id=current_user.id,
        job_id=BatchJobId(job_id),
    )
    return BatchJobResponse(
        job_id=job.id.value,
        job_type=job.job_type,
        status=job.status.value,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/batch-jobs/{job_id}/cancel",
    response_model=BatchJobResponse,
    status_code=status.HTTP_200_OK,
)
@require_ai_enabled
async def cancel_batch_job(
    job_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    use_case: CancelBatchJobUseCase = Depends(inject_use_case(container.cancel_batch_job_use_case)),
) -> BatchJobResponse:
    """Cancel a pending or processing batch job."""
    job = await use_case.execute(
        user_id=current_user.id,
        job_id=BatchJobId(job_id),
    )
    return BatchJobResponse(
        job_id=job.id.value,
        job_type=job.job_type,
        status=job.status.value,
        total_items=job.total_items,
        completed_items=job.completed_items,
        failed_items=job.failed_items,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
