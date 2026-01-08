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


class ValidationError(CrossbillError):
    """Validation error."""


class ServiceError(CrossbillError):
    """Service layer error."""


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
