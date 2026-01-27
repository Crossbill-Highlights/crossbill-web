"""
Command and CommandHandler base classes.

Commands represent intentions to change the system state.
They are named in imperative form: CreateFlashcard, DeleteFlashcard, etc.

Example:
    @dataclass(frozen=True)
    class CreateFlashcardCommand(Command):
        user_id: int
        highlight_id: int
        question: str
        answer: str

    class CreateFlashcardHandler(CommandHandler[CreateFlashcardCommand, FlashcardId]):
        def __init__(self, repo: FlashcardRepository, uow: UnitOfWork) -> None:
            self._repo = repo
            self._uow = uow

        def handle(self, command: CreateFlashcardCommand) -> FlashcardId:
            flashcard = Flashcard.create(...)
            self._repo.save(flashcard)
            self._uow.commit()
            return flashcard.id
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

# Input type (the command)
TCommand = TypeVar("TCommand", bound="Command")
# Output type (the result of handling the command)
TResult = TypeVar("TResult")


@dataclass(frozen=True)
class Command:
    """
    Base class for Commands.

    Commands are:
    - Immutable (frozen dataclass)
    - Named in imperative form (CreateFlashcard, not FlashcardCreation)
    - Carry all data needed to execute the operation
    - Represent intentions, not facts

    Commands should be validated at the API boundary before
    being passed to handlers.
    """


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """
    Base class for Command Handlers.

    Command Handlers:
    - Execute a single command type
    - Orchestrate domain logic
    - Manage transactions (via Unit of Work)
    - Return the result of the operation

    Each command should have exactly one handler.
    """

    @abstractmethod
    def handle(self, command: TCommand) -> TResult:
        """
        Handle the command and return the result.

        This method should:
        1. Validate business rules
        2. Execute domain logic
        3. Persist changes (via repositories)
        4. Commit the transaction (via Unit of Work)
        5. Return the result

        Raises:
            DomainError: When business rules are violated
        """
        raise NotImplementedError
