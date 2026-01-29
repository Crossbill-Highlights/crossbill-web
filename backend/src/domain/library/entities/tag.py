"""Tag entity for categorizing books."""

from dataclasses import dataclass
from datetime import UTC, datetime

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import TagId, UserId


@dataclass
class Tag(Entity[TagId]):
    """
    Tag entity for categorizing books.

    Represents a user-defined tag for organizing and filtering books.
    """

    # Identity
    id: TagId
    user_id: UserId

    # Content
    name: str

    # Timestamps
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.name or not self.name.strip():
            raise DomainError("Tag name cannot be empty")

    # Query methods
    def matches_name(self, search: str) -> bool:
        """Check if tag name contains the search string (case-insensitive)."""
        return search.lower() in self.name.lower()

    # Factory methods
    @classmethod
    def create(
        cls,
        user_id: UserId,
        name: str,
    ) -> "Tag":
        """Factory for creating new tag."""
        now = datetime.now(UTC)
        return cls(
            id=TagId.generate(),
            user_id=user_id,
            name=name.strip(),
            created_at=now,
            updated_at=now,
        )

    @classmethod
    def create_with_id(
        cls,
        id: TagId,
        user_id: UserId,
        name: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> "Tag":
        """Factory for reconstituting tag from persistence."""
        return cls(
            id=id,
            user_id=user_id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
        )
