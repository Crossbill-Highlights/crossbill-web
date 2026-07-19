"""Use case for retrieving ereader-friendly prereading content for a book."""

from dataclasses import dataclass
from datetime import datetime

from src.application.common.ownership import require_book_by_client_id
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import (
    ChapterRepositoryProtocol,
)
from src.application.reading.protocols.chapter_prereading_repository import (
    ChapterPrereadingRepositoryProtocol,
)
from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.chapter import Chapter
from src.domain.reading.entities.chapter_prereading_content import (
    ChapterPrereadingContent,
)


@dataclass
class EreaderChapterPrereading:
    """Ereader-friendly prereading content for a single chapter.

    Only exposes question text (no AI or user answers) to keep the payload
    small and preserve the active-recall value on the device.
    """

    chapter_id: int
    chapter_name: str
    chapter_number: int | None
    parent_chapter_name: str | None
    summary: str
    keypoints: list[str]
    questions: list[str]
    generated_at: datetime


class GetEreaderBookPrereadingUseCase:
    """Retrieve all chapter prereading content for a book by client_book_id."""

    def __init__(
        self,
        book_repo: BookRepositoryProtocol,
        chapter_repo: ChapterRepositoryProtocol,
        prereading_repo: ChapterPrereadingRepositoryProtocol,
    ) -> None:
        self.book_repo = book_repo
        self.chapter_repo = chapter_repo
        self.prereading_repo = prereading_repo

    async def get_prereading_for_client_book(
        self, client_book_id: str, user_id: UserId
    ) -> list[EreaderChapterPrereading]:
        """Get ereader-friendly prereading for every chapter that has it.

        Chapters are returned in the order provided by ``find_all_by_book``
        (chapter_number ascending, nulls last), and chapters without prereading
        content are omitted.

        Raises:
            BookNotFoundError: If no book matches client_book_id for the user.
        """
        book = await self._resolve_book(client_book_id, user_id)
        chapters = await self.chapter_repo.find_all_by_book(book.id, user_id)
        prereading_by_chapter = await self._build_prereading_lookup(book.id)
        parent_name_by_id = self._build_parent_name_lookup(chapters)
        return self._join_chapters_with_prereading(
            chapters, prereading_by_chapter, parent_name_by_id
        )

    async def _resolve_book(self, client_book_id: str, user_id: UserId) -> Book:
        return await require_book_by_client_id(self.book_repo, client_book_id, user_id)

    async def _build_prereading_lookup(
        self, book_id: BookId
    ) -> dict[int, ChapterPrereadingContent]:
        contents = await self.prereading_repo.find_all_by_book_id(book_id)
        return {content.chapter_id.value: content for content in contents}

    def _build_parent_name_lookup(self, chapters: list[Chapter]) -> dict[int, str]:
        return {chapter.id.value: chapter.name for chapter in chapters}

    def _join_chapters_with_prereading(
        self,
        chapters: list[Chapter],
        prereading_by_chapter: dict[int, ChapterPrereadingContent],
        parent_name_by_id: dict[int, str],
    ) -> list[EreaderChapterPrereading]:
        items: list[EreaderChapterPrereading] = []
        for chapter in chapters:
            content = prereading_by_chapter.get(chapter.id.value)
            if content is None:
                continue
            parent_name = (
                parent_name_by_id.get(chapter.parent_id.value)
                if chapter.parent_id is not None
                else None
            )
            items.append(
                EreaderChapterPrereading(
                    chapter_id=chapter.id.value,
                    chapter_name=chapter.name,
                    chapter_number=chapter.chapter_number,
                    parent_chapter_name=parent_name,
                    summary=content.summary,
                    keypoints=content.keypoints,
                    questions=[q.question for q in content.questions],
                    generated_at=content.generated_at,
                )
            )
        return items
