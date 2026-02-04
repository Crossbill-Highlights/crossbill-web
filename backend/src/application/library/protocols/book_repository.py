from typing import Protocol

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class BookRepositoryProtocol(Protocol):
    def find_by_client_book_id(self, client_book_id: str, user_id: UserId) -> Book | None: ...

    def find_by_id(self, book_id: BookId, user_id: UserId) -> Book | None: ...

    def save(self, book: Book) -> Book: ...

    def delete(self, book: Book) -> None: ...

    def get_recently_viewed_books(
        self, user_id: UserId, limit: int = 10
    ) -> list[tuple[Book, int, int, list[Tag]]]: ...

    def get_books_with_counts(
        self,
        user_id: UserId,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> tuple[list[tuple[Book, int, int, list[Tag]]], int]: ...
