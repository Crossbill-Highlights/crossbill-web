"""
Base class for Aggregate Roots.

Aggregate Roots are the entry point to an aggregate - a cluster of domain
objects that are treated as a single unit. All external references should
go through the aggregate root, and all invariants are enforced here.

Example:
    @dataclass
    class Flashcard(AggregateRoot[FlashcardId]):
        id: FlashcardId
        user_id: UserId
        question: str
        answer: str

        def update_content(self, question: str, answer: str) -> None:
            self.question = question
            self.answer = answer
            self._record_event(FlashcardUpdated(self.id))
"""

from dataclasses import dataclass
from typing import Generic

from .entity import Entity, IdType


@dataclass
class AggregateRoot(Entity[IdType], Generic[IdType]):
    """
    Base class for Aggregate Roots in the domain model.

    Aggregate Roots are:
    - Entry point to an aggregate (cluster of related entities)
    - Responsible for maintaining invariants
    - The only entity referenced from outside the aggregate
    """
