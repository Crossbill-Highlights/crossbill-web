from dependency_injector import containers, providers

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
from src.application.library.use_cases.book_tag_associations.get_book_tags_use_case import (
    GetBookTagsUseCase,
)
from src.application.library.use_cases.book_tag_associations.replace_book_tags_use_case import (
    ReplaceBookTagsUseCase,
)


class LibraryContainer(containers.DeclarativeContainer):
    """Library module use cases."""

    # Dependencies from shared
    book_repository = providers.Dependency()
    chapter_repository = providers.Dependency()
    bookmark_repository = providers.Dependency()
    highlight_repository = providers.Dependency()
    highlight_tag_repository = providers.Dependency()
    highlight_style_repository = providers.Dependency()
    reading_session_repository = providers.Dependency()
    tag_repository = providers.Dependency()
    flashcard_repository = providers.Dependency()
    file_repository = providers.Dependency()
    highlight_grouping_service = providers.Dependency()
    highlight_style_resolver = providers.Dependency()
    epub_parser_service = providers.Dependency()
    epub_position_index_service = providers.Dependency()
    cover_image_service = providers.Dependency()

    # Cross-module dependency from reading
    get_highlight_tags_for_book_use_case = providers.Dependency()

    # Book tag associations (needed by create/update book)
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

    # Book files
    ebook_upload_use_case = providers.Factory(
        EbookUploadUseCase,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        file_repository=file_repository,
        epub_parser=epub_parser_service,
        cover_image_service=cover_image_service,
        position_index_service=epub_position_index_service,
        highlight_repository=highlight_repository,
        session_repository=reading_session_repository,
    )
    ebook_deletion_use_case = providers.Factory(
        EbookDeletionUseCase,
        file_repository=file_repository,
    )

    # Book management
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
        flashcard_repository=flashcard_repository,
        get_book_tags_use_case=get_book_tags_use_case,
        highlight_tag_use_case=get_highlight_tags_for_book_use_case,
        highlight_grouping_service=highlight_grouping_service,
        reading_session_repository=reading_session_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
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

    # Book queries
    get_books_with_counts_use_case = providers.Factory(
        GetBooksWithCountsUseCase,
        book_repository=book_repository,
    )
    get_recently_viewed_books_use_case = providers.Factory(
        GetRecentlyViewedBooksUseCase,
        book_repository=book_repository,
    )
    get_ereader_metadata_use_case = providers.Factory(
        GetEreaderMetadataUseCase,
        book_repository=book_repository,
    )
