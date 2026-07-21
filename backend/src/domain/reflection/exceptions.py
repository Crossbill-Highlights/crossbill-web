"""Reflection domain exceptions."""

from src.domain.common.exceptions import EntityNotFoundError


class BookReflectionNotFoundError(EntityNotFoundError):
    """Raised when a book reflection cannot be found."""

    def __init__(self, book_reflection_id: int) -> None:
        super().__init__("BookReflection", book_reflection_id)
        self.book_reflection_id = book_reflection_id
