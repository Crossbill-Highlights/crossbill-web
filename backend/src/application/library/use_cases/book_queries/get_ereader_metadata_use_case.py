"""Get ereader metadata use case."""

from dataclasses import dataclass
from pathlib import Path

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.exceptions import BookNotFoundError

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "book-files" / "book-covers"


@dataclass
class EreaderMetadata:
    """Lightweight book metadata for ereader operations."""

    book_id: int
    title: str
    author: str | None
    has_cover: bool
    has_ebook: bool


class GetEreaderMetadataUseCase:
    """Use case for getting ereader metadata."""

    def __init__(self, book_repository: BookRepositoryProtocol) -> None:
        self.book_repository = book_repository

    def get_metadata_for_ereader(self, client_book_id: str, user_id: int) -> EreaderMetadata:
        """
        Get basic book metadata for ereader operations.

        This method returns lightweight book information that KOReader uses to
        decide whether it needs to upload cover images, epub files, etc.

        Args:
            client_book_id: The client-provided book identifier
            user_id: ID of the user

        Returns:
            EreaderMetadata with book info and file availability flags

        Raises:
            BookNotFoundError: If book is not found for the given client_book_id
        """
        user_id_vo = UserId(user_id)

        book = self.book_repository.find_by_client_book_id(client_book_id, user_id_vo)
        if not book:
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found"
            )

        # Check if cover file exists
        cover_filename = f"{book.id.value}.jpg"
        cover_path = COVERS_DIR / cover_filename
        has_cover = cover_path.is_file()

        # Check if ebook file exists
        has_ebook = book.file_path is not None

        return EreaderMetadata(
            book_id=book.id.value,
            title=book.title,
            author=book.author,
            has_cover=has_cover,
            has_ebook=has_ebook,
        )
