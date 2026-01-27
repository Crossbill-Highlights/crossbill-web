"""
Result type for use case outcomes.

The Result type provides a way to handle success and failure cases
explicitly, without relying on exceptions for control flow.

Example:
    def create_flashcard(command: CreateFlashcardCommand) -> Result[FlashcardId, str]:
        if not command.question:
            return Failure("Question cannot be empty")
        flashcard = Flashcard.create(...)
        return Success(flashcard.id)

    # Usage
    result = create_flashcard(command)
    if result.is_success:
        print(f"Created: {result.unwrap()}")
    else:
        print(f"Error: {result.unwrap_error()}")
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")  # Success value type
E = TypeVar("E")  # Error type
U = TypeVar("U")  # Mapped value type


@dataclass(frozen=True)
class Success(Generic[T]):
    """Represents a successful result containing a value."""

    value: T

    @property
    def is_success(self) -> bool:
        """Always True for Success."""
        return True

    @property
    def is_failure(self) -> bool:
        """Always False for Success."""
        return False

    def unwrap(self) -> T:
        """Get the success value."""
        return self.value

    def unwrap_error(self) -> None:
        """Raises ValueError - Success has no error."""
        raise ValueError("Cannot get error from Success result")

    def value_or(self, default: T) -> T:
        """Get the value (default is ignored for Success)."""
        return self.value

    def map(self, fn: Callable[[T], U]) -> "Success[U]":
        """Apply a function to the success value."""
        return Success(fn(self.value))

    def flat_map(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Apply a function that returns a Result to the success value."""
        return fn(self.value)

    def map_error(self, fn: Callable[[E], U]) -> "Success[T]":
        """No-op for Success - returns self."""
        return self

    def __repr__(self) -> str:
        return f"Success({self.value!r})"


@dataclass(frozen=True)
class Failure(Generic[E]):
    """Represents a failed result containing an error."""

    error: E

    @property
    def is_success(self) -> bool:
        """Always False for Failure."""
        return False

    @property
    def is_failure(self) -> bool:
        """Always True for Failure."""
        return True

    def unwrap(self) -> None:
        """Raises ValueError - Failure has no value."""
        raise ValueError("Cannot get value from Failure result")

    def unwrap_error(self) -> E:
        """Get the error."""
        return self.error

    def value_or(self, default: T) -> T:
        """Return the default value for Failure."""
        return default

    def map(self, fn: Callable[[T], U]) -> "Failure[E]":
        """No-op for Failure - returns self."""
        return self

    def flat_map(self, fn: Callable[[T], "Result[U, E]"]) -> "Failure[E]":
        """No-op for Failure - returns self."""
        return self

    def map_error(self, fn: Callable[[E], U]) -> "Failure[U]":
        """Apply a function to the error value."""
        return Failure(fn(self.error))

    def __repr__(self) -> str:
        return f"Failure({self.error!r})"


# Type alias for Result - a union of Success and Failure
Result = Success[T] | Failure[E]
