"""Tests for EnqueueBookPrereadingUseCase."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.jobs.use_cases.enqueue_book_prereading_use_case import (
    EnqueueBookPrereadingUseCase,
)
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, ChapterId, UserId
from src.domain.jobs.entities.job_batch import JobBatchType
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.exceptions import BookNotFoundError


def _make_chapter(chapter_id: int, book_id: int = 1) -> Chapter:
    return Chapter.create_with_id(
        id=ChapterId(chapter_id),
        book_id=BookId(book_id),
        name=f"Chapter {chapter_id}",
        created_at=datetime.now(UTC),
        start_xpoint=f"/body/chapter[{chapter_id}]",
    )


def _make_book_mock() -> MagicMock:
    book = MagicMock()
    book.file_path = "/app/book-files/epubs/test.epub"
    book.file_type = "epub"
    return book


@pytest.fixture
def chapter_repo() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def book_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_id.return_value = _make_book_mock()
    return repo


@pytest.fixture
def batch_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save.side_effect = lambda b: b
    return repo


@pytest.fixture
def queue_service() -> AsyncMock:
    service = AsyncMock()
    service.enqueue = AsyncMock(side_effect=lambda fn, **kw: f"saq:job:{kw.get('chapter_id', 0)}")
    return service


@pytest.fixture
def prereading_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_all_by_book_id.return_value = []
    return repo


@pytest.fixture
def file_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.get_epub.return_value = b"fake epub content"
    return repo


@pytest.fixture
def text_extraction_service() -> MagicMock:
    service = MagicMock()
    service.extract_chapter_text.return_value = "A" * 100
    return service


@pytest.fixture
def use_case(
    chapter_repo: AsyncMock,
    book_repo: AsyncMock,
    batch_repo: AsyncMock,
    queue_service: AsyncMock,
    prereading_repo: AsyncMock,
    file_repo: AsyncMock,
    text_extraction_service: MagicMock,
) -> EnqueueBookPrereadingUseCase:
    return EnqueueBookPrereadingUseCase(
        chapter_repo=chapter_repo,
        book_repo=book_repo,
        batch_repo=batch_repo,
        queue_service=queue_service,
        prereading_repo=prereading_repo,
        file_repo=file_repo,
        text_extraction_service=text_extraction_service,
    )


class TestEnqueueBookPrereading:
    async def test_enqueues_one_job_per_chapter(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        chapters = [_make_chapter(1), _make_chapter(2), _make_chapter(3)]
        chapter_repo.find_all_by_book.return_value = chapters

        batch = await use_case.execute(BookId(1), UserId(1))

        assert batch.total_jobs == 3
        assert batch.batch_type == JobBatchType.CHAPTER_PREREADING
        assert batch.reference_id == "1"
        assert len(batch.job_keys) == 3
        assert queue_service.enqueue.call_count == 3

    async def test_enqueue_passes_chapter_text(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        chapter_repo.find_all_by_book.return_value = [_make_chapter(1)]

        await use_case.execute(BookId(1), UserId(1))

        call_kwargs = queue_service.enqueue.call_args.kwargs
        assert "chapter_text" in call_kwargs
        assert len(call_kwargs["chapter_text"]) > 0

    async def test_skips_chapters_without_xpoint(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        ch_with = _make_chapter(1)
        ch_without = Chapter.create_with_id(
            id=ChapterId(2),
            book_id=BookId(1),
            name="No XPoint",
            created_at=ch_with.created_at,
            start_xpoint=None,
        )
        chapter_repo.find_all_by_book.return_value = [ch_with, ch_without]

        batch = await use_case.execute(BookId(1), UserId(1))

        assert batch.total_jobs == 1
        assert queue_service.enqueue.call_count == 1

    async def test_skips_chapters_with_existing_prereading(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        prereading_repo: AsyncMock,
        queue_service: AsyncMock,
    ) -> None:
        chapters = [_make_chapter(1), _make_chapter(2), _make_chapter(3)]
        chapter_repo.find_all_by_book.return_value = chapters

        existing = MagicMock()
        existing.chapter_id = ChapterId(2)
        prereading_repo.find_all_by_book_id.return_value = [existing]

        batch = await use_case.execute(BookId(1), UserId(1))

        assert batch.total_jobs == 2
        assert queue_service.enqueue.call_count == 2

    async def test_skips_chapters_with_short_text(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
        text_extraction_service: MagicMock,
        queue_service: AsyncMock,
    ) -> None:
        chapter_repo.find_all_by_book.return_value = [_make_chapter(1)]
        text_extraction_service.extract_chapter_text.return_value = "Short"

        with pytest.raises(DomainError, match="No eligible chapters"):
            await use_case.execute(BookId(1), UserId(1))

    async def test_raises_when_book_not_found(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        book_repo: AsyncMock,
    ) -> None:
        book_repo.find_by_id.return_value = None

        with pytest.raises(BookNotFoundError):
            await use_case.execute(BookId(999), UserId(1))

    async def test_raises_when_no_eligible_chapters(
        self,
        use_case: EnqueueBookPrereadingUseCase,
        chapter_repo: AsyncMock,
    ) -> None:
        chapter_repo.find_all_by_book.return_value = []

        with pytest.raises(DomainError, match="No eligible chapters"):
            await use_case.execute(BookId(1), UserId(1))
