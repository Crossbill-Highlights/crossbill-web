"""Use case for enqueuing batch prereading generation for a book."""

import structlog

from src.application.jobs.protocols.job_batch_repository import JobBatchRepositoryProtocol
from src.application.jobs.protocols.job_queue_service import JobQueueServiceProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.application.reading.protocols.ebook_text_extraction_service import (
    EbookTextExtractionServiceProtocol,
)
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.jobs.entities.job_batch import JobBatch, JobBatchType
from src.domain.reading.exceptions import BookNotFoundError

logger = structlog.get_logger(__name__)

MIN_CHAPTER_LENGTH = 50


class EnqueueBookPrereadingUseCase:
    def __init__(
        self,
        chapter_repo: ChapterRepositoryProtocol,
        book_repo: BookRepositoryProtocol,
        batch_repo: JobBatchRepositoryProtocol,
        queue_service: JobQueueServiceProtocol,
        prereading_repo: ChapterPrereadingRepositoryProtocol,
        file_repo: FileRepositoryProtocol,
        text_extraction_service: EbookTextExtractionServiceProtocol,
    ) -> None:
        self._chapter_repo = chapter_repo
        self._book_repo = book_repo
        self._batch_repo = batch_repo
        self._queue_service = queue_service
        self._prereading_repo = prereading_repo
        self._file_repo = file_repo
        self._text_extraction = text_extraction_service

    async def execute(self, book_id: BookId, user_id: UserId) -> JobBatch:
        book = await self._book_repo.find_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id.value)

        if not book.file_path or book.file_type != "epub":
            raise DomainError("Book must be an EPUB with an uploaded file")

        epub_path = await self._file_repo.find_epub(book.id)
        if not epub_path or not epub_path.exists():
            raise BookNotFoundError(book_id.value)

        chapters = await self._chapter_repo.find_all_by_book(book_id, user_id)

        existing = await self._prereading_repo.find_all_by_book_id(book_id)
        already_generated = {p.chapter_id for p in existing}

        # Extract text for each eligible chapter upfront so the worker
        # doesn't need filesystem access
        chapters_with_text: list[tuple[int, str]] = []
        for ch in chapters:
            if not ch.start_xpoint or ch.id in already_generated:
                continue
            try:
                text = self._text_extraction.extract_chapter_text(
                    epub_path=epub_path,
                    start_xpoint=ch.start_xpoint,
                    end_xpoint=ch.end_xpoint,
                )
            except Exception:
                logger.warning("failed_to_extract_chapter_text", chapter_id=ch.id.value)
                continue

            if not text or len(text.strip()) < MIN_CHAPTER_LENGTH:
                continue

            chapters_with_text.append((ch.id.value, text))

        if not chapters_with_text:
            raise DomainError("No eligible chapters found for prereading generation")

        batch = JobBatch.create(
            user_id=user_id,
            batch_type=JobBatchType.CHAPTER_PREREADING,
            reference_id=str(book_id.value),
            total_jobs=len(chapters_with_text),
        )
        batch = await self._batch_repo.save(batch)

        for chapter_id, chapter_text in chapters_with_text:
            try:
                job_key = await self._queue_service.enqueue(
                    "generate_chapter_prereading",
                    retries=3,
                    timeout_seconds=300,
                    batch_id=batch.id.value,
                    chapter_id=chapter_id,
                    user_id=user_id.value,
                    chapter_text=chapter_text,
                )
                batch.add_job_key(job_key)
            except Exception:
                logger.exception(
                    "failed_to_enqueue_job",
                    chapter_id=chapter_id,
                    batch_id=batch.id.value,
                )
                break

        if not batch.job_keys:
            batch.cancel()
            await self._batch_repo.save(batch)
            raise DomainError("Failed to enqueue any jobs for prereading generation")

        batch.total_jobs = min(batch.total_jobs, len(batch.job_keys))
        await self._batch_repo.save(batch)

        logger.info(
            "book_prereading_batch_enqueued",
            batch_id=batch.id.value,
            book_id=book_id.value,
            total_jobs=batch.total_jobs,
        )
        return batch
