
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src import repositories
from src.exceptions import ValidationError
from src.services.ebook.epub_service import EpubService
from src.services.ebook.pdf_service import PdfService


class EbookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.epub_service = EpubService(db)
        self.pdf_service = PdfService(db)
        self.book_repo = repositories.BookRepository(db)

    def upload_ebook(self, client_book_id: str, file: UploadFile, user_id: int) -> tuple[str, str]:
        # Detect file type from content-type header
        if file.content_type == "application/epub+zip":
            return self.epub_service.upload_epub_by_client_book_id(client_book_id, file, user_id)
        if file.content_type == "application/pdf":
            return self.pdf_service.upload_pdf_by_client_book_id(client_book_id, file, user_id)
        raise ValidationError(
            f"Unsupported file type: {file.content_type}. Only EPUB and PDF files are supported."
        )

    def delete_ebook(self, book_id: int) -> bool:
        # Try deleting both EPUB and PDF files (one of them should exist)
        # Book is already deleted from database at this point, so we can't check file_type
        epub_deleted = self.epub_service.delete_epub(book_id)
        pdf_deleted = self.pdf_service.delete_pdf(book_id)
        return epub_deleted or pdf_deleted

    def extract_text_between(
        self, book_id: int, user_id: int, start: str | int, end: str | int
    ) -> str:
        # Validate that start and end are the same type
        if type(start) is type(end):
            raise ValidationError(
                "start and end must be the same type (both int for pages or both str for xpoints)"
            )

        # Route based on parameter types
        if isinstance(start, int) and isinstance(end, int):
            # PDF: page numbers
            return self.pdf_service.extract_text_between_pages(book_id, user_id, start, end)
        if isinstance(start, str) and isinstance(end, str):
            # EPUB: xpoints
            return self.epub_service.extract_text_between_xpoints(book_id, user_id, start, end)
        raise ValidationError("start and end must both be int (pages) or str (xpoints)")
