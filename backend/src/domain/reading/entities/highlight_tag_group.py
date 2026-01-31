from dataclasses import dataclass

from src.domain.common.entity import Entity
from src.domain.common.exceptions import DomainError
from src.domain.common.value_objects.ids import BookId, HighlightTagGroupId


@dataclass
class HighlightTagGroup(Entity[HighlightTagGroupId]):
    """Tag group for organizing highlight tags within a book."""

    id: HighlightTagGroupId
    book_id: BookId
    name: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise DomainError("Tag group name cannot be empty")

    def rename(self, new_name: str) -> None:
        """Rename the tag group."""
        if not new_name or not new_name.strip():
            raise DomainError("Tag group name cannot be empty")
        object.__setattr__(self, "name", new_name.strip())

    @classmethod
    def create(cls, book_id: BookId, name: str) -> "HighlightTagGroup":
        """Create a new tag group."""
        return cls(
            id=HighlightTagGroupId.generate(),
            book_id=book_id,
            name=name.strip(),
        )

    @classmethod
    def create_with_id(
        cls,
        id: HighlightTagGroupId,
        book_id: BookId,
        name: str,
    ) -> "HighlightTagGroup":
        """Reconstitute a tag group from persistence."""
        return cls(
            id=id,
            book_id=book_id,
            name=name,
        )
