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

from dataclasses import dataclass, field
from typing import Generic

from .domain_event import DomainEvent
from .entity import Entity, IdType


@dataclass
class AggregateRoot(Entity[IdType], Generic[IdType]):
    """
    Base class for Aggregate Roots in the domain model.

    Aggregate Roots are:
    - Entry point to an aggregate (cluster of related entities)
    - Responsible for maintaining invariants
    - The only entity referenced from outside the aggregate
    - Can record domain events for later dispatch

    Domain events are collected and can be dispatched after
    the aggregate is persisted (through the Unit of Work).
    """

    _events: list[DomainEvent] = field(
        default_factory=list, repr=False, compare=False, kw_only=True
    )

    def _record_event(self, event: DomainEvent) -> None:
        """
        Record a domain event to be dispatched later.

        Events are typically dispatched by the Unit of Work
        after the aggregate is successfully persisted.
        """
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """
        Collect and clear all recorded domain events.

        This is called by the infrastructure layer (e.g., Unit of Work)
        after persisting the aggregate.
        """
        events = self._events.copy()
        self._events.clear()
        return events

    @property
    def pending_events(self) -> list[DomainEvent]:
        """Return pending events without clearing them."""
        return self._events.copy()
