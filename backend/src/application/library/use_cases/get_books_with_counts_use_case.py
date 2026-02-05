"""Use case for retrieving books with counts."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetBooksWithCountsUseCase:
    """Use case for retrieving books with highlight and flashcard counts."""

    def __init__(self, book_repository: BookRepositoryProtocol) -> None:
        """Initialize use case with dependencies."""
        self.book_repository = book_repository

    def get_books_with_counts(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> tuple[list[tuple[Book, int, int, list[Tag]]], int]:
        """
        Get books with their highlight and flashcard counts.

        Args:
            user_id: ID of the user whose books to retrieve
            offset: Number of books to skip (default: 0)
            limit: Maximum number of books to return (default: 100)
            include_only_with_flashcards: Include only books which have flashcards
            search_text: Optional text to search for in book title or author

        Returns:
            tuple[list[tuple[Book, highlight_count, flashcard_count, list[Tag]]], total_count]
        """
        user_id_vo = UserId(user_id)
        return self.book_repository.get_books_with_counts(
            user_id=user_id_vo,
            offset=offset,
            limit=limit,
            include_only_with_flashcards=include_only_with_flashcards,
            search_text=search_text,
        )
