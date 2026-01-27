"""
Domain common module.

Contains base classes for domain modeling:
- ValueObject: Immutable objects defined by their attributes
- Entity: Objects with identity and lifecycle
- AggregateRoot: Consistency boundaries with domain events
- DomainEvent: Notifications of significant domain occurrences
"""

from .aggregate_root import AggregateRoot
from .domain_event import DomainEvent
from .entity import Entity, EntityId
from .exceptions import (
    BusinessRuleViolationError,
    DomainError,
    EntityNotFoundError,
    InvariantViolationError,
    ValidationError,
)
from .value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "BusinessRuleViolationError",
    "DomainError",
    "DomainEvent",
    "Entity",
    "EntityId",
    "EntityNotFoundError",
    "InvariantViolationError",
    "ValidationError",
    "ValueObject",
]
