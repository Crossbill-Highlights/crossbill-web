"""Use case for getting global highlight labels."""

from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.domain.common.value_objects import UserId
from src.domain.reading.entities.highlight_style import HighlightStyle


class GetGlobalHighlightLabelsUseCase:
    """Get all global default highlight labels."""

    def __init__(
        self,
        highlight_style_repository: HighlightStyleRepositoryProtocol,
    ) -> None:
        self.highlight_style_repository = highlight_style_repository

    def execute(self, user_id: int) -> list[HighlightStyle]:
        """Returns list of global highlight styles."""
        return self.highlight_style_repository.find_global(UserId(user_id))
