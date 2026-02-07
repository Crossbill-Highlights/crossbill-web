from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from src.application.identity.use_cases.authentication_use_case import AuthenticationUseCase
from src.application.identity.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.identity.use_cases.update_user_use_case import UpdateUserUseCase
from src.application.learning.use_cases.flashcard_ai_use_case import FlashcardAIUseCase
from src.application.learning.use_cases.flashcard_use_case import FlashcardUseCase
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
from src.application.reading.use_cases.chapter_prereading_use_case import (
    ChapterPrereadingUseCase,
)
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
from src.infrastructure.identity.repositories.user_repository import UserRepository
from src.infrastructure.identity.services.password_service_adapter import PasswordServiceAdapter
from src.infrastructure.identity.services.token_service_adapter import TokenServiceAdapter
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
from src.infrastructure.reading.repositories.chapter_prereading_repository import (
    ChapterPrereadingRepository,
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
    chapter_prereading_repository = providers.Factory(ChapterPrereadingRepository, db=db)
    file_repository = providers.Factory(FileRepository)
    ebook_text_extraction_service = providers.Factory(EbookTextExtractionService, db=db)

    # Identity repositories and services
    user_repository = providers.Factory(UserRepository, db=db)
    password_service = providers.Singleton(PasswordServiceAdapter)
    token_service = providers.Singleton(TokenServiceAdapter)

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
    chapter_prereading_use_case = providers.Factory(
        ChapterPrereadingUseCase,
        prereading_repo=chapter_prereading_repository,
        chapter_repo=chapter_repository,
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
        chapter_repository=chapter_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
        flashcard_repository=flashcard_repository,
        book_tag_association_use_case=book_tag_association_use_case,
        ebook_deletion_use_case=ebook_deletion_use_case,
        highlight_tag_use_case=highlight_tag_use_case,
        highlight_grouping_service=highlight_grouping_service,
    )

    # Learning module use cases
    flashcard_use_case = providers.Factory(
        FlashcardUseCase,
        flashcard_repository=flashcard_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )

    flashcard_ai_use_case = providers.Factory(
        FlashcardAIUseCase,
        highlight_repository=highlight_repository,
    )

    # Identity use cases
    update_user_use_case = providers.Factory(
        UpdateUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
    )

    authentication_use_case = providers.Factory(
        AuthenticationUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )

    register_user_use_case = providers.Factory(
        RegisterUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )


# Initialize container
container = Container()
