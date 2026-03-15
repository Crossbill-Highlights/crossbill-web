"""Use case for retrieving books with counts."""

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag


class GetBooksWithCountsUseCase:
    """Use case for retrieving books with highlight and flashcard counts."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        """Initialize use case with dependencies."""
        self.book_repository = book_repository
        self.file_repository = file_repository

    async def get_books_with_counts(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
        include_only_with_flashcards: bool = False,
        search_text: str | None = None,
    ) -> tuple[list[tuple[Book, int, int, list[Tag], bool]], int]:
        """
        Get books with their highlight and flashcard counts.

        Args:
            user_id: ID of the user whose books to retrieve
            offset: Number of books to skip (default: 0)
            limit: Maximum number of books to return (default: 100)
            include_only_with_flashcards: Include only books which have flashcards
            search_text: Optional text to search for in book title or author

        Returns:
            tuple[list[tuple[Book, highlight_count, flashcard_count, list[Tag], has_cover]], total_count]
        """
        user_id_vo = UserId(user_id)
        results, total = await self.book_repository.get_books_with_counts(
            user_id=user_id_vo,
            offset=offset,
            limit=limit,
            include_only_with_flashcards=include_only_with_flashcards,
            search_text=search_text,
        )

        results_with_cover = [
            (
                book,
                h_count,
                f_count,
                tags,
                await self.file_repository.find_cover(book.id) is not None,
            )
            for book, h_count, f_count, tags in results
        ]

        return results_with_cover, total
