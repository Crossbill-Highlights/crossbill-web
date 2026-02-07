"""Use case for ebook deletion operations."""

import logging

from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects.ids import BookId

logger = logging.getLogger(__name__)


class EbookDeletionUseCase:
    """Use case for deleting ebook files."""

    def __init__(self, file_repository: FileRepositoryProtocol) -> None:
        """Initialize use case with dependencies."""
        self.file_repository = file_repository

    def delete_ebook(self, book_id: int) -> bool:
        """
        Delete ebook file (EPUB or PDF) from disk.

        Attempts to delete both EPUB and PDF files. Returns True if either succeeded.

        Args:
            book_id: ID of the book

        Returns:
            True if at least one file was deleted, False if no files existed
        """
        book_id_obj = BookId(book_id)

        epub_deleted = self.file_repository.delete_epub(book_id_obj)
        pdf_deleted = self.file_repository.delete_pdf(book_id_obj)

        if epub_deleted or pdf_deleted:
            logger.info(f"Deleted ebook file(s) for book {book_id}")
            return True

        logger.info(f"No ebook files found for book {book_id}")
        return False
