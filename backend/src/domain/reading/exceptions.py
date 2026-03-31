"""Reading module domain exceptions."""

from src.domain.common.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    EntityNotFoundError,
)


class BookNotFoundError(EntityNotFoundError):
    """Raised when a book cannot be found."""

    def __init__(self, book_id: int | str | None = None, *, message: str | None = None) -> None:
        if book_id is not None:
            super().__init__("Book", book_id)
        else:
            super().__init__("Book", "unknown")
        if message:
            self.message = message


class ReadingSessionNotFoundError(EntityNotFoundError):
    """Raised when a reading session cannot be found."""

    def __init__(self, session_id: int | None = None) -> None:
        super().__init__("ReadingSession", session_id or "unknown")
        self.session_id = session_id


class HighlightNotFoundError(EntityNotFoundError):
    """Raised when a highlight cannot be found."""

    def __init__(self, highlight_id: int) -> None:
        super().__init__("Highlight", highlight_id)


class HighlightAlreadyDeletedError(BusinessRuleViolationError):
    """Raised when trying to delete an already-deleted highlight."""

    def __init__(self, highlight_id: int) -> None:
        super().__init__(
            rule="highlight_not_deleted",
            message=f"Highlight {highlight_id} is already deleted",
        )


class DuplicateHighlightError(ConflictError):
    """Raised when attempting to create a duplicate highlight."""

    def __init__(self, content_hash: str) -> None:
        super().__init__(
            f"Duplicate highlight with hash {content_hash}",
            {"content_hash": content_hash},
        )


class HighlightTagNotFoundError(EntityNotFoundError):
    """Raised when a highlight tag cannot be found."""

    def __init__(self, tag_id: int) -> None:
        super().__init__("HighlightTag", tag_id)


class DuplicateTagNameError(ConflictError):
    """Raised when attempting to create a tag with a duplicate name."""

    def __init__(self, tag_name: str) -> None:
        super().__init__(
            f"Tag '{tag_name}' already exists for this book",
            {"tag_name": tag_name},
        )


class HighlightTagGroupNotFoundError(EntityNotFoundError):
    """Raised when a highlight tag group cannot be found."""

    def __init__(self, group_id: int) -> None:
        super().__init__("HighlightTagGroup", group_id)


class DuplicateTagGroupNameError(ConflictError):
    """Raised when attempting to create a tag group with a duplicate name."""

    def __init__(self, group_name: str) -> None:
        super().__init__(
            f"Tag group '{group_name}' already exists for this book",
            {"group_name": group_name},
        )
