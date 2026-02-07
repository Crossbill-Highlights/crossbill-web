"""Use case for ebook upload operations."""

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from src.application.library.protocols.book_repository import BookRepositoryProtocol
from src.application.library.protocols.chapter_repository import ChapterRepositoryProtocol
from src.application.library.protocols.file_repository import FileRepositoryProtocol
from src.domain.common.value_objects.ids import UserId
from src.domain.reading.exceptions import BookNotFoundError
from src.exceptions import InvalidEbookError

logger = logging.getLogger(__name__)


def _sanitize_filename(text: str) -> str:
    """
    Sanitize text for use in filename.

    Removes/replaces characters that are invalid in filenames.
    Limits length to prevent overly long filenames.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text safe for filenames
    """
    # Remove invalid filename characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "", text)
    # Replace spaces and other whitespace with underscores
    sanitized = re.sub(r"\s+", "_", sanitized)
    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip("_.")
    # Limit length (leave room for book_id and extension)
    max_length = 100
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def _validate_epub(content: bytes) -> bool:
    """
    Validate epub file using ebooklib.

    This performs lightweight validation by attempting to read
    the epub structure. Full validation would be too slow for upload.

    Args:
        content: The file content as bytes

    Returns:
        True if valid epub, False otherwise
    """
    try:
        # Create a temporary file-like object from bytes
        epub_file = BytesIO(content)

        # Try to read the epub - ebooklib will raise exception if invalid
        book = epub.read_epub(epub_file)

        # Basic validation: epub should have some metadata
        if not book.get_metadata("DC", "title"):
            logger.warning("EPUB missing title metadata")
            # Allow epubs without metadata (user explicitly uploading)

        return True

    except Exception as e:
        logger.error(f"EPUB validation failed: {e!s}")
        return False


# TODO: should this and helper functions here be a domain service?
def _extract_toc_hierarchy(
    toc_items: list[Any], current_number: int = 1, parent_name: str | None = None
) -> list[tuple[str, int, str | None, str | None]]:
    """
    Extract hierarchical TOC structure into a list preserving parent relationships.

    EPUB TOC can be nested. This function preserves the hierarchy while
    assigning sequential chapter numbers for reading order.

    Args:
        toc_items: List of TOC items from ebooklib (can be Link objects or tuples)
        current_number: Starting chapter number (used for recursion)
        parent_name: Name of the parent chapter (None for root-level chapters)

    Returns:
        List of (chapter_title, chapter_number, parent_name, href) tuples in reading order.
        parent_name is None for root-level chapters. href is the TOC link target.
    """
    chapters: list[tuple[str, int, str | None, str | None]] = []

    for item in toc_items:
        # TOC items can be Link objects or tuples (Section, [children])
        if isinstance(item, tuple):
            # Nested section: (Link, [children])
            section, children = item[0], item[1] if len(item) > 1 else []

            # Add the section itself
            if hasattr(section, "title"):
                href = getattr(section, "href", None)
                chapters.append((section.title, current_number, parent_name, href))
                section_name = section.title
                current_number += 1
            else:
                section_name = parent_name

            # Recursively process children with this section as parent
            child_chapters = _extract_toc_hierarchy(children, current_number, section_name)
            chapters.extend(child_chapters)
            current_number += len(child_chapters)

        elif hasattr(item, "title"):
            # Simple Link object
            href = getattr(item, "href", None)
            chapters.append((item.title, current_number, parent_name, href))
            current_number += 1

    return chapters


