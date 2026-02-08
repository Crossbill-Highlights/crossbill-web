from pathlib import Path
from typing import Protocol


class EbookTextExtractionServiceProtocol(Protocol):
    def extract_text(self, epub_path: Path, start_xpoint: str, end_xpoint: str) -> str: ...

    def extract_chapter_text(
        self,
        epub_path: Path,
        start_xpoint: str,
        end_xpoint: str | None,
    ) -> str: ...
