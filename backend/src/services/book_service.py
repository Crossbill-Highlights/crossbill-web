"""Service layer for book-related business logic."""

import logging
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src import repositories, schemas
from src.exceptions import BookNotFoundError
from src.services.tag_service import TagService

logger = logging.getLogger(__name__)

# Directory for book cover images
COVERS_DIR = Path(__file__).parent.parent.parent / "book-covers"


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

        # Get chapters for the book
        chapters = self.chapter_repo.get_by_book_id(book_id, user_id)

        # Get highlight tags with active associations only
        highlight_tags = self.highlight_tag_repo.get_by_book_id(book_id, user_id)

        # Get highlights for each chapter and build response
        chapters_with_highlights = []
        for chapter in chapters:
            highlights = self.highlight_repo.find_by_chapter(chapter.id, user_id)

            # Convert highlights to schema
            highlight_schemas = [
                schemas.Highlight(
                    id=h.id,
                    book_id=h.book_id,
                    chapter_id=h.chapter_id,
                    text=h.text,
                    chapter=chapter.name,  # Include chapter name for display
                    chapter_number=chapter.chapter_number,  # Include chapter number
                    page=h.page,
                    note=h.note,
                    datetime=h.datetime,
                    highlight_tags=[
                        schemas.HighlightTagInBook.model_validate(tag) for tag in h.highlight_tags
                    ],
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                )
                for h in highlights
            ]

            chapter_with_highlights = schemas.ChapterWithHighlights(
                id=chapter.id,
                name=chapter.name,
                chapter_number=chapter.chapter_number,
                highlights=highlight_schemas,
                created_at=chapter.created_at,
                updated_at=chapter.updated_at,
            )
            chapters_with_highlights.append(chapter_with_highlights)

        # Get bookmarks for the book
        bookmarks = self.bookmark_repo.get_by_book_id(book_id, user_id)
        bookmark_schemas = [schemas.Bookmark.model_validate(b) for b in bookmarks]

        # Create and return the response
        return schemas.BookDetails(
            id=book.id,
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            cover=book.cover,
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
            cover: Uploaded image file (JPEG, PNG, etc.)

        Returns:
            CoverUploadResponse with success status and cover URL

        Raises:
            HTTPException: If book is not found or upload fails
        """
        # Verify book exists
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book:
            raise BookNotFoundError(book_id)

        # Ensure covers directory exists
        COVERS_DIR.mkdir(parents=True, exist_ok=True)

        # Save the uploaded file
        cover_filename = f"{book_id}.jpg"
        cover_path = COVERS_DIR / cover_filename

        # Read and write the file content
        content = cover.file.read()
        cover_path.write_bytes(content)

        logger.info(f"Successfully saved cover for book {book_id} at {cover_path}")

        # Update book's cover field in database
        cover_url = f"/media/covers/{cover_filename}"
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
        updated_book = tag_service.update_book_tags(book_id, update_data.tags, user_id)

        # Commit the changes
        self.db.commit()

        # Get highlight count for the response
        highlight_count = self.highlight_repo.count_by_book_id(book_id, user_id)

        logger.info(f"Successfully updated book {book_id}")

        # Return updated book with highlight count
        return schemas.BookWithHighlightCount(
            id=updated_book.id,
            title=updated_book.title,
            author=updated_book.author,
            isbn=updated_book.isbn,
            cover=updated_book.cover,
            highlight_count=highlight_count,
            tags=[schemas.TagInBook.model_validate(tag) for tag in updated_book.tags],
            created_at=updated_book.created_at,
            updated_at=updated_book.updated_at,
            last_viewed=updated_book.last_viewed,
        )
