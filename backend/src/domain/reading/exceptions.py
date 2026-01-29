"""Reading module domain exceptions."""

from src.domain.common.exceptions import DomainError


class BookNotFoundError(DomainError):
    """Raised when a book cannot be found."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class HighlightNotFoundError(DomainError):
    """Raised when a highlight cannot be found."""

    def __init__(self, highlight_id: int) -> None:
        super().__init__(f"Highlight {highlight_id} not found")


class HighlightAlreadyDeletedError(DomainError):
    """Raised when trying to delete an already-deleted highlight."""

    def __init__(self, highlight_id: int) -> None:
        super().__init__(f"Highlight {highlight_id} is already deleted")


class DuplicateHighlightError(DomainError):
    """Raised when attempting to create a duplicate highlight."""

    def __init__(self, content_hash: str) -> None:
        super().__init__(f"Duplicate highlight with hash {content_hash}")
