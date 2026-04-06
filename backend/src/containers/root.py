from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.containers.identity import IdentityContainer
from src.containers.jobs import JobsContainer
from src.containers.learning import LearningContainer
from src.containers.library import LibraryContainer
from src.containers.reading import ReadingContainer
from src.containers.shared import SharedContainer


class RootContainer(containers.DeclarativeContainer):
    """Root DI container composing module sub-containers."""

    db = providers.Dependency(instance_of=AsyncSession)

    settings = providers.Object(get_settings())

    shared = providers.Container(SharedContainer, db=db, settings=settings)

    identity = providers.Container(
        IdentityContainer,
        user_repository=shared.user_repository,
        password_service=shared.password_service,
        token_service=shared.token_service,
        refresh_token_repository=shared.refresh_token_repository,
    )

    reading = providers.Container(
        ReadingContainer,
        book_repository=shared.book_repository,
        bookmark_repository=shared.bookmark_repository,
        highlight_repository=shared.highlight_repository,
        highlight_tag_repository=shared.highlight_tag_repository,
        chapter_repository=shared.chapter_repository,
        reading_session_repository=shared.reading_session_repository,
        chapter_prereading_repository=shared.chapter_prereading_repository,
        highlight_style_repository=shared.highlight_style_repository,
        file_repository=shared.file_repository,
        highlight_deduplication_service=shared.highlight_deduplication_service,
        highlight_style_resolver=shared.highlight_style_resolver,
        epub_position_index_service=shared.epub_position_index_service,
        ebook_text_extraction_service=shared.ebook_text_extraction_service,
        ai_service=shared.ai_service,
    )

    library = providers.Container(
        LibraryContainer,
        book_repository=shared.book_repository,
        chapter_repository=shared.chapter_repository,
        bookmark_repository=shared.bookmark_repository,
        highlight_repository=shared.highlight_repository,
        highlight_tag_repository=shared.highlight_tag_repository,
        highlight_style_repository=shared.highlight_style_repository,
        reading_session_repository=shared.reading_session_repository,
        tag_repository=shared.tag_repository,
        flashcard_repository=shared.flashcard_repository,
        file_repository=shared.file_repository,
        highlight_grouping_service=shared.highlight_grouping_service,
        highlight_style_resolver=shared.highlight_style_resolver,
        epub_parser_service=shared.epub_parser_service,
        epub_position_index_service=shared.epub_position_index_service,
        get_highlight_tags_for_book_use_case=reading.get_highlight_tags_for_book_use_case,
    )

    learning = providers.Container(
        LearningContainer,
        flashcard_repository=shared.flashcard_repository,
        highlight_repository=shared.highlight_repository,
        highlight_style_repository=shared.highlight_style_repository,
        highlight_style_resolver=shared.highlight_style_resolver,
        book_repository=shared.book_repository,
        chapter_repository=shared.chapter_repository,
        chapter_prereading_repository=shared.chapter_prereading_repository,
        file_repository=shared.file_repository,
        ebook_text_extraction_service=shared.ebook_text_extraction_service,
        ai_service=shared.ai_service,
        ai_chat_session_repository=shared.ai_chat_session_repository,
    )

    job_queue_service = providers.Dependency()

    jobs = providers.Container(
        JobsContainer,
        job_batch_repository=shared.job_batch_repository,
        job_queue_service=job_queue_service,
        chapter_repository=shared.chapter_repository,
        book_repository=shared.book_repository,
        chapter_prereading_repository=shared.chapter_prereading_repository,
    )
