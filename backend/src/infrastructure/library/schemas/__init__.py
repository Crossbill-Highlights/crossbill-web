"""Library context schemas."""

from src.infrastructure.library.schemas.book_schemas import (
    Book,
    BookBase,
    BookCreate,
    BooksListResponse,
    BookWithHighlightCount,
    CoverUploadResponse,
    EpubUploadResponse,
    EreaderBookMetadata,
    RecentlyViewedBooksResponse,
    TagInBook,
)
from src.infrastructure.library.schemas.chapter_schemas import Chapter, ChapterBase
from src.infrastructure.library.schemas.tag_schemas import BookUpdateRequest, Tag

__all__ = [
    "Book",
    "BookBase",
    "BookCreate",
    "BookUpdateRequest",
    "BookWithHighlightCount",
    "BooksListResponse",
    "Chapter",
    "ChapterBase",
    "CoverUploadResponse",
    "EpubUploadResponse",
    "EreaderBookMetadata",
    "RecentlyViewedBooksResponse",
    "Tag",
    "TagInBook",
]
