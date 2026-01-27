"""
Query and QueryHandler base classes.

Queries represent requests for information without side effects.
They are named descriptively: GetFlashcard, ListFlashcards, etc.

Example:
    @dataclass(frozen=True)
    class GetFlashcardQuery(Query):
        flashcard_id: int
        user_id: int

    class GetFlashcardHandler(QueryHandler[GetFlashcardQuery, FlashcardDTO | None]):
        def __init__(self, repo: FlashcardRepository) -> None:
            self._repo = repo

        def handle(self, query: GetFlashcardQuery) -> FlashcardDTO | None:
            flashcard = self._repo.find_by_id(query.flashcard_id, query.user_id)
            return FlashcardDTO.from_entity(flashcard) if flashcard else None
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

# Input type (the query)
TQuery = TypeVar("TQuery", bound="Query")
# Output type (the result of the query)
TResult = TypeVar("TResult")


@dataclass(frozen=True)
class Query:
    """
    Base class for Queries.

    Queries are:
    - Immutable (frozen dataclass)
    - Named descriptively (GetFlashcard, ListFlashcards)
    - Carry filter/pagination parameters
    - Have no side effects (read-only)

    Queries should not modify state - they only retrieve data.
    """


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """
    Base class for Query Handlers.

    Query Handlers:
    - Execute a single query type
    - Return DTOs or primitive data (not domain entities)
    - Have no side effects
    - May use read-optimized data access

    Each query should have exactly one handler.
    Query handlers don't need Unit of Work since they don't modify state.
    """

    @abstractmethod
    def handle(self, query: TQuery) -> TResult:
        """
        Handle the query and return the result.

        This method should:
        1. Fetch data from repositories
        2. Transform to DTOs if needed
        3. Return the result

        Query handlers should NOT:
        - Modify any state
        - Trigger side effects
        - Return domain entities directly
        """
        raise NotImplementedError
