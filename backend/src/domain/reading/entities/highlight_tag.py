"""
HighlightTag entity for categorizing highlights.
"""

from dataclasses import dataclass
from datetime import datetime

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects import BookId, HighlightTagId, UserId


@dataclass
class HighlightTag(Entity[HighlightTagId]):
    """
    Tag for categorizing highlights within a book.

    Business Rules:
    - Tag names are scoped per book per user
    - Tags can optionally belong to groups
    """

    id: HighlightTagId
    user_id: UserId
    book_id: BookId
    name: str
    tag_group_id: int | None = None
    group_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate invariants."""
        if not self.name or not self.name.strip():
            raise DomainError("Tag name cannot be empty")

    def rename(self, new_name: str) -> None:
        """
        Rename this tag.

        Args:
            new_name: New tag name

        Raises:
            DomainError: If new name is empty
        """
        if not new_name or not new_name.strip():
            raise DomainError("Tag name cannot be empty")

        self.name = new_name.strip()

    def set_group(self, group_name: str | None) -> None:
        """Set or clear the group for this tag."""
        self.group_name = group_name.strip() if group_name else None
