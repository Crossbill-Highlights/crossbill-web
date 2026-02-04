from typing import Protocol

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.chapter import Chapter


class ChapterRepositoryProtocol(Protocol):
    def get_by_numbers(
        self, book_id: BookId, chapter_numbers: set[int], user_id: UserId
    ) -> dict[int, Chapter]: ...

    def sync_chapters_from_toc(
        self, book_id: BookId, user_id: UserId, chapters: list[tuple[str, int, str | None]]
    ) -> int: ...
