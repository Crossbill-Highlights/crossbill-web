"""
Use case for deleting a highlight tag group.
"""

import structlog

from src.application.reading.protocols.highlight_tag_repository import (
    HighlightTagRepositoryProtocol,
)
from src.domain.common.value_objects.ids import HighlightTagGroupId

logger = structlog.get_logger(__name__)


class DeleteHighlightTagGroupUseCase:
    """Use case for deleting a highlight tag group."""

    def __init__(
        self,
        tag_repository: HighlightTagRepositoryProtocol,
    ) -> None:
        self.tag_repository = tag_repository

    def delete_group(self, group_id: int, user_id: int) -> bool:
        """
        Delete a tag group (nullifies tag associations).

        Args:
            group_id: ID of the group to delete
            user_id: ID of the user

        Returns:
            True if deleted, False if not found
        """
        group_id_vo = HighlightTagGroupId(group_id)

        success = self.tag_repository.delete_group(group_id_vo)
        if success:
            logger.info("deleted_tag_group", group_id=group_id)

        return success
