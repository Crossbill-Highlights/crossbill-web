"""
Book cover management use case.

Handles cover file operations for the library context.
"""

import logging
from pathlib import Path

from fastapi import HTTPException

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects import BookId, UserId
from src.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)


class BookCoverUseCase:
    """Use case for book cover management operations."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
            file_repository: File repository protocol implementation
        """
        self.book_repository = book_repository
        self.file_repository = file_repository

    async def get_cover_path(self, book_id: int, user_id: int) -> Path:
        """
        Get the file path for a book cover with ownership verification.

        Args:
            book_id: ID of the book
            user_id: ID of the user requesting the cover

        Returns:
            Path to the cover file

        Raises:
            BookNotFoundError: If book is not found or user doesn't own it
            HTTPException: If cover file doesn't exist
        """
        # Convert primitives to value objects
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        # Verify book exists and user owns it
        book = await self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Find cover file
        cover_path = await self.file_repository.find_cover(book_id_vo)
        if not cover_path:
            # TODO: Remove Fastapi dependency from application layer
            raise HTTPException(status_code=404, detail="Cover not found")

        return cover_path
