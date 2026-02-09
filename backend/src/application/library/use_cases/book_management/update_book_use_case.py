"""Update book use case."""

import logging

from src.application.learning.protocols.flashcard_repository import FlashcardRepositoryProtocol
from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.use_cases.book_management.book_tag_association_use_case import (
    BookTagAssociationUseCase,
)
from src.application.reading.protocols.highlight_repository import HighlightRepositoryProtocol
from src.domain.common.value_objects import BookId, UserId
from src.domain.library.entities.book import Book
from src.domain.library.entities.tag import Tag
from src.exceptions import BookNotFoundError
from src.infrastructure.library.schemas import BookUpdateRequest

logger = logging.getLogger(__name__)


class UpdateBookUseCase:
    """Use case for updating book information."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        highlight_repository: HighlightRepositoryProtocol,
        flashcard_repository: FlashcardRepositoryProtocol,
        book_tag_association_use_case: BookTagAssociationUseCase,
    ) -> None:
        self.book_repository = book_repository
        self.highlight_repository = highlight_repository
        self.flashcard_repository = flashcard_repository
        self.book_tag_association_use_case = book_tag_association_use_case

    def update_book(
        self, book_id: int, update_data: BookUpdateRequest, user_id: int
    ) -> tuple[Book, int, int, list[Tag]]:
        """
        Update book information.

        Currently supports updating tags only.

        Args:
            book_id: ID of the book to update
            update_data: Book update request containing tags
            user_id: ID of the user

        Returns:
            Tuple of (book, highlight_count, flashcard_count, tags)

        Raises:
            BookNotFoundError: If book is not found
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Update tags using use case
        tags = self.book_tag_association_use_case.replace_book_tags(
            book_id, update_data.tags, user_id
        )

        # Get counts
        highlight_count = self.highlight_repository.count_by_book(book_id_vo, user_id_vo)
        flashcard_count = self.flashcard_repository.count_by_book(book_id_vo, user_id_vo)

        logger.info(f"Successfully updated book {book_id}")

        # Return domain entities
        return book, highlight_count, flashcard_count, tags
