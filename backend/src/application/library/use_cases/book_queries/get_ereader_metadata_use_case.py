"""Get ereader metadata use case."""

from dataclasses import dataclass

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.domain.common.value_objects import UserId
from src.domain.reading.exceptions import BookNotFoundError


@dataclass
class EreaderMetadata:
    """Lightweight book metadata for ereader operations."""

    book_id: int
    title: str
    author: str | None
    cover_file: str | None
    has_ebook: bool


class GetEreaderMetadataUseCase:
    """Use case for getting ereader metadata."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
    ) -> None:
        self.book_repository = book_repository

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

        cover_file = book.cover_file
        has_ebook = book.ebook_file is not None

        return EreaderMetadata(
            book_id=book.id.value,
            title=book.title,
            author=book.author,
            cover_file=cover_file,
            has_ebook=has_ebook,
        )
