"""
Base class for Entities.

Entities are objects that have a distinct identity that runs through time
and different states. Two entities are equal if they have the same identity,
regardless of their attributes.

Example:
    @dataclass
    class User(Entity[UserId]):
        id: UserId
        name: str
        email: Email

        def change_email(self, new_email: Email) -> None:
            self.email = new_email
"""

from abc import ABC
from dataclasses import dataclass
from typing import Generic, Self, TypeVar
from uuid import UUID

from .value_object import ValueObject


@dataclass(frozen=True)
class EntityId(ValueObject):
    """
    Base class for strongly-typed entity identifiers.

    Entity IDs are value objects that wrap an integer or UUID.
    They provide type safety to prevent mixing up IDs of different entities.

    Example:
        @dataclass(frozen=True)
        class UserId(EntityId):
            pass

        user_id = UserId(42)
        book_id = BookId(42)
        # These are different types, preventing accidental mixing
    """

    value: int | UUID

    def __post_init__(self) -> None:
        if isinstance(self.value, int) and self.value <= 0:
            raise ValueError(f"{self.__class__.__name__} must be positive")

    def __int__(self) -> int:
        if isinstance(self.value, int):
            return self.value
        raise TypeError(f"Cannot convert UUID-based {self.__class__.__name__} to int")

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def generate(cls) -> Self:
        """Set placeholder id. Usually these are set by the database"""
        return cls(0)

    def to_primitive(self) -> int | str:
        """Convert to primitive for serialization."""
        if isinstance(self.value, int):
            return self.value
        return str(self.value)


IdType = TypeVar("IdType", bound=EntityId)


class Entity(ABC, Generic[IdType]):
    """
    Base class for Entities in the domain model.

    Entities are:
    - Defined by identity (not attributes)
    - Mutable (state can change over time)
    - Have lifecycle (created, modified, deleted)

    Subclasses must have an 'id' attribute of type IdType.
    """

    id: IdType

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"
