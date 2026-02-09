"""Delete book use case."""

import logging

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.use_cases.book_files.ebook_deletion_use_case import (
    EbookDeletionUseCase,
)
from src.domain.common.value_objects import BookId, UserId
from src.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)


class DeleteBookUseCase:
    """Use case for deleting books."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        ebook_deletion_use_case: EbookDeletionUseCase,
    ) -> None:
        self.book_repository = book_repository
        self.ebook_deletion_use_case = ebook_deletion_use_case

    def delete_book(self, book_id: int, user_id: int) -> None:
        """
        Delete a book and all its contents (hard delete).

        This will permanently delete the book, all its chapters, highlights,
        cover image, and epub file.

        Args:
            book_id: ID of the book to delete
            user_id: ID of the user

        Raises:
            BookNotFoundError: If book is not found
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        self.ebook_deletion_use_case.delete_ebook(book_id)
        self.book_repository.delete(book)

        logger.info(f"Successfully deleted book {book_id}")
