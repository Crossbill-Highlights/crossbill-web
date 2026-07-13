from dependency_injector import containers, providers

from src.application.notes.use_cases.create_note_use_case import CreateNoteUseCase
from src.application.notes.use_cases.get_note_use_case import GetNoteUseCase


class NotesContainer(containers.DeclarativeContainer):
    """Notes module use cases."""

    # Dependencies from shared
    note_repository = providers.Dependency()
    book_repository = providers.Dependency()
    chapter_repository = providers.Dependency()
    highlight_repository = providers.Dependency()
    highlight_tag_repository = providers.Dependency()

    create_note_use_case = providers.Factory(
        CreateNoteUseCase,
        note_repository=note_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
    get_note_use_case = providers.Factory(
        GetNoteUseCase,
        note_repository=note_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        highlight_tag_repository=highlight_tag_repository,
    )
