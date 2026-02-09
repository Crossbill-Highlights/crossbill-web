"""
Use case for removing a tag from a highlight.
"""

import structlog

from src.application.reading.protocols.highlight_repository import (
    HighlightRepositoryProtocol,
)
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import HighlightId, HighlightTagId, UserId
from src.domain.reading.entities.highlight import Highlight
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class RemoveTagFromHighlightUseCase:
    """Use case for removing a tag from a highlight."""

    def __init__(
        self,
        highlight_repository: HighlightRepositoryProtocol,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.highlight_repository = highlight_repository
        self.tag_repository = tag_repository

    def remove_tag(self, highlight_id: int, tag_id: int, user_id: int) -> Highlight:
        """
        Remove a tag from a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag to remove
            user_id: ID of the user

        Returns:
            Updated highlight entity

        Raises:
            ValueError: If highlight not found
        """
        highlight_id_vo = HighlightId(highlight_id)
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        # Load highlight
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        # Remove association via repository
        removed = self.tag_repository.remove_tag_from_highlight(
            highlight_id_vo, tag_id_vo, user_id_vo
        )
        if removed:
            logger.info("removed_tag_from_highlight", highlight_id=highlight_id, tag_id=tag_id)

        return highlight
