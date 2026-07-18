from dependency_injector import containers, providers

from src.application.notes.use_cases.create_note_use_case import CreateNoteUseCase
from src.application.notes.use_cases.delete_note_use_case import DeleteNoteUseCase
from src.application.notes.use_cases.get_note_use_case import GetNoteUseCase
from src.application.notes.use_cases.get_notes_by_book_use_case import GetNotesByBookUseCase
from src.application.notes.use_cases.update_note_use_case import UpdateNoteUseCase


class NotesContainer(containers.DeclarativeContainer):
    """Notes module use cases."""

    # Dependencies from shared
    note_repository = providers.Dependency()
    book_repository = providers.Dependency()
    chapter_repository = providers.Dependency()
    highlight_repository = providers.Dependency()
    tag_repository = providers.Dependency()
    flashcard_repository = providers.Dependency()

    create_note_use_case = providers.Factory(
        CreateNoteUseCase,
        note_repository=note_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        tag_repository=tag_repository,
    )
    get_note_use_case = providers.Factory(
        GetNoteUseCase,
        note_repository=note_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        tag_repository=tag_repository,
        flashcard_repository=flashcard_repository,
    )
    get_notes_by_book_use_case = providers.Factory(
        GetNotesByBookUseCase,
        note_repository=note_repository,
        book_repository=book_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        tag_repository=tag_repository,
    )
    update_note_use_case = providers.Factory(
        UpdateNoteUseCase,
        note_repository=note_repository,
        chapter_repository=chapter_repository,
        highlight_repository=highlight_repository,
        tag_repository=tag_repository,
    )
    delete_note_use_case = providers.Factory(
        DeleteNoteUseCase,
        note_repository=note_repository,
    )
