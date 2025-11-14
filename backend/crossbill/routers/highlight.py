"""API routes for individual highlight management."""

import logging

from fastapi import APIRouter, HTTPException, status

from crossbill import schemas
from crossbill.database import DatabaseSession
from crossbill.exceptions import CrossbillError
from crossbill.services import HighlightTagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/highlight", tags=["highlight"])


@router.get(
    "/{highlight_id}/tags",
    response_model=schemas.HighlightTagsResponse,
    status_code=status.HTTP_200_OK,
)
def get_highlight_tags(
    highlight_id: int,
    db: DatabaseSession,
) -> schemas.HighlightTagsResponse:
    """
    Get all tags associated with a highlight.

    Args:
        highlight_id: ID of the highlight
        db: Database session

    Returns:
        HighlightTagsResponse with list of tags

    Raises:
        HTTPException: If highlight is not found or fetching fails
    """
    try:
        service = HighlightTagService(db)
        tags = service.get_tags_for_highlight(highlight_id)
        return schemas.HighlightTagsResponse(tags=tags)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except CrossbillError:
        # Re-raise custom exceptions - handled by exception handlers
        raise
    except Exception as e:
        logger.error(f"Failed to fetch tags for highlight {highlight_id}: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch highlight tags: {e!s}",
        ) from e
