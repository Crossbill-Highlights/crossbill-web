"""Application-layer DTOs for library module."""

from dataclasses import dataclass, field


@dataclass
class CreateBookInput:
    """Input data for creating a book."""

    title: str
    client_book_id: str
    author: str | None = None
    isbn: str | None = None
    description: str | None = None
    language: str | None = None
    page_count: int | None = None
    keywords: list[str] | None = None


@dataclass
class UpdateBookInput:
    """Input data for updating a book."""

    tags: list[str] = field(default_factory=list)
