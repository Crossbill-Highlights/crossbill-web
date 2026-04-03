"""Library domain exceptions."""

from src.domain.common.exceptions import ValidationError


class XPointParseError(ValidationError):
    """Invalid xpoint format."""

    def __init__(self, xpoint: str, reason: str) -> None:
        super().__init__(
            f"Invalid xpoint '{xpoint}': {reason}",
            field="xpoint",
            value=xpoint,
        )
        self.xpoint = xpoint
        self.reason = reason


class XPointNavigationError(ValidationError):
    """Could not navigate to xpoint location in EPUB."""

    def __init__(self, xpoint: str, reason: str) -> None:
        super().__init__(
            f"Cannot navigate to xpoint '{xpoint}': {reason}",
            field="xpoint",
            value=xpoint,
        )
        self.xpoint = xpoint
        self.reason = reason


class InvalidEbookError(ValidationError):
    """Invalid ebook file."""

    def __init__(self, reason: str, ebook_type: str = "ebook") -> None:
        super().__init__(
            f"Invalid {ebook_type}: {reason}",
            field="ebook",
        )
        self.reason = reason
        self.ebook_type = ebook_type
