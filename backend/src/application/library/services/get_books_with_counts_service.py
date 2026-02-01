from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag
from src.infrastructure.library.repositories.book_repository import BookRepository


class GetBooksWithCountsService:
    """Application service for retrieving books with highlight and flashcard counts."""

    def __init__(self, db: Session) -> None:
        self.repository = BookRepository(db)

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
        return self.repository.get_books_with_counts(
            user_id=user_id_vo,
            offset=offset,
            limit=limit,
            include_only_with_flashcards=include_only_with_flashcards,
            search_text=search_text,
        )
