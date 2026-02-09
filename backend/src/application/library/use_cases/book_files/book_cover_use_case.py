"""
Book cover management use case.

Handles cover file operations and validation for the library context.
"""

import logging
from pathlib import Path

from fastapi import HTTPException, UploadFile

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common import ValidationError
from src.domain.common.value_objects import BookId, UserId
from src.exceptions import BookNotFoundError

logger = logging.getLogger(__name__)

# Maximum cover image size (5MB)
MAX_COVER_SIZE = 5 * 1024 * 1024

# Magic bytes for image file type validation
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",  # WebP starts with RIFF, followed by size, then WEBP
}

# WebP header requires at least 12 bytes for validation
WEBP_MIN_HEADER_SIZE = 12


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

    def upload_cover(self, book_id: int, cover: UploadFile, user_id: int) -> str:
        """
        Upload a book cover image.

        This method accepts an uploaded image file and saves it as the book's cover.
        The cover is saved to the covers directory with the filename {book_id}.jpg
        and the book's cover field is updated in the database.

        Args:
            book_id: ID of the book
            cover: Uploaded image file (JPEG, PNG, or WebP)
            user_id: ID of the user uploading the cover

        Returns:
            Cover URL path

        Raises:
            BookNotFoundError: If book is not found
            HTTPException: If file validation fails or upload fails
        """
        book_id_vo = BookId(book_id)
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if cover.content_type not in allowed_types:
            raise ValidationError("Only JPEG, PNG, and WebP images are allowed")

        content = cover.file.read(MAX_COVER_SIZE + 1)
        if len(content) > MAX_COVER_SIZE:
            raise ValidationError("File too large (max 5MB)")

        file_type = self._validate_image_type(content)
        if file_type not in {"jpeg", "png", "webp"}:
            raise ValidationError("Invalid image file")

        # TODO: Do not set id here. Set it in the repository implementation
        cover_filename = f"{book_id}.jpg"
        self.file_repository.save_cover(book_id_vo, content, cover_filename)

        # TODO: Do we need to save the cover image api url to the database? Frontend could infer the path by book id...?
        # Update book's cover field in database using domain method
        cover_url = f"/api/v1/books/{book_id}/cover"
        book.update_cover(cover_url)
        self.book_repository.save(book)

        return cover_url

    def upload_cover_by_client_book_id(
        self, client_book_id: str, cover: UploadFile, user_id: int
    ) -> str:
        """
        Upload a book cover image using client_book_id.

        This method looks up the book by client_book_id and then uploads the cover.
        Used by KOReader which identifies books by client_book_id.

        Args:
            client_book_id: The client-provided book identifier
            cover: Uploaded image file (JPEG, PNG, or WebP)
            user_id: ID of the user uploading the cover

        Returns:
            Cover URL path

        Raises:
            BookNotFoundError: If book is not found for the given client_book_id
            HTTPException: If file validation fails or upload fails
        """
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_client_book_id(client_book_id, user_id_vo)
        if not book:
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found"
            )

        # Delegate to the existing upload_cover method using book.id
        return self.upload_cover(book.id.value, cover, user_id)

    def get_cover_path(self, book_id: int, user_id: int) -> Path:
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
        book = self.book_repository.find_by_id(book_id_vo, user_id_vo)
        if not book:
            raise BookNotFoundError(book_id)

        # Find cover file
        cover_path = self.file_repository.find_cover(book_id_vo)
        if not cover_path:
            raise HTTPException(status_code=404, detail="Cover not found")

        return cover_path

    @staticmethod
    def _validate_image_type(content: bytes) -> str | None:
        """
        Validate image type by checking magic bytes.

        Args:
            content: The file content as bytes

        Returns:
            Image type (jpeg, png, webp) or None if not recognized
        """
        # Check JPEG
        if content.startswith(b"\xff\xd8\xff"):
            return "jpeg"

        # Check PNG
        if content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"

        # Check WebP (RIFF header followed by WEBP)
        if (
            content.startswith(b"RIFF")
            and len(content) > WEBP_MIN_HEADER_SIZE
            and content[8:12] == b"WEBP"
        ):
            return "webp"

        return None
