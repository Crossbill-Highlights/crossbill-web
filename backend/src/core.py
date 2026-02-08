from dependency_injector import containers, providers
from sqlalchemy.orm import Session

from src.application.identity.use_cases.authentication.authenticate_user_use_case import (
    AuthenticateUserUseCase,
)
from src.application.identity.use_cases.authentication.get_user_by_id_use_case import (
    GetUserByIdUseCase,
)
from src.application.identity.use_cases.authentication.refresh_access_token_use_case import (
    RefreshAccessTokenUseCase,
)
from src.application.identity.use_cases.register_user_use_case import RegisterUserUseCase
from src.application.identity.use_cases.update_user_use_case import UpdateUserUseCase
from src.application.learning.use_cases.flashcards.create_flashcard_for_book_use_case import (
    CreateFlashcardForBookUseCase,
)
from src.application.learning.use_cases.flashcards.create_flashcard_for_highlight_use_case import (
    CreateFlashcardForHighlightUseCase,
)
from src.application.learning.use_cases.flashcards.delete_flashcard_use_case import (
    DeleteFlashcardUseCase,
)
from src.application.learning.use_cases.flashcards.get_flashcard_suggestions_use_case import (
    GetFlashcardSuggestionsUseCase,
)
from src.application.learning.use_cases.flashcards.get_flashcards_by_book_use_case import (
    GetFlashcardsByBookUseCase,
)
from src.application.learning.use_cases.flashcards.update_flashcard_use_case import (
    UpdateFlashcardUseCase,
)
from src.application.library.use_cases.book_files.book_cover_use_case import BookCoverUseCase
from src.application.library.use_cases.book_files.ebook_deletion_use_case import (
    EbookDeletionUseCase,
)
from src.application.library.use_cases.book_files.ebook_upload_use_case import EbookUploadUseCase
from src.application.library.use_cases.book_management.create_book_use_case import (
    CreateBookUseCase,
)
from src.application.library.use_cases.book_management.delete_book_use_case import (
    DeleteBookUseCase,
)
from src.application.library.use_cases.book_management.get_book_details_use_case import (
    GetBookDetailsUseCase,
)
from src.application.library.use_cases.book_management.update_book_use_case import (
    UpdateBookUseCase,
)
from src.application.library.use_cases.book_queries.get_books_with_counts_use_case import (
    GetBooksWithCountsUseCase,
)
from src.application.library.use_cases.book_queries.get_ereader_metadata_use_case import (
    GetEreaderMetadataUseCase,
)
from src.application.library.use_cases.book_queries.get_recently_viewed_books_use_case import (
    GetRecentlyViewedBooksUseCase,
)
from src.application.library.use_cases.book_tag_associations.add_tags_to_book_use_case import (
    AddTagsToBookUseCase,
)
from src.application.reading.use_cases.chapter_content_use_case import (
    ChapterContentUseCase,
)
from src.application.library.use_cases.book_tag_associations.get_book_tags_use_case import (
    GetBookTagsUseCase,
)
from src.application.library.use_cases.book_tag_associations.replace_book_tags_use_case import (
    ReplaceBookTagsUseCase,
)
from src.application.reading.use_cases.bookmarks.create_bookmark_use_case import (
    CreateBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.delete_bookmark_use_case import (
    DeleteBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.get_bookmarks_use_case import (
    GetBookmarksUseCase,
)
from src.application.reading.use_cases.chapter_prereading.generate_chapter_prereading_use_case import (
    GenerateChapterPrereadingUseCase,
)
from src.application.reading.use_cases.chapter_prereading.get_book_prereading_use_case import (
    GetBookPrereadingUseCase,
)
from src.application.reading.use_cases.chapter_prereading.get_chapter_prereading_use_case import (
    GetChapterPrereadingUseCase,
)
from src.application.reading.use_cases.highlight_tag_associations.add_tag_to_highlight_by_id_use_case import (
    AddTagToHighlightByIdUseCase,
)
from src.application.reading.use_cases.highlight_tag_associations.add_tag_to_highlight_by_name_use_case import (
    AddTagToHighlightByNameUseCase,
)
from src.application.reading.use_cases.highlight_tag_associations.remove_tag_from_highlight_use_case import (
    RemoveTagFromHighlightUseCase,
)
from src.application.reading.use_cases.highlight_tag_groups.create_highlight_tag_group_use_case import (
    CreateHighlightTagGroupUseCase,
)
from src.application.reading.use_cases.highlight_tag_groups.delete_highlight_tag_group_use_case import (
    DeleteHighlightTagGroupUseCase,
)
from src.application.reading.use_cases.highlight_tag_groups.update_highlight_tag_group_use_case import (
    UpdateHighlightTagGroupUseCase,
)
from src.application.reading.use_cases.highlight_tag_groups.update_tag_group_association_use_case import (
    UpdateTagGroupAssociationUseCase,
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
from src.application.reading.use_cases.highlights.highlight_delete_use_case import (
    HighlightDeleteUseCase,
)
from src.application.reading.use_cases.highlights.highlight_search_use_case import (
    HighlightSearchUseCase,
)
from src.application.reading.use_cases.highlights.highlight_upload_use_case import (
    HighlightUploadUseCase,
)
from src.application.reading.use_cases.highlights.update_highlight_note_use_case import (
    HighlightUpdateNoteUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_ai_summary_use_case import (
    ReadingSessionAISummaryUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_query_use_case import (
    ReadingSessionQueryUseCase,
)
from src.application.reading.use_cases.reading_sessions.reading_session_upload_use_case import (
    ReadingSessionUploadUseCase,
)
from src.domain.reading.services.deduplication_service import HighlightDeduplicationService
from src.domain.reading.services.highlight_grouping_service import HighlightGroupingService
from src.infrastructure.ai.ai_service import AIService
from src.infrastructure.identity.repositories.user_repository import UserRepository
from src.infrastructure.identity.services.password_service_adapter import PasswordServiceAdapter
from src.infrastructure.identity.services.token_service_adapter import TokenServiceAdapter
from src.infrastructure.learning.repositories.flashcard_repository import FlashcardRepository
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.chapter_repository import ChapterRepository
from src.infrastructure.library.repositories.file_repository import FileRepository
from src.infrastructure.library.repositories.tag_repository import TagRepository
from src.infrastructure.library.services.epub_text_extraction_service import (
    EpubTextExtractionService,
)
from src.infrastructure.library.services.epub_toc_parser_service import EpubTocParserService
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

    # Infrastructure services (no db dependency)
    ebook_text_extraction_service = providers.Factory(EpubTextExtractionService)
    epub_toc_parser_service = providers.Factory(EpubTocParserService)
    ai_service = providers.Factory(AIService)

    # Identity repositories and services
    user_repository = providers.Factory(UserRepository, db=db)
    password_service = providers.Singleton(PasswordServiceAdapter)
    token_service = providers.Singleton(TokenServiceAdapter)

    # Domain services (pure domain logic, no db)
    highlight_deduplication_service = providers.Factory(HighlightDeduplicationService)
    highlight_grouping_service = providers.Factory(HighlightGroupingService)

    # Reading module, application use cases
    create_bookmark_use_case = providers.Factory(
        CreateBookmarkUseCase,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
    )
    delete_bookmark_use_case = providers.Factory(
        DeleteBookmarkUseCase,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
    )
    get_bookmarks_use_case = providers.Factory(
        GetBookmarksUseCase,
        book_repository=book_repository,
        bookmark_repository=bookmark_repository,
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
    create_highlight_tag_use_case = providers.Factory(
        CreateHighlightTagUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )

    delete_highlight_tag_use_case = providers.Factory(
        DeleteHighlightTagUseCase,
        tag_repository=highlight_tag_repository,
    )

    update_highlight_tag_name_use_case = providers.Factory(
        UpdateHighlightTagNameUseCase,
        tag_repository=highlight_tag_repository,
    )

    get_highlight_tags_for_book_use_case = providers.Factory(
        GetHighlightTagsForBookUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )
    create_highlight_tag_group_use_case = providers.Factory(
        CreateHighlightTagGroupUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )
    update_highlight_tag_group_use_case = providers.Factory(
        UpdateHighlightTagGroupUseCase,
        tag_repository=highlight_tag_repository,
        book_repository=book_repository,
    )
    delete_highlight_tag_group_use_case = providers.Factory(
        DeleteHighlightTagGroupUseCase,
        tag_repository=highlight_tag_repository,
    )
    update_tag_group_association_use_case = providers.Factory(
        UpdateTagGroupAssociationUseCase,
        tag_repository=highlight_tag_repository,
    )
    add_tag_to_highlight_by_id_use_case = providers.Factory(
        AddTagToHighlightByIdUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
    )
    add_tag_to_highlight_by_name_use_case = providers.Factory(
        AddTagToHighlightByNameUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
    )
    remove_tag_from_highlight_use_case = providers.Factory(
        RemoveTagFromHighlightUseCase,
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
        file_repo=file_repository,
    )
    reading_session_ai_summary_use_case = providers.Factory(
        ReadingSessionAISummaryUseCase,
        session_repository=reading_session_repository,
        text_extraction_service=ebook_text_extraction_service,
        book_repo=book_repository,
        file_repo=file_repository,
        ai_summary_service=ai_service,
    )
    get_chapter_prereading_use_case = providers.Factory(
        GetChapterPrereadingUseCase,
        prereading_repo=chapter_prereading_repository,
        chapter_repo=chapter_repository,
    )
    get_book_prereading_use_case = providers.Factory(
        GetBookPrereadingUseCase,
        prereading_repo=chapter_prereading_repository,
        chapter_repo=chapter_repository,
    )
    generate_chapter_prereading_use_case = providers.Factory(
        GenerateChapterPrereadingUseCase,
        prereading_repo=chapter_prereading_repository,
        chapter_repo=chapter_repository,
        text_extraction_service=ebook_text_extraction_service,
        book_repo=book_repository,
        file_repo=file_repository,
        ai_prereading_service=ai_service,
    )
    chapter_content_use_case = providers.Factory(
        ChapterContentUseCase,
        chapter_repo=chapter_repository,
        book_repo=book_repository,
        file_repo=file_repository,
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

    add_tags_to_book_use_case = providers.Factory(
        AddTagsToBookUseCase,
        tag_repository=tag_repository,
        book_repository=book_repository,
    )
    replace_book_tags_use_case = providers.Factory(
        ReplaceBookTagsUseCase,
        tag_repository=tag_repository,
        book_repository=book_repository,
    )
    get_book_tags_use_case = providers.Factory(
        GetBookTagsUseCase,
        tag_repository=tag_repository,
        book_repository=book_repository,
    )

    ebook_upload_use_case = providers.Factory(
        EbookUploadUseCase,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        file_repository=file_repository,
        epub_toc_parser=epub_toc_parser_service,
    )

    create_book_use_case = providers.Factory(
        CreateBookUseCase,
        book_repository=book_repository,
        add_tags_to_book_use_case=add_tags_to_book_use_case,
    )

    get_book_details_use_case = providers.Factory(
        GetBookDetailsUseCase,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        bookmark_repository=bookmark_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
        get_book_tags_use_case=get_book_tags_use_case,
        highlight_tag_use_case=get_highlight_tags_for_book_use_case,
        highlight_grouping_service=highlight_grouping_service,
    )

    update_book_use_case = providers.Factory(
        UpdateBookUseCase,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
        flashcard_repository=flashcard_repository,
        replace_book_tags_use_case=replace_book_tags_use_case,
    )

    delete_book_use_case = providers.Factory(
        DeleteBookUseCase,
        book_repository=book_repository,
        ebook_deletion_use_case=ebook_deletion_use_case,
    )

    get_ereader_metadata_use_case = providers.Factory(
        GetEreaderMetadataUseCase,
        book_repository=book_repository,
    )

    # Learning module use cases
    create_flashcard_for_highlight_use_case = providers.Factory(
        CreateFlashcardForHighlightUseCase,
        flashcard_repository=flashcard_repository,
        highlight_repository=highlight_repository,
    )

    create_flashcard_for_book_use_case = providers.Factory(
        CreateFlashcardForBookUseCase,
        flashcard_repository=flashcard_repository,
        book_repository=book_repository,
    )

    get_flashcards_by_book_use_case = providers.Factory(
        GetFlashcardsByBookUseCase,
        flashcard_repository=flashcard_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )

    update_flashcard_use_case = providers.Factory(
        UpdateFlashcardUseCase,
        flashcard_repository=flashcard_repository,
    )

    delete_flashcard_use_case = providers.Factory(
        DeleteFlashcardUseCase,
        flashcard_repository=flashcard_repository,
    )

    get_flashcard_suggestions_use_case = providers.Factory(
        GetFlashcardSuggestionsUseCase,
        highlight_repository=highlight_repository,
        ai_flashcard_service=ai_service,
    )

    # Identity use cases
    update_user_use_case = providers.Factory(
        UpdateUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
    )

    authenticate_user_use_case = providers.Factory(
        AuthenticateUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )
    refresh_access_token_use_case = providers.Factory(
        RefreshAccessTokenUseCase,
        user_repository=user_repository,
        token_service=token_service,
    )
    get_user_by_id_use_case = providers.Factory(
        GetUserByIdUseCase,
        user_repository=user_repository,
    )

    register_user_use_case = providers.Factory(
        RegisterUserUseCase,
        user_repository=user_repository,
        password_service=password_service,
        token_service=token_service,
    )


# Initialize container
container = Container()
