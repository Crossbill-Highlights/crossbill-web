"""
Domain layer exceptions.

These exceptions represent domain-level errors that occur when
business rules are violated or domain invariants are broken.
They should be caught and translated to appropriate responses
by the infrastructure layer.
"""


class DomainError(Exception):
    """
    Base exception for all domain errors.

    All domain exceptions should inherit from this class
    so they can be caught and handled uniformly.
    """

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


class ValidationError(DomainError):
    """
    Raised when domain validation fails.

    Example: Invalid email format, negative quantity, etc.
    """

    def __init__(self, message: str, field: str | None = None, value: object = None) -> None:
        details: dict[str, object] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)
        self.field = field
        self.value = value


class EntityNotFoundError(DomainError):
    """
    Raised when an entity cannot be found.

    Example: Looking up a flashcard by ID that doesn't exist.
    """

    def __init__(self, entity_type: str, entity_id: object) -> None:
        message = f"{entity_type} with id {entity_id} not found"
        super().__init__(message, {"entity_type": entity_type, "entity_id": entity_id})
        self.entity_type = entity_type
        self.entity_id = entity_id


class BusinessRuleViolationError(DomainError):
    """
    Raised when a business rule is violated.

    Example: Trying to delete a flashcard that belongs to another user.
    """

    def __init__(self, rule: str, message: str | None = None) -> None:
        msg = message or f"Business rule violated: {rule}"
        super().__init__(msg, {"rule": rule})
        self.rule = rule


class InvariantViolationError(DomainError):
    """
    Raised when an aggregate invariant is violated.

    Invariants are rules that must always be true for an aggregate
    to be in a valid state.

    Example: A flashcard must always have both question and answer.
    """

    def __init__(self, aggregate: str, invariant: str) -> None:
        message = f"Invariant violation in {aggregate}: {invariant}"
        super().__init__(message, {"aggregate": aggregate, "invariant": invariant})
        self.aggregate = aggregate
        self.invariant = invariant


class AuthorizationError(DomainError):
    """
    Raised when an operation is not authorized.

    Example: User trying to access another user's flashcard.
    """

    def __init__(self, message: str = "Not authorized to perform this action") -> None:
        super().__init__(message)
