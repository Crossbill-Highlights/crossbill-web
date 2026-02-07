from typing import Protocol

from src.domain.common.value_objects.ids import BookId, UserId


class EbookTextExtractionServiceProtocol(Protocol):
    def extract_text(
        self, book_id: BookId, user_id: UserId, start: str | int, end: str | int
    ) -> str: ...

    def extract_chapter_text(
        self,
        book_id: BookId,
        user_id: UserId,
        start_xpoint: str,
        end_xpoint: str | None,
    ) -> str: ...
