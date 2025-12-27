"""Service layer for book-related business logic."""

import logging
from collections import defaultdict
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError
from src.services.tag_service import TagService

logger = logging.getLogger(__name__)

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent.parent / "book-covers"

# Maximum cover image size (5MB)
MAX_COVER_SIZE = 5 * 1024 * 1024

# Magic bytes for image file type validation
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"RIFF": "webp",  # WebP starts with RIFF, followed by size, then WEBP
}

# WebP header requires at least 12 bytes for validation
WEBP_MIN_HEADER_SIZE = 12


def _validate_image_type(content: bytes) -> str | None:
    """
    Validate image type by checking magic bytes.

    Args:
        content: The file content as bytes

    Returns:
        Image type (jpeg, png, webp) or None if not recognized
    """
    # Check JPEG
    if content.startswith(b"\xff\xd8\xff"):
        return "jpeg"

    # Check PNG
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    # Check WebP (RIFF header followed by WEBP)
    if (
        content.startswith(b"RIFF")
        and len(content) > WEBP_MIN_HEADER_SIZE
        and content[8:12] == b"WEBP"
    ):
        return "webp"

    return None


class BookService:
    """Service for handling book-related operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)
        self.highlight_repo = repositories.HighlightRepository(db)
        self.highlight_tag_repo = repositories.HighlightTagRepository(db)
        self.bookmark_repo = repositories.BookmarkRepository(db)
        self.flashcard_repo = repositories.FlashcardRepository(db)

    def get_book_details(self, book_id: int, user_id: int) -> schemas.BookDetails:
        """
        Get detailed information about a book including its chapters and highlights.

        Also updates the book's last_viewed timestamp.

        Args:
            book_id: ID of the book to retrieve

        Returns:
            BookDetails with chapters and their highlights

        Raises:
            HTTPException: If book is not found
        """
        # Get the book and update last_viewed timestamp
        book = self.book_repo.update_last_viewed(book_id, user_id)
        self.db.commit()

        if not book:
            raise BookNotFoundError(book_id)

        chapters = self.chapter_repo.get_by_book_id(book_id, user_id)
        highlight_tags = self.highlight_tag_repo.get_by_book_id(book_id, user_id)
        all_highlights = self.highlight_repo.find_by_book_with_relationships(book_id, user_id)

        # Group highlights by chapter_id
        highlights_by_chapter: dict[int | None, list[schemas.Highlight]] = defaultdict(list)
        chapter_lookup = {chapter.id: chapter for chapter in chapters}

        for h in all_highlights:
            chapter = chapter_lookup.get(h.chapter_id) if h.chapter_id is not None else None
            highlight_schema = schemas.Highlight(
                id=h.id,
                book_id=h.book_id,
                chapter_id=h.chapter_id,
                text=h.text,
                chapter=chapter.name if chapter else None,
                chapter_number=chapter.chapter_number if chapter else None,
                page=h.page,
                note=h.note,
                datetime=h.datetime,
                flashcards=[schemas.Flashcard.model_validate(fc) for fc in h.flashcards],
                highlight_tags=[
                    schemas.HighlightTagInBook.model_validate(ht) for ht in h.highlight_tags
                ],
                created_at=h.created_at,
                updated_at=h.updated_at,
            )
            highlights_by_chapter[h.chapter_id].append(highlight_schema)

        chapters_with_highlights = []
        for chapter in chapters:
            chapter_with_highlights = schemas.ChapterWithHighlights(
                id=chapter.id,
                name=chapter.name,
                chapter_number=chapter.chapter_number,
                highlights=highlights_by_chapter[chapter.id],
                created_at=chapter.created_at,
                updated_at=chapter.updated_at,
            )
            chapters_with_highlights.append(chapter_with_highlights)

        bookmarks = self.bookmark_repo.get_by_book_id(book_id, user_id)
        bookmark_schemas = [schemas.Bookmark.model_validate(b) for b in bookmarks]

        return schemas.BookDetails(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            cover=book.cover,
            description=book.description,
            language=book.language,
            page_count=book.page_count,
            tags=[schemas.TagInBook.model_validate(tag) for tag in book.tags],
            highlight_tags=[
                schemas.HighlightTagInBook.model_validate(tag) for tag in highlight_tags
            ],
            highlight_tag_groups=[
                schemas.HighlightTagGroupInBook.model_validate(group)
                for group in book.highlight_tag_groups
            ],
            bookmarks=bookmark_schemas,
            chapters=chapters_with_highlights,
            created_at=book.created_at,
            updated_at=book.updated_at,
            last_viewed=book.last_viewed,
        )

    def delete_book(self, book_id: int, user_id: int) -> bool:
        """
        Delete a book and all its contents (hard delete).

        This will permanently delete the book, all its chapters, and all its highlights.

        Args:
            book_id: ID of the book to delete

        Returns:
            bool: True if book was deleted

        Raises:
            HTTPException: If book is not found
        """
        deleted = self.book_repo.delete(book_id, user_id)

        if not deleted:
            raise BookNotFoundError(book_id)

        # Commit the deletion
        self.db.commit()

        logger.info(f"Successfully deleted book {book_id}")
        return True

    def delete_highlights(
        self, book_id: int, highlight_ids: list[int], user_id: int
    ) -> schemas.HighlightDeleteResponse:
        """
        Soft delete highlights from a book.

        This performs a soft delete by marking the highlights as deleted.
        When syncing highlights, deleted highlights will not be recreated,
        ensuring that user deletions persist across syncs.

        Args:
            book_id: ID of the book
            highlight_ids: List of highlight IDs to delete

        Returns:
            HighlightDeleteResponse with deletion status and count

        Raises:
            HTTPException: If book is not found
        """
        # Verify book exists
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book:
            raise BookNotFoundError(book_id)

        # Soft delete highlights
        deleted_count = self.highlight_repo.soft_delete_by_ids(book_id, user_id, highlight_ids)

        # Commit the changes
        self.db.commit()

        return schemas.HighlightDeleteResponse(
            success=True,
            message=f"Successfully deleted {deleted_count} highlight(s)",
            deleted_count=deleted_count,
        )

    def upload_cover(
        self, book_id: int, cover: UploadFile, user_id: int
    ) -> schemas.CoverUploadResponse:
        """
        Upload a book cover image.

        This method accepts an uploaded image file and saves it as the book's cover.
        The cover is saved to the covers directory with the filename {book_id}.jpg
        and the book's cover field is updated in the database.

        Args:
            book_id: ID of the book
            cover: Uploaded image file (JPEG, PNG, or WebP)
            user_id: ID of the user uploading the cover

        Returns:
            CoverUploadResponse with success status and cover URL

        Raises:
            HTTPException: If book is not found, file validation fails, or upload fails
        """
        # Verify book exists
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book:
            raise BookNotFoundError(book_id)

        # Check content-type header
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if cover.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, detail="Only JPEG, PNG, and WebP images are allowed"
            )

        # Read with size limit
        content = cover.file.read(MAX_COVER_SIZE + 1)
        if len(content) > MAX_COVER_SIZE:
            raise HTTPException(status_code=400, detail="File too large (max 5MB)")

        # Verify magic bytes
        file_type = _validate_image_type(content)
        if file_type not in {"jpeg", "png", "webp"}:
            raise HTTPException(status_code=400, detail="Invalid image file")

        COVERS_DIR.mkdir(parents=True, exist_ok=True)

        cover_filename = f"{book_id}.jpg"
        cover_path = COVERS_DIR / cover_filename
        cover_path.write_bytes(content)

        logger.info(f"Successfully saved cover for book {book_id} at {cover_path}")

        # Update book's cover field in database
        cover_url = f"/api/v1/books/{book_id}/cover"
        book.cover = cover_url
        self.db.commit()

        return schemas.CoverUploadResponse(
            success=True,
            message="Cover uploaded successfully",
            cover_url=cover_url,
        )

    def update_book(
        self, book_id: int, update_data: schemas.BookUpdateRequest, user_id: int
    ) -> schemas.BookWithHighlightCount:
        """
        Update book information.

        Currently supports updating tags only. The tags will be replaced with the provided list.

        Args:
            book_id: ID of the book to update
            update_data: Book update request containing tags

        Returns:
            Updated book with highlight count and tags

        Raises:
            HTTPException: If book is not found
        """
        # Verify book exists
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book:
            raise BookNotFoundError(book_id)

        # Update tags using TagService
        tag_service = TagService(self.db)
        updated_book = tag_service.update_book_tags(book, update_data.tags, user_id)

        # Commit the changes
        self.db.commit()

        # Get highlight and flashcard counts for the response
        highlight_count = self.highlight_repo.count_by_book_id(book_id, user_id)
        flashcard_count = self.flashcard_repo.count_by_book_id(book_id, user_id)

        logger.info(f"Successfully updated book {book_id}")

        # Return updated book with highlight and flashcard counts
        return schemas.BookWithHighlightCount(
            id=updated_book.id,
            title=updated_book.title,
            author=updated_book.author,
            isbn=updated_book.isbn,
            cover=updated_book.cover,
            description=updated_book.description,
            language=updated_book.language,
            page_count=updated_book.page_count,
            highlight_count=highlight_count,
            flashcard_count=flashcard_count,
            tags=[schemas.TagInBook.model_validate(tag) for tag in updated_book.tags],
            created_at=updated_book.created_at,
            updated_at=updated_book.updated_at,
            last_viewed=updated_book.last_viewed,
        )

    def get_cover_path(self, book_id: int, user_id: int) -> Path:
        """
        Get the file path for a book cover with ownership verification.

        Args:
            book_id: ID of the book
            user_id: ID of the user requesting the cover

        Returns:
            Path to the cover file

        Raises:
            BookNotFoundError: If book is not found or user doesn't own it
            HTTPException: If cover file doesn't exist
        """
        # Verify book exists and user owns it
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book:
            raise BookNotFoundError(book_id)

        cover_filename = f"{book_id}.jpg"
        cover_path = COVERS_DIR / cover_filename

        if not cover_path.is_file():
            raise HTTPException(status_code=404, detail="Cover not found")

        return cover_path
