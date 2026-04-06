"""Get ereader metadata use case."""

from dataclasses import dataclass

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.domain.reading.exceptions import BookNotFoundError


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

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository
        self.file_repository = file_repository

    async def get_metadata_for_ereader(self, client_book_id: str, user_id: int) -> EreaderMetadata:
        """
        Get basic book metadata for ereader operations.

        Args:
            client_book_id: The client-provided book identifier
            user_id: ID of the user

        Returns:
            EreaderMetadata with book info and file availability flags

        Raises:
            BookNotFoundError: If book is not found for the given client_book_id
        """
        user_id_vo = UserId(user_id)

        book = await self.book_repository.find_by_client_book_id(client_book_id, user_id_vo)
        if not book:
            raise BookNotFoundError(client_book_id)

        has_cover = await self.file_repository.has_cover(book.id)
        has_ebook = book.file_path is not None

        return EreaderMetadata(
            book_id=book.id.value,
            title=book.title,
            author=book.author,
            has_cover=has_cover,
            has_ebook=has_ebook,
        )
