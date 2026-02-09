"""Application services and use cases for reading domain.

This module re-exports use cases and their DTOs for convenience.
All services have been migrated to use cases following DDD hexagonal architecture.
"""

# Re-export use cases (these are in use_cases/ subdirectories now)
from src.application.reading.use_cases.bookmarks.create_bookmark_use_case import (
    CreateBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.delete_bookmark_use_case import (
    DeleteBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.get_bookmarks_use_case import (
    GetBookmarksUseCase,
)
from src.application.reading.use_cases.highlights.highlight_delete_use_case import (
    HighlightDeleteUseCase,
)
from src.application.reading.use_cases.highlights.highlight_search_use_case import (
    HighlightSearchUseCase,
)
from src.application.reading.use_cases.highlights.highlight_tag_association_use_case import (
    HighlightTagAssociationUseCase,
)
from src.application.reading.use_cases.highlights.highlight_tag_group_use_case import (
    HighlightTagGroupUseCase,
)
from src.application.reading.use_cases.highlight_tags.create_highlight_tag_use_case import (
    CreateHighlightTagUseCase,
)
from src.application.reading.use_cases.highlight_tags.delete_highlight_tag_use_case import (
    DeleteHighlightTagUseCase,
)
from src.application.reading.use_cases.highlight_tags.get_highlight_tags_for_book_use_case import (
    GetHighlightTagsForBookUseCase,
)
from src.application.reading.use_cases.highlight_tags.update_highlight_tag_name_use_case import (
    UpdateHighlightTagNameUseCase,
)
from src.application.reading.use_cases.highlights.highlight_upload_use_case import (
    HighlightUploadData,
    HighlightUploadUseCase,
)
from src.application.reading.use_cases.highlights.update_highlight_note_use_case import (
    HighlightUpdateNoteUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_ai_summary_use_case import (
    ReadingSessionAISummaryUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_query_use_case import (
    ReadingSessionQueryResult,
    ReadingSessionQueryUseCase,
    ReadingSessionWithHighlights,
)
from src.application.reading.use_cases.reading_sessions.reading_session_upload_use_case import (
    ReadingSessionUploadData,
    ReadingSessionUploadResult,
    ReadingSessionUploadUseCase,
)

__all__ = [
    # Use cases
    "CreateBookmarkUseCase",
    "DeleteBookmarkUseCase",
    "GetBookmarksUseCase",
    "HighlightDeleteUseCase",
    "HighlightSearchUseCase",
    "HighlightTagAssociationUseCase",
    "HighlightTagGroupUseCase",
    "CreateHighlightTagUseCase",
    "DeleteHighlightTagUseCase",
    "GetHighlightTagsForBookUseCase",
    "UpdateHighlightTagNameUseCase",
    "HighlightUpdateNoteUseCase",
    # DTOs
    "HighlightUploadData",
    "HighlightUploadUseCase",
    "ReadingSessionAISummaryUseCase",
    "ReadingSessionQueryResult",
    "ReadingSessionQueryUseCase",
    "ReadingSessionUploadData",
    "ReadingSessionUploadResult",
    "ReadingSessionUploadUseCase",
    "ReadingSessionWithHighlights",
]
