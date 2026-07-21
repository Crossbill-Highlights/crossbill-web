"""Protocol for BookReflection repository."""

from typing import Protocol

from src.domain.common.value_objects import BookId, UserId
from src.domain.reflection.entities.book_reflection import BookReflection


class BookReflectionRepositoryProtocol(Protocol):
    """Protocol for BookReflection repository operations."""

    async def find_by_book_id(self, book_id: BookId, user_id: UserId) -> BookReflection | None:
        """Find the reflection for a book, scoped to the user."""
        ...

    async def save(self, reflection: BookReflection) -> BookReflection:
        """Create or update a reflection, replacing note association rows."""
        ...
