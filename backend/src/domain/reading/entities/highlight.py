"""
Highlight aggregate root.

Encapsulates all business rules for managing highlights.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.common.aggregate_root import AggregateRoot
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import (
    BookId,
    ChapterId,
    ContentHash,
    HighlightId,
    UserId,
    XPointRange,
)


@dataclass
class Highlight(AggregateRoot[HighlightId]):
    """
    Highlight aggregate root.

    Represents a text highlight from an e-reader with optional annotations.

    Business Rules:
    - Cannot have empty text
    - Content hash is computed from text (for deduplication)
    - Soft deletion is supported (deleted_at timestamp)
    - Tags can be added/removed
    - Notes can be updated
    """

    # Identity
    id: HighlightId
    user_id: UserId
    book_id: BookId

    # Content
    text: str
    content_hash: ContentHash

    # Position (optional - may not always be available from e-reader)
    chapter_id: ChapterId | None = None
    xpoints: XPointRange | None = None
    page: int | None = None

    # Annotation
    note: str | None = None

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None

    # Relationships
    _tag_ids: list[int] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        if self.page is not None and self.page < 0:
            raise DomainError("Page number cannot be negative")

    # Query methods

    def is_deleted(self) -> bool:
        """Check if this highlight has been soft-deleted."""
        return self.deleted_at is not None

    def has_note(self) -> bool:
        """Check if this highlight has an associated note."""
        return self.note is not None and len(self.note.strip()) > 0

    def has_position_info(self) -> bool:
        """Check if this highlight has position information (xpoints or page)."""
        return self.xpoints is not None or self.page is not None

    # Command methods (state changes)

    def soft_delete(self) -> None:
        """
        Soft delete this highlight.

        Raises:
            DomainError: If highlight is already deleted
        """
        if self.is_deleted():
            raise DomainError(f"Highlight {self.id} is already deleted")

        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """
        Restore a soft-deleted highlight.

        Raises:
            DomainError: If highlight is not deleted
        """
        if not self.is_deleted():
            raise DomainError(f"Highlight {self.id} is not deleted")

        self.deleted_at = None

    def update_note(self, note: str | None) -> None:
        """
        Update the note attached to this highlight.

        Args:
            note: New note text, or None to remove note
        """
        self.note = note.strip() if note else None

    def associate_with_chapter(self, chapter_id: ChapterId) -> None:
        """Associate this highlight with a chapter."""
        self.chapter_id = chapter_id

    # Factory methods

    @classmethod
    def create(
        cls,
        user_id: UserId,
        book_id: BookId,
        text: str,
        chapter_id: ChapterId | None = None,
        xpoints: XPointRange | None = None,
        page: int | None = None,
        note: str | None = None,
    ) -> "Highlight":
        """
        Factory method for creating a new highlight.

        Args:
            user_id: User who created the highlight
            book_id: Book this highlight belongs to
            text: Highlighted text
            chapter_id: Optional chapter reference
            xpoints: Optional XPoint range for precise position
            page: Optional page number
            note: Optional note/annotation

        Returns:
            New Highlight instance

        Raises:
            ValueError: If text is invalid
        """
        highlight_text = text

        # Compute content hash for deduplication
        content_hash = ContentHash.compute(text)

        return cls(
            id=HighlightId.generate(),  # Generate new ID
            user_id=user_id,
            book_id=book_id,
            text=highlight_text,
            content_hash=content_hash,
            chapter_id=chapter_id,
            xpoints=xpoints,
            page=page,
            note=note.strip() if note else None,
            created_at=datetime.now(UTC),
            deleted_at=None,
            _tag_ids=[],
        )

    @classmethod
    def create_with_id(
        cls,
        id: HighlightId,
        user_id: UserId,
        book_id: BookId,
        text: str,
        content_hash: ContentHash,
        created_at: datetime,
        chapter_id: ChapterId | None = None,
        xpoints: XPointRange | None = None,
        page: int | None = None,
        note: str | None = None,
        deleted_at: datetime | None = None,
    ) -> "Highlight":
        """
        Factory method for reconstituting highlight from persistence.

        Used by repositories when loading from database.
        """
        return cls(
            id=id,
            user_id=user_id,
            book_id=book_id,
            text=text,
            content_hash=content_hash,
            chapter_id=chapter_id,
            xpoints=xpoints,
            page=page,
            note=note,
            created_at=created_at,
            deleted_at=deleted_at,
            _tag_ids=[],
        )
