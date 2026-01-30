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


class HighlightTagNotFoundError(DomainError):
    """Raised when a highlight tag cannot be found."""

    def __init__(self, tag_id: int) -> None:
        super().__init__(f"Highlight tag {tag_id} not found")


class DuplicateTagNameError(DomainError):
    """Raised when attempting to create a tag with a duplicate name."""

    def __init__(self, tag_name: str) -> None:
        super().__init__(f"Tag '{tag_name}' already exists for this book")


class HighlightTagGroupNotFoundError(DomainError):
    """Raised when a highlight tag group cannot be found."""

    def __init__(self, group_id: int) -> None:
        super().__init__(f"Highlight tag group {group_id} not found")


class DuplicateTagGroupNameError(DomainError):
    """Raised when attempting to create a tag group with a duplicate name."""

    def __init__(self, group_name: str) -> None:
        super().__init__(f"Tag group '{group_name}' already exists for this book")
