from typing import Protocol

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.chapter import Chapter


class ChapterRepositoryProtocol(Protocol):
    def get_by_numbers(
        self, book_id: BookId, chapter_numbers: set[int], user_id: UserId
    ) -> dict[int, Chapter]: ...
