"""
Unit of Work interface.

The Unit of Work pattern maintains a list of objects affected by a business
transaction and coordinates the writing out of changes and the resolution
of concurrency problems.

Example:
    class CreateFlashcardHandler(CommandHandler[CreateFlashcardCommand, FlashcardId]):
        def __init__(self, repo: FlashcardRepository, uow: UnitOfWork) -> None:
            self._repo = repo
            self._uow = uow

        def handle(self, command: CreateFlashcardCommand) -> FlashcardId:
            with self._uow:
                flashcard = Flashcard.create(...)
                self._repo.save(flashcard)
                self._uow.commit()
                return flashcard.id
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from types import TracebackType
from typing import Self

from src.domain.common import DomainEvent


class UnitOfWork(ABC):
    """
    Unit of Work interface (Port).

    The Unit of Work:
    - Manages database transactions
    - Ensures atomicity of operations
    - Collects and dispatches domain events
    - Can be used as a context manager

    Infrastructure layer provides concrete implementations
    (e.g., SQLAlchemyUnitOfWork).
    """

    @abstractmethod
    def commit(self) -> None:
        """
        Commit the current transaction.

        This persists all changes made within the unit of work.
        After commit, domain events should be dispatched.
        """
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """
        Rollback the current transaction.

        This discards all changes made within the unit of work.
        """
        raise NotImplementedError

    def __enter__(self) -> Self:
        """Enter the unit of work context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit the unit of work context.

        If an exception occurred, rollback. Otherwise, do nothing
        (commit must be called explicitly).
        """
        if exc_type is not None:
            self.rollback()

    def collect_events(self) -> list[DomainEvent]:
        """
        Collect domain events from aggregates.

        Override in implementations to collect events from
        tracked aggregates before dispatching.
        """
        return []

    def register_event_handler(self, handler: Callable[[DomainEvent], None]) -> None:
        """
        Register a handler to be called for domain events.

        Events are dispatched after successful commit.
        Override in implementations that support event dispatching.
        """
        # Default no-op implementation - override in subclasses if needed
        _ = handler  # Mark as used
