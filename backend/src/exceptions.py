"""Custom exception hierarchy for Crossbill application."""

from fastapi import HTTPException
from starlette import status


class CrossbillError(Exception):
    """Base exception for all Crossbill errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        """Initialize exception with message and optional status code."""
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(CrossbillError):
    """Resource not found error."""

    def __init__(self, message: str) -> None:
        """Initialize with message and 404 status code."""
        super().__init__(message, status_code=404)


class BookNotFoundError(NotFoundError):
    """Book not found error."""

    def __init__(self, book_id: int | None = None, *, message: str | None = None) -> None:
        """Initialize with book ID or custom message."""
        self.book_id = book_id
        if message:
            super().__init__(message)
        elif book_id is not None:
            super().__init__(f"Book with id {book_id} not found")
        else:
            super().__init__("Book not found")


class ReadingSessionNotFoundError(NotFoundError):
    """Reading session not found error."""

    def __init__(self, session_id: int | None = None, *, message: str | None = None) -> None:
        """Initialize with session ID or custom message."""
        self.session_id = session_id
        if message:
            super().__init__(message)
        elif session_id is not None:
            super().__init__(f"Reading session with id {session_id} not found")
        else:
            super().__init__("Reading session not found")


class ValidationError(CrossbillError):
    """Validation error."""


class ServiceError(CrossbillError):
    """Service layer error."""


class XPointParseError(ValidationError):
    """Invalid xpoint format."""

    def __init__(self, xpoint: str, reason: str) -> None:
        """Initialize with the invalid xpoint and reason for failure."""
        self.xpoint = xpoint
        self.reason = reason
        super().__init__(f"Invalid xpoint '{xpoint}': {reason}", status_code=400)


class XPointNavigationError(CrossbillError):
    """Could not navigate to xpoint location in EPUB."""

    def __init__(self, xpoint: str, reason: str) -> None:
        """Initialize with the xpoint and reason for navigation failure."""
        self.xpoint = xpoint
        self.reason = reason
        super().__init__(f"Cannot navigate to xpoint '{xpoint}': {reason}", status_code=400)


class InvalidEbookError(ValidationError):
    """Invalid ebook file."""

    def __init__(self, reason: str, ebook_type: str = "ebook") -> None:
        """Initialize with reason for validation failure."""
        self.reason = reason
        self.ebook_type = ebook_type
        super().__init__(f"Invalid {ebook_type}: {reason}", status_code=400)


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
