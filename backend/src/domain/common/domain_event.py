"""
Base class for Domain Events.

Domain Events represent something significant that happened in the domain.
They are immutable records of past occurrences that other parts of the
system can react to.

Example:
    @dataclass(frozen=True)
    class FlashcardCreated(DomainEvent):
        flashcard_id: FlashcardId
        user_id: UserId
        highlight_id: HighlightId
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for Domain Events.

    Domain Events are:
    - Immutable (frozen dataclass)
    - Named in past tense (FlashcardCreated, not CreateFlashcard)
    - Self-contained (carry all data needed to understand what happened)
    - Timestamped (when the event occurred)

    Subclasses should be decorated with @dataclass(frozen=True)
    and define their specific attributes.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        """Return the event type name for serialization."""
        return self.__class__.__name__

    def to_dict(self) -> dict[str, object]:
        """Convert event to dictionary for serialization."""
        result: dict[str, object] = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, UUID):
                result[key] = str(value)
            elif hasattr(value, "to_primitive"):
                result[key] = value.to_primitive()
            else:
                result[key] = value
        result["event_type"] = self.event_type
        return result
