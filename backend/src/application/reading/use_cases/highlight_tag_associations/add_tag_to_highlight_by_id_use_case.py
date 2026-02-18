"""
Use case for adding an existing tag to a highlight by ID.
"""

import structlog

from src.application.reading.protocols.highlight_repository import (
    HighlightRepositoryProtocol,
)
from src.application.reading.protocols.highlight_style_repository import (
    HighlightStyleRepositoryProtocol,
)
from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import HighlightId, HighlightTagId, UserId
from src.domain.learning.entities.flashcard import Flashcard
from src.domain.reading.entities.highlight import Highlight
from src.domain.reading.entities.highlight_tag import HighlightTag
from src.domain.reading.services.highlight_style_resolver import (
    HighlightStyleResolver,
    ResolvedLabel,
)
from src.exceptions import NotFoundError

logger = structlog.get_logger(__name__)


class AddTagToHighlightByIdUseCase:
    """Use case for adding an existing tag to a highlight by ID."""

    def __init__(
        self,
        highlight_repository: HighlightRepositoryProtocol,
        tag_repository: HighlightTagRepositoryProtocol,
        highlight_style_repository: HighlightStyleRepositoryProtocol | None = None,
        highlight_style_resolver: HighlightStyleResolver | None = None,
    ) -> None:
        self.highlight_repository = highlight_repository
        self.tag_repository = tag_repository
        self.highlight_style_repository = highlight_style_repository
        self.highlight_style_resolver = highlight_style_resolver

    def add_tag(
        self, highlight_id: int, tag_id: int, user_id: int
    ) -> tuple[Highlight, list[Flashcard], list[HighlightTag], dict[int, ResolvedLabel]]:
        """
        Add an existing tag to a highlight.

        Args:
            highlight_id: ID of the highlight
            tag_id: ID of the tag to add
            user_id: ID of the user

        Returns:
            Tuple of (Highlight, Flashcards, Tags, Labels)

        Raises:
            ValueError: If highlight or tag not found
        """
        highlight_id_vo = HighlightId(highlight_id)
        tag_id_vo = HighlightTagId(tag_id)
        user_id_vo = UserId(user_id)

        # Load entities
        highlight = self.highlight_repository.find_by_id(highlight_id_vo, user_id_vo)
        if not highlight:
            raise NotFoundError(f"Highlight with id {highlight_id} not found")

        tag = self.tag_repository.find_by_id(tag_id_vo, user_id_vo)
        if not tag:
            raise NotFoundError(f"Tag with id {tag_id} not found")

        # Use domain entity to validate
        highlight.add_tag(tag)

        # Persist association via repository
        added = self.tag_repository.add_tag_to_highlight(highlight_id_vo, tag_id_vo, user_id_vo)
        if added:
            logger.info("added_tag_to_highlight", highlight_id=highlight_id, tag_id=tag_id)

        # Reload with relations
        result = self.highlight_repository.find_by_id_with_relations(highlight_id_vo, user_id_vo)
        if not result:
            raise NotFoundError(f"Highlight with id {highlight_id} not found after reload")
        highlight, flashcards, tags = result

        # Resolve labels
        labels: dict[int, ResolvedLabel] = {}
        if self.highlight_style_repository and self.highlight_style_resolver:
            all_styles = self.highlight_style_repository.find_for_resolution(
                user_id_vo, highlight.book_id
            )
            for style in all_styles:
                if style.is_combination_level() and not style.is_global():
                    resolved = self.highlight_style_resolver.resolve(style, all_styles)
                    labels[style.id.value] = resolved

        return highlight, flashcards, tags, labels
