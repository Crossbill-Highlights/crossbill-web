from typing import Protocol

from src.domain.common.value_objects import ContentHash
from src.domain.common.value_objects.ids import BookId, HighlightId, ReadingSessionId, UserId
from src.domain.learning.entities import Flashcard
from src.domain.library.entities.book import Book
from src.domain.library.entities.chapter import Chapter
from src.domain.reading import Highlight, HighlightTag


class HighlightRepositoryProtocol(Protocol):
    def find_by_id(self, highlight_id: HighlightId, user_id: UserId) -> Highlight | None: ...

    def find_by_id_with_relations(
        self, highlight_id: HighlightId, user_id: UserId
    ) -> tuple[Highlight, list[Flashcard], list[HighlightTag]] | None: ...

    def find_by_ids_with_tags(
        self, highlight_ids: list[HighlightId], user_id: UserId
    ) -> list[tuple[Highlight, Chapter | None, list[HighlightTag]]]: ...

    def find_by_book_id(self, book_id: BookId, user_id: UserId) -> list[Highlight]: ...

    def count_by_book(self, book_id: BookId, user_id: UserId) -> int: ...

    def get_highlights_by_session_ids(
        self,
        session_ids: list[ReadingSessionId],
        user_id: UserId,
    ) -> dict[ReadingSessionId, list[Highlight]]: ...

    def get_existing_hashes(
        self, user_id: UserId, book_id: BookId, hashes: list[ContentHash]
    ) -> set[ContentHash]: ...

    def search(
        self,
        search_text: str,
        user_id: UserId,
        book_id: BookId | None = None,
        limit: int = 100,
    ) -> list[tuple[Highlight, Book, Chapter | None, list[HighlightTag], list[Flashcard]]]: ...

    def save(self, highlight: Highlight) -> Highlight: ...

    def bulk_save(self, highlights: list[Highlight]) -> list[Highlight]: ...

    def soft_delete_by_ids(
        self,
        highlight_ids: list[HighlightId],
        user_id: UserId,
        book_id: BookId,
    ) -> int: ...
