"""
Base class for Value Objects.

Value Objects are immutable objects that are defined by their attributes
rather than by identity. Two value objects are equal if all their
attributes are equal.

Example:
    @dataclass(frozen=True)
    class Email(ValueObject):
        value: str

        def __post_init__(self) -> None:
            if "@" not in self.value:
                raise ValidationError("Invalid email format")
"""


class ValueObject:
    """
    Base class for Value Objects in the domain model.

    Value Objects are:
    - Immutable (use frozen=True in dataclass)
    - Compared by value (all attributes must match)
    - Self-validating (validation in __post_init__)

    Subclasses should be decorated with @dataclass(frozen=True)
    and implement validation in __post_init__.
    """

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"

    def to_primitive(self) -> object:
        """
        Convert to primitive Python type for serialization.

        Override in subclasses if needed. Default returns
        the first attribute value for single-value VOs.
        """
        values = list(self.__dict__.values())
        if len(values) == 1:
            return values[0]
        return dict(self.__dict__)
