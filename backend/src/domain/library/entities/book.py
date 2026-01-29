from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, UserId


@dataclass
class Book(Entity[BookId]):
    """
    Book aggregate root.

    Represents a book in a user's library.
    """

    # Identity
    id: BookId
    user_id: UserId

    # Essential metadata
    title: str

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Optional fields
    author: str | None = None
    client_book_id: str | None = None  # From KOReader for deduplication
    isbn: str | None = None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    cover: str | None = None
    file_path: str | None = None
    file_type: str | None = None
    last_viewed: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.title or not self.title.strip():
            raise DomainError("Book title cannot be empty")

        if self.page_count is not None and self.page_count < 0:
            raise DomainError("Page count cannot be negative")

    # Query methods
    def has_been_viewed(self) -> bool:
        """Check if book has been viewed."""
        return self.last_viewed is not None

    # Command methods
    def mark_as_viewed(self) -> None:
        """Update last viewed timestamp to now."""
        self.last_viewed = datetime.now(UTC)

    # Factory methods
    @classmethod
    def create(
        cls,
        user_id: UserId,
        title: str,
        client_book_id: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        description: str | None = None,
        language: str | None = None,
        page_count: int | None = None,
        cover: str | None = None,
        file_path: str | None = None,
        file_type: str | None = None,
    ) -> "Book":
        """Factory for creating new book."""
        now = datetime.now(UTC)
        return cls(
            id=BookId.generate(),
            user_id=user_id,
            title=title.strip(),
            client_book_id=client_book_id,
            author=author.strip() if author else None,
            isbn=isbn,
            description=description,
            language=language,
            page_count=page_count,
            cover=cover,
            file_path=file_path,
            file_type=file_type,
            created_at=now,
            updated_at=now,
            last_viewed=None,
        )

    @classmethod
    def create_with_id(
        cls,
        id: BookId,
        user_id: UserId,
        title: str,
        created_at: datetime,
        updated_at: datetime,
        client_book_id: str | None = None,
        author: str | None = None,
        isbn: str | None = None,
        description: str | None = None,
        language: str | None = None,
        page_count: int | None = None,
        cover: str | None = None,
        file_path: str | None = None,
        file_type: str | None = None,
        last_viewed: datetime | None = None,
    ) -> "Book":
        """Factory for reconstituting book from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            title=title,
            client_book_id=client_book_id,
            author=author,
            isbn=isbn,
            description=description,
            language=language,
            page_count=page_count,
            cover=cover,
            file_path=file_path,
            file_type=file_type,
            created_at=created_at,
            updated_at=updated_at,
            last_viewed=last_viewed,
        )
