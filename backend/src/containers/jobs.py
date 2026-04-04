"""DI container for jobs module."""

from dependency_injector import containers, providers

from src.application.jobs.use_cases.cancel_job_batch_use_case import CancelJobBatchUseCase
from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.application.jobs.use_cases.get_active_book_batch_use_case import (
    GetActiveBookBatchUseCase,
)
from src.application.jobs.use_cases.get_job_batch_use_case import GetJobBatchUseCase


class JobsContainer(containers.DeclarativeContainer):
    """Container for job-related use cases."""

    job_batch_repository = providers.Dependency()
    job_queue_service = providers.Dependency()
    chapter_repository = providers.Dependency()
    book_repository = providers.Dependency()
    chapter_prereading_repository = providers.Dependency()
    file_repository = providers.Dependency()
    ebook_text_extraction_service = providers.Dependency()

    enqueue_book_prereading_use_case = providers.Factory(
        EnqueueBookPrereadingUseCase,
        chapter_repo=chapter_repository,
        book_repo=book_repository,
        batch_repo=job_batch_repository,
        queue_service=job_queue_service,
        prereading_repo=chapter_prereading_repository,
        file_repo=file_repository,
        text_extraction_service=ebook_text_extraction_service,
    )

    get_job_batch_use_case = providers.Factory(
        GetJobBatchUseCase,
        batch_repo=job_batch_repository,
    )

    cancel_job_batch_use_case = providers.Factory(
        CancelJobBatchUseCase,
        batch_repo=job_batch_repository,
        queue_service=job_queue_service,
    )

    get_active_book_batch_use_case = providers.Factory(
        GetActiveBookBatchUseCase,
        batch_repo=job_batch_repository,
    )
