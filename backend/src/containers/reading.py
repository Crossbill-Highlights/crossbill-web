from dependency_injector import containers, providers

from src.application.reading.use_cases.bookmarks.create_bookmark_use_case import (
    CreateBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.delete_bookmark_use_case import (
    DeleteBookmarkUseCase,
)
from src.application.reading.use_cases.bookmarks.get_bookmarks_use_case import (
    GetBookmarksUseCase,
)
from src.application.reading.use_cases.chapter_content_use_case import (
    ChapterContentUseCase,
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
from src.application.reading.use_cases.highlight_labels.create_global_highlight_label_use_case import (
    CreateGlobalHighlightLabelUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_book_highlight_labels_use_case import (
    GetBookHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.get_global_highlight_labels_use_case import (
    GetGlobalHighlightLabelsUseCase,
)
from src.application.reading.use_cases.highlight_labels.update_highlight_label_use_case import (
    UpdateHighlightLabelUseCase,
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


class ReadingContainer(containers.DeclarativeContainer):
    """Reading module use cases."""

    # Dependencies from shared
    book_repository = providers.Dependency()
    bookmark_repository = providers.Dependency()
    highlight_repository = providers.Dependency()
    highlight_tag_repository = providers.Dependency()
    chapter_repository = providers.Dependency()
    reading_session_repository = providers.Dependency()
    chapter_prereading_repository = providers.Dependency()
    highlight_style_repository = providers.Dependency()
    file_repository = providers.Dependency()
    highlight_deduplication_service = providers.Dependency()
    highlight_style_resolver = providers.Dependency()
    epub_position_index_service = providers.Dependency()
    ebook_text_extraction_service = providers.Dependency()
    ai_service = providers.Dependency()

    # Bookmarks
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

    # Highlights
    highlight_search_use_case = providers.Factory(
        HighlightSearchUseCase,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    highlight_delete_use_case = providers.Factory(
        HighlightDeleteUseCase,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
    )
    highlight_update_note_use_case = providers.Factory(
        HighlightUpdateNoteUseCase,
        highlight_repository=highlight_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    highlight_upload_use_case = providers.Factory(
        HighlightUploadUseCase,
        highlight_repository=highlight_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        deduplication_service=highlight_deduplication_service,
        position_index_service=epub_position_index_service,
        file_repository=file_repository,
        highlight_style_repository=highlight_style_repository,
    )

    # Highlight tags
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

    # Highlight tag groups
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

    # Highlight tag associations
    add_tag_to_highlight_by_id_use_case = providers.Factory(
        AddTagToHighlightByIdUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    add_tag_to_highlight_by_name_use_case = providers.Factory(
        AddTagToHighlightByNameUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    remove_tag_from_highlight_use_case = providers.Factory(
        RemoveTagFromHighlightUseCase,
        highlight_repository=highlight_repository,
        tag_repository=highlight_tag_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )

    # Highlight labels
    get_book_highlight_labels_use_case = providers.Factory(
        GetBookHighlightLabelsUseCase,
        highlight_style_repository=highlight_style_repository,
        book_repository=book_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    update_highlight_label_use_case = providers.Factory(
        UpdateHighlightLabelUseCase,
        highlight_style_repository=highlight_style_repository,
    )
    get_global_highlight_labels_use_case = providers.Factory(
        GetGlobalHighlightLabelsUseCase,
        highlight_style_repository=highlight_style_repository,
    )
    create_global_highlight_label_use_case = providers.Factory(
        CreateGlobalHighlightLabelUseCase,
        highlight_style_repository=highlight_style_repository,
    )

    # Reading sessions
    reading_session_upload_use_case = providers.Factory(
        ReadingSessionUploadUseCase,
        session_repository=reading_session_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
        position_index_service=epub_position_index_service,
        file_repository=file_repository,
    )
    reading_session_query_use_case = providers.Factory(
        ReadingSessionQueryUseCase,
        session_repository=reading_session_repository,
        book_repository=book_repository,
        highlight_repository=highlight_repository,
        text_extraction_service=ebook_text_extraction_service,
        file_repo=file_repository,
        highlight_style_repository=highlight_style_repository,
        highlight_style_resolver=highlight_style_resolver,
    )
    reading_session_ai_summary_use_case = providers.Factory(
        ReadingSessionAISummaryUseCase,
        session_repository=reading_session_repository,
        text_extraction_service=ebook_text_extraction_service,
        book_repo=book_repository,
        file_repo=file_repository,
        ai_summary_service=ai_service,
    )

    # Chapter prereading
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

    # Chapter content
    chapter_content_use_case = providers.Factory(
        ChapterContentUseCase,
        chapter_repo=chapter_repository,
        book_repo=book_repository,
        file_repo=file_repository,
        text_extraction_service=ebook_text_extraction_service,
    )