class EbookUploadUseCase:
    """Use case for uploading ebook files."""

    def __init__(
        self,
        book_repository: BookRepositoryProtocol,
        chapter_repository: ChapterRepositoryProtocol,
        file_repository: FileRepositoryProtocol,
    ) -> None:
        """
        Initialize use case with dependencies.

        Args:
            book_repository: Book repository protocol implementation
            chapter_repository: Chapter repository protocol implementation
            file_repository: File repository protocol implementation
        """
        self.book_repository = book_repository
        self.chapter_repository = chapter_repository
        self.file_repository = file_repository

    def upload_ebook(
        self,
        client_book_id: str,
        content: bytes,
        content_type: str,
        user_id: int,
    ) -> tuple[str, str]:
        """
        Upload and save an ebook file (EPUB or PDF).

        Args:
            client_book_id: Client-provided book identifier
            content: File content as bytes
            content_type: MIME type of the file
            user_id: ID of the user uploading the file

        Returns:
            tuple[str, str]: (file_path_for_db, absolute_file_path)

        Raises:
            EntityNotFoundError: If book not found for the given client_book_id
            InvalidEbookError: If file validation fails
            NotImplementedError: If PDF upload is requested (not yet implemented)
        """
        # Route by content type
        if content_type in ["application/epub+zip", "application/epub"]:
            return self._upload_epub(client_book_id, content, UserId(user_id))
        if content_type == "application/pdf":
            raise NotImplementedError("PDF upload not yet implemented")
        raise InvalidEbookError(f"Unsupported content type: {content_type}", ebook_type="UNKNOWN")

    def _upload_epub(
        self,
        client_book_id: str,
        content: bytes,
        user_id: UserId,
    ) -> tuple[str, str]:
        """
        Upload and validate an EPUB file for a book.

        This method:
        1. Validates the book exists and belongs to user
        2. Validates epub structure using ebooklib
        3. Generates sanitized filename from book title and ID
        4. Saves file to epubs directory
        5. Removes old epub file if filename differs
        6. Updates book.file_path and book.file_type in database
        7. Parses TOC and saves chapters

        Args:
            client_book_id: Client-provided book identifier
            content: The epub file content as bytes
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            EntityNotFoundError: If book not found or doesn't belong to user
            InvalidEbookError: If epub structure validation fails
        """
        # Find book by client_book_id
        book = self.book_repository.find_by_client_book_id(client_book_id, user_id)
        if not book:
            raise BookNotFoundError(f"client_book_id={client_book_id}")

        if not _validate_epub(content):
            raise InvalidEbookError("EPUB structure validation failed", ebook_type="EPUB")

        # TODO: These likely belong to the repository level
        # Generate filename: sanitized_title_bookid.epub
        sanitized_title = _sanitize_filename(book.title)
        epub_filename = f"{sanitized_title}_{book.id.value}.epub"

        # Check if book already has an epub file for deletion
        old_file_path = None
        if book.file_path and book.file_type == "epub":
            old_file_path = book.file_path

        # Delete old epub file if it exists and has different name
        if old_file_path and old_file_path != epub_filename:
            self.file_repository.delete_epub(book.id)

        # Save new epub file
        epub_path = self.file_repository.save_epub(book.id, content, epub_filename)
        book.update_file(epub_filename, "epub")
        self.book_repository.save(book)

        # Parse TOC and save chapters to database
        # TODO: this parsing logic might belong to domain level
        toc_chapters = self._parse_toc_from_epub(epub_path)
        if toc_chapters:
            # TODO: maybe we could pass domain objects to the repository?
            self.chapter_repository.sync_chapters_from_toc(book.id, user_id, toc_chapters)

        return epub_filename, str(epub_path)

    @staticmethod
    def _build_href_to_spine_index(book: Any) -> dict[str, int]:  # noqa: ANN401
        """
        Build a mapping from spine item file names to 1-based spine indices.

        Args:
            book: An ebooklib EpubBook instance

        Returns:
            Dict mapping file_name (without path) → 1-based spine index
        """
        mapping: dict[str, int] = {}
        spine_items = book.spine  # list of (item_id, linear) tuples
        items_by_id = {item.id: item for item in book.get_items()}

        for idx, (item_id, _linear) in enumerate(spine_items, start=1):
            item = items_by_id.get(item_id)
            if item:
                # item.file_name is like "OEBPS/chapter1.xhtml" or "chapter1.xhtml"
                file_name = item.file_name
                # Store both full path and basename for flexible matching
                mapping[file_name] = idx
                basename = file_name.rsplit("/", 1)[-1] if "/" in file_name else file_name
                if basename not in mapping:
                    mapping[basename] = idx
        return mapping

    @staticmethod
    def _href_to_spine_index(href: str, mapping: dict[str, int]) -> int | None:
        """
        Resolve a TOC href to a spine index using the mapping.

        Args:
            href: TOC link href (e.g. "chapter1.xhtml#section1")
            mapping: Dict from _build_href_to_spine_index

        Returns:
            1-based spine index, or None if not found
        """
        # Strip fragment
        file_part = href.split("#")[0]

        # Try exact match first
        if file_part in mapping:
            return mapping[file_part]

        # Try basename match
        basename = file_part.rsplit("/", 1)[-1] if "/" in file_part else file_part
        return mapping.get(basename)

    @staticmethod
    def _resolve_href_to_xpoint(
        book: Any,  # noqa: ANN401
        href: str,
        spine_mapping: dict[str, int],
        html_cache: dict[int, etree._Element],  # pyright: ignore[reportPrivateUsage]
    ) -> str | None:
        """Resolve a TOC href to a precise XPoint string.

        When the href contains a fragment identifier (e.g., chapter.xhtml#section2),
        this resolves it to the specific element's XPath within the spine item.

        Args:
            book: An ebooklib EpubBook instance
            href: TOC link href (e.g. "chapter1.xhtml#section2")
            spine_mapping: Dict from _build_href_to_spine_index
            html_cache: Cache of parsed HTML trees by spine index (mutated)

        Returns:
            XPoint string like "/body/DocFragment[N]/body/section[2]", or None if
            the href cannot be resolved to a spine index.
        """
        # Split href into file part and fragment
        parts = href.split("#", 1)
        file_part = parts[0]
        fragment_id = parts[1] if len(parts) > 1 else None

        # Get spine index from file part
        spine_idx = EbookUploadUseCase._href_to_spine_index(file_part, spine_mapping)
        if spine_idx is None:
            # Try with full href (basename matching)
            spine_idx = EbookUploadUseCase._href_to_spine_index(href.split("#")[0], spine_mapping)
            if spine_idx is None:
                return None

        base_xpoint = f"/body/DocFragment[{spine_idx}]/body"

        if not fragment_id:
            return base_xpoint

        # Load and parse the spine item HTML (with caching)
        if spine_idx not in html_cache:
            spine_index_0 = spine_idx - 1
            if spine_index_0 < 0 or spine_index_0 >= len(book.spine):
                return base_xpoint

            item_id = book.spine[spine_index_0][0]
            items_by_id = {item.id: item for item in book.get_items()}
            item = items_by_id.get(item_id)
            if item is None:
                return base_xpoint

            content = item.get_content()
            parser = etree.HTMLParser()
            html_cache[spine_idx] = etree.fromstring(content, parser)

        tree = html_cache[spine_idx]

        # Find element with the fragment ID
        xpath_result = tree.xpath(f'//*[@id="{fragment_id}"]')
        if not isinstance(xpath_result, list) or not xpath_result:
            logger.warning(
                f"Fragment #{fragment_id} not found in spine item {spine_idx}, "
                f"falling back to body-level XPoint"
            )
            return base_xpoint

        element = cast(etree._Element, xpath_result[0])  # pyright: ignore[reportPrivateUsage]

        # Compute XPath from root and strip /html prefix
        element_xpath: str = tree.getroottree().getpath(element)
        if element_xpath.startswith("/html"):
            element_xpath = element_xpath[len("/html") :]

        return f"/body/DocFragment[{spine_idx}]{element_xpath}"

    def _parse_toc_from_epub(
        self, epub_path: Path
    ) -> list[tuple[str, int, str | None, str | None, str | None]]:
        """
        Parse table of contents from an EPUB file.

        Extracts chapter titles, reading order, hierarchy, and XPoint positions
        from the EPUB's TOC. Handles both NCX (EPUB 2) and Navigation Document
        (EPUB 3) formats.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of (chapter_title, chapter_number, parent_name, start_xpoint, end_xpoint)
            tuples in reading order. parent_name is None for root-level chapters.
            Returns empty list if EPUB has no TOC or TOC is invalid.
        """
        try:
            book = epub.read_epub(str(epub_path))

            # Get TOC from epub (supports both NCX and nav.xhtml)
            toc = book.toc

            if not toc:
                logger.info(f"EPUB at {epub_path} has no table of contents")
                return []

            # Extract hierarchical TOC structure with hrefs
            chapters_with_hrefs = _extract_toc_hierarchy(toc)

            # Build spine mapping and compute XPoints
            spine_mapping = self._build_href_to_spine_index(book)
            result: list[tuple[str, int, str | None, str | None, str | None]] = []
            html_cache: dict[int, etree._Element] = {}  # pyright: ignore[reportPrivateUsage]

            # First pass: compute start_xpoints (with precise fragment resolution)
            start_xpoints: list[str | None] = []
            for _title, _number, _parent, href in chapters_with_hrefs:
                if href:
                    xpoint = self._resolve_href_to_xpoint(book, href, spine_mapping, html_cache)
                    start_xpoints.append(xpoint)
                else:
                    start_xpoints.append(None)

            # Second pass: compute end_xpoints (next chapter's start_xpoint)
            for i, (title, number, parent, _href) in enumerate(chapters_with_hrefs):
                start_xpoint = start_xpoints[i]
                # end_xpoint is the next chapter's start_xpoint (None for last)
                end_xpoint = None
                for j in range(i + 1, len(start_xpoints)):
                    if start_xpoints[j] is not None:
                        end_xpoint = start_xpoints[j]
                        break
                result.append((title, number, parent, start_xpoint, end_xpoint))

            logger.info(f"Parsed {len(result)} chapters from EPUB TOC at {epub_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse TOC from EPUB at {epub_path}: {e!s}")
            return []
