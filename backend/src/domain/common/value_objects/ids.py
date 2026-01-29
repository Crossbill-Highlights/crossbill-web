from dataclasses import dataclass

from ..entity import EntityId


@dataclass(frozen=True)
class BookId(EntityId):
    """Strongly-typed book identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("BookId must be non-negative")


@dataclass(frozen=True)
class UserId(EntityId):
    """Strongly-typed user identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("UserId must be non-negative")


@dataclass(frozen=True)
class HighlightId(EntityId):
    """Strongly-typed highlight identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("HighlightId must be non-negative")


@dataclass(frozen=True)
class ChapterId(EntityId):
    """Strongly-typed chapter identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("ChapterId must be non-negative")


@dataclass(frozen=True)
class ReadingSessionId(EntityId):
    """Strongly-typed reading session identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("ReadingSessionId must be non-negative")


@dataclass(frozen=True)
class HighlightTagId(EntityId):
    """Strongly-typed highlight tag identifier."""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("HighlightTagId must be non-negative")
