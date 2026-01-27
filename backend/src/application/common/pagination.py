"""
Pagination types for queries.

Provides standardized pagination for list queries.

Example:
    @dataclass(frozen=True)
    class ListFlashcardsQuery(Query):
        user_id: int
        book_id: int | None
        pagination: Pagination

    class ListFlashcardsHandler(QueryHandler[ListFlashcardsQuery, PaginatedResult[FlashcardDTO]]):
        def handle(self, query: ListFlashcardsQuery) -> PaginatedResult[FlashcardDTO]:
            items, total = self._repo.find_all(query.user_id, query.pagination)
            return PaginatedResult(
                items=[FlashcardDTO.from_entity(f) for f in items],
                total=total,
                pagination=query.pagination,
            )
"""

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

# Maximum allowed page size
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Pagination:
    """
    Pagination parameters for list queries.

    Attributes:
        page: Current page number (1-indexed)
        page_size: Number of items per page
    """

    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValueError("Page must be at least 1")
        if self.page_size < 1:
            raise ValueError("Page size must be at least 1")
        if self.page_size > MAX_PAGE_SIZE:
            raise ValueError(f"Page size cannot exceed {MAX_PAGE_SIZE}")

    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the limit for database queries."""
        return self.page_size


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """
    Paginated result containing items and metadata.

    Attributes:
        items: List of items for the current page
        total: Total number of items across all pages
        pagination: The pagination parameters used
    """

    items: list[T]
    total: int
    pagination: Pagination

    @property
    def page(self) -> int:
        """Current page number."""
        return self.pagination.page

    @property
    def page_size(self) -> int:
        """Number of items per page."""
        return self.pagination.page_size

    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        if self.total == 0:
            return 0
        return (self.total + self.pagination.page_size - 1) // self.pagination.page_size

    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.pagination.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.pagination.page > 1
