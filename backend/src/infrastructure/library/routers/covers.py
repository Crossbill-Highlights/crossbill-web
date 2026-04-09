"""Public endpoint for serving book cover images."""

import re

from fastapi import APIRouter, HTTPException
from starlette import status
from starlette.responses import Response

from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.core import container

router = APIRouter(prefix="/covers", tags=["covers"])

# UUID filename pattern: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.jpg
_UUID_FILENAME_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$"
)


@router.get("/{filename}", status_code=status.HTTP_200_OK, response_class=Response)
async def get_cover(filename: str) -> Response:
    """
    Get a book cover image by filename.

    This is a public endpoint - no authentication required.
    Cover filenames are UUIDs, making enumeration infeasible.
    """
    if not _UUID_FILENAME_RE.match(filename):
        raise HTTPException(status_code=404, detail="Cover not found")

    file_repository: FileRepositoryProtocol = container.shared.file_repository()
    cover_bytes = await file_repository.get_cover(filename)

    if cover_bytes is None:
        raise HTTPException(status_code=404, detail="Cover not found")

    return Response(
        content=cover_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )
