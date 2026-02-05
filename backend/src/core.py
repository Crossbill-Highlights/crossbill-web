from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from src.application.library.services.ebook_text_extraction_service import (
    EbookTextExtractionService,
)
from src.application.library.use_cases.book_cover_use_case import BookCoverUseCase
from src.application.library.use_cases.book_management_use_case import BookManagementUseCase
from src.application.library.use_cases.book_tag_association_use_case import (
    BookTagAssociationUseCase,
)
from src.application.library.use_cases.ebook_deletion_use_case import EbookDeletionUseCase
from src.application.library.use_cases.ebook_upload_use_case import EbookUploadUseCase
from src.application.library.use_cases.get_books_with_counts_use_case import (
    GetBooksWithCountsUseCase,
)
from src.application.library.use_cases.get_recently_viewed_books_use_case import (
    GetRecentlyViewedBooksUseCase,
)
from src.application.reading.use_cases.bookmark_use_case import BookmarkUseCase
from src.application.reading.use_cases.highlight_delete_use_case import HighlightDeleteUseCase
from src.application.reading.use_cases.highlight_search_use_case import HighlightSearchUseCase
from src.application.reading.use_cases.highlight_tag_association_use_case import (
    HighlightTagAssociationUseCase,
)
from src.application.reading.use_cases.highlight_tag_group_use_case import (
    HighlightTagGroupUseCase,
)
from src.application.reading.use_cases.highlight_tag_use_case import HighlightTagUseCase
from src.application.reading.use_cases.highlight_upload_use_case import HighlightUploadUseCase
from src.application.reading.use_cases.reading_session_ai_summary_use_case import (
    ReadingSessionAISummaryUseCase,
)
from src.application.reading.use_cases.reading_session_query_use_case import (
    ReadingSessionQueryUseCase,
)
from src.application.reading.use_cases.reading_session_upload_use_case import (
    ReadingSessionUploadUseCase,
)
from src.application.reading.use_cases.update_highlight_note_use_case import (
    HighlightUpdateNoteUseCase,
)
from src.domain.reading.services.deduplication_service import HighlightDeduplicationService
from src.domain.reading.services.highlight_grouping_service import HighlightGroupingService
from src.infrastructure.learning.repositories.flashcard_repository import FlashcardRepository
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.repositories.tag_repository import TagRepository
from src.infrastructure.reading.repositories import (
    BookmarkRepository,
    HighlightRepository,
    HighlightTagRepository,
)
from src.infrastructure.reading.repositories.reading_session_repository import (
    ReadingSessionRepository,
)


class Container(containers.DeclarativeContainer):
    """Dependency injection container."""

    # Declare db as a dependency that will be provided at runtime
    db = providers.Dependency(instance_of=Session)

    # Repositories
    book_repository = providers.Factory(BookRepository, db=db)
    bookmark_repository = providers.Factory(BookmarkRepository, db=db)
    highlight_repository = providers.Factory(HighlightRepository, db=db)
    highlight_tag_repository = providers.Factory(HighlightTagRepository, db=db)
    chapter_repository = providers.Factory(ChapterRepository, db=db)
    reading_session_repository = providers.Factory(ReadingSessionRepository, db=db)
    tag_repository = providers.Factory(TagRepository, db=db)
    flashcard_repository = providers.Factory(FlashcardRepository, db=db)
    file_repository = providers.Factory(FileRepository)
    ebook_text_extraction_service = providers.Factory(EbookTextExtractionService, db=db)

    # Domain services (pure domain logic, no db)
    highlight_deduplication_service = providers.Factory(HighlightDeduplicationService)
    highlight_grouping_service = providers.Factory(HighlightGroupingService)

    # Reading module, application use cases
    bookmark_use_case = providers.Factory(
        BookmarkUseCase,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
    )

    highlight_search_use_case = providers.Factory(
        HighlightSearchUseCase,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )
    highlight_delete_use_case = providers.Factory(
        HighlightDeleteUseCase,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )
    highlight_update_note_use_case = providers.Factory(
        HighlightUpdateNoteUseCase,
        highlight_repository=highlight_repository,
    )
    highlight_tag_use_case = providers.Factory(
        HighlightTagUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )
    highlight_tag_group_use_case = providers.Factory(
        HighlightTagGroupUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )
    highlight_tag_association_use_case = providers.Factory(
        HighlightTagAssociationUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
    )
    highlight_upload_use_case = providers.Factory(
        HighlightUploadUseCase,
        highlight_repository=highlight_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        deduplication_service=highlight_deduplication_service,
    )
    reading_session_upload_use_case = providers.Factory(
        ReadingSessionUploadUseCase,
        session_repository=reading_session_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )
    reading_session_query_use_case = providers.Factory(
        ReadingSessionQueryUseCase,
        session_repository=reading_session_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
        text_extraction_service=ebook_text_extraction_service,
    )
    reading_session_ai_summary_use_case = providers.Factory(
        ReadingSessionAISummaryUseCase,
        session_repository=reading_session_repository,
        text_extraction_service=ebook_text_extraction_service,
    )

    # Library module, application use cases
    ebook_deletion_use_case = providers.Factory(
        EbookDeletionUseCase,
        file_repository=file_repository,
    )

    get_books_with_counts_use_case = providers.Factory(
        GetBooksWithCountsUseCase,
        book_repository=book_repository,
    )

    get_recently_viewed_books_use_case = providers.Factory(
        GetRecentlyViewedBooksUseCase,
        book_repository=book_repository,
    )

    book_cover_use_case = providers.Factory(
        BookCoverUseCase,
        book_repository=book_repository,
        file_repository=file_repository,
    )

    book_tag_association_use_case = providers.Factory(
        BookTagAssociationUseCase,
        tag_repository=tag_repository,
        book_repository=book_repository,
    )

    ebook_upload_use_case = providers.Factory(
        EbookUploadUseCase,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        file_repository=file_repository,
    )

    book_management_use_case = providers.Factory(
        BookManagementUseCase,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
        flashcard_repository=flashcard_repository,
        book_tag_association_use_case=book_tag_association_use_case,
        ebook_deletion_use_case=ebook_deletion_use_case,
        highlight_tag_use_case=highlight_tag_use_case,
        highlight_grouping_service=highlight_grouping_service,
    )


# Initialize container
container = Container()
