"""Pydantic schemas for API request/response validation."""

from crossbill.schemas.book_schemas import (
    Book,
    BookBase,
    BookCreate,
    BooksListResponse,
    BookWithHighlightCount,
    CoverUploadResponse,
)
from crossbill.schemas.chapter_schemas import Chapter, ChapterBase
from crossbill.schemas.highlight_schemas import (
    BookDetails,
    ChapterWithHighlights,
    Highlight,
    HighlightBase,
    HighlightCreate,
    HighlightDeleteRequest,
    HighlightDeleteResponse,
    HighlightSearchResponse,
    HighlightSearchResult,
    HighlightUploadRequest,
    HighlightUploadResponse,
)
from crossbill.schemas.tag_schemas import BookUpdateRequest, Tag

__all__ = [
    "Book",
    "BookBase",
    "BookCreate",
    "BookDetails",
    "BookUpdateRequest",
    "BookWithHighlightCount",
    "BooksListResponse",
    "Chapter",
    "ChapterBase",
    "ChapterWithHighlights",
    "CoverUploadResponse",
    "Highlight",
    "HighlightBase",
    "HighlightCreate",
    "HighlightDeleteRequest",
    "HighlightDeleteResponse",
    "HighlightSearchResponse",
    "HighlightSearchResult",
    "HighlightUploadRequest",
    "HighlightUploadResponse",
    "Tag",
]
