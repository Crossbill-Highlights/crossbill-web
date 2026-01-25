from fastapi import UploadFile
from sqlalchemy.orm import Session

from src import repositories


class EbookService:
    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)

    def upload_book(self, book_id: int, file: UploadFile, user_id: int) -> tuple[str, str]:
        pass

    def get_book_path(self, book_id: int, user_id: str) -> Path:
        pass