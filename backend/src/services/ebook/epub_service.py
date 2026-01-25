"""Service layer for epub-related operations."""

# pyright: reportPrivateUsage=false, reportArgumentType=false
# pyright: reportReturnType=false, reportGeneralTypeIssues=false
# pyright: reportIndexIssue=false, reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# The above ignores are needed because lxml type stubs don't accurately
# represent xpath() return types which depend on the query string content.

import logging
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from sqlalchemy.orm import Session

from src import models, repositories
from src.exceptions import BookNotFoundError, InvalidEbookError, XPointNavigationError
from src.utils import ParsedXPoint

logger = logging.getLogger(__name__)


def _extract_toc_hierarchy(
    toc_items: list[Any], current_number: int = 1, parent_name: str | None = None
) -> list[tuple[str, int, str | None]]:
    """
    Extract hierarchical TOC structure into a list preserving parent relationships.

    EPUB TOC can be nested. This function preserves the hierarchy while
    assigning sequential chapter numbers for reading order.

    Args:
        toc_items: List of TOC items from ebooklib (can be Link objects or tuples)
        current_number: Starting chapter number (used for recursion)
        parent_name: Name of the parent chapter (None for root-level chapters)

    Returns:
        List of (chapter_title, chapter_number, parent_name) tuples in reading order.
        parent_name is None for root-level chapters.
    """
    chapters = []

    for item in toc_items:
        # TOC items can be Link objects or tuples (Section, [children])
        if isinstance(item, tuple):
            # Nested section: (Link, [children])
            section, children = item[0], item[1] if len(item) > 1 else []

            # Add the section itself
            if hasattr(section, "title"):
                chapters.append((section.title, current_number, parent_name))
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
            chapters.append((item.title, current_number, parent_name))
            current_number += 1

    return chapters


# Directory for epub files (parallel to book-covers)
EPUBS_DIR = Path(__file__).parent.parent.parent / "book-files" / "epubs"


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


class EpubService:
    """Service for handling epub file operations."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = repositories.BookRepository(db)
        self.chapter_repo = repositories.ChapterRepository(db)

    def _upload_epub(self, book_id: int, content: bytes, user_id: int) -> tuple[str, str]:
        """
        Upload and validate an epub file for a book.

        This method:
        1. Validates the book exists and belongs to user
        2. Validates epub structure using ebooklib
        3. Generates sanitized filename from book title and ID
        4. Saves file to epubs directory
        5. Removes old epub file if filename differs
        6. Updates book.file_path and book.file_type in database

        Args:
            book_id: ID of the book
            content: The epub file content as bytes
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            BookNotFoundError: If book not found or doesn't belong to user
            InvalidEbookError: If epub structure validation fails
        """
        # Verify book exists and belongs to user
        book = self.book_repo.get_by_id(book_id, user_id)
        if not book:
            raise BookNotFoundError(book_id)

        # Validate epub structure
        if not _validate_epub(content):
            raise InvalidEbookError("EPUB structure validation failed", ebook_type="EPUB")

        # Create epubs directory if it doesn't exist
        EPUBS_DIR.mkdir(parents=True, exist_ok=True)

        # Generate filename: sanitized_title_bookid.epub
        sanitized_title = _sanitize_filename(book.title)
        epub_filename = f"{sanitized_title}_{book_id}.epub"
        epub_path = EPUBS_DIR / epub_filename

        # Check if book already has an epub file
        old_epub_path = None
        if book.file_path and book.file_type == "epub":
            old_epub_path = EPUBS_DIR / book.file_path

        # Save new epub file
        epub_path.write_bytes(content)
        logger.info(f"Successfully saved epub for book {book_id} at {epub_path}")

        # Delete old epub file if it exists and has different name
        if old_epub_path and old_epub_path != epub_path and old_epub_path.exists():
            try:
                old_epub_path.unlink()
                logger.info(f"Deleted old epub file: {old_epub_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old epub file {old_epub_path}: {e!s}")

        # Update book's file_path and file_type fields in database (store just the filename)
        book.file_path = epub_filename
        book.file_type = "epub"
        self.db.flush()

        # Parse TOC and save chapters to database
        toc_chapters = self._parse_toc_from_epub(epub_path)
        if toc_chapters:
            self._save_chapters_from_toc(book_id, user_id, toc_chapters)

        return epub_filename, str(epub_path)

    def get_epub_path(self, book_id: int, user_id: int) -> Path:
        """
        Get the file path for a book's epub file with ownership verification.

        Args:
            book_id: ID of the book
            user_id: ID of the user requesting the epub

        Returns:
            Path to the epub file

        Raises:
            BookNotFoundError: If book not found or user doesn't own it or epub file doesn't exist
        """
        book = self.book_repo.get_by_id(book_id, user_id)

        if not book or not book.file_path or book.file_type != "epub":
            raise BookNotFoundError(book_id, message="EPUB file not found for this book")

        epub_path = EPUBS_DIR / book.file_path

        if not epub_path.exists() or not epub_path.is_file():
            raise BookNotFoundError(book_id, message="EPUB file not found on disk")

        return epub_path

    def upload_epub_by_client_book_id(
        self, client_book_id: str, content: bytes, user_id: int
    ) -> tuple[str, str]:
        """
        Upload and validate an epub file for a book using client_book_id.

        This method looks up the book by client_book_id and then uploads the epub.
        Used by KOReader which identifies books by client_book_id.

        Args:
            client_book_id: The client-provided book identifier
            content: The epub file content as bytes
            user_id: ID of the user uploading the epub

        Returns:
            tuple[str, str]: (epub_path_for_db, absolute_file_path)

        Raises:
            BookNotFoundError: If book not found for the given client_book_id
            InvalidEbookError: If epub validation fails
        """
        book = self.book_repo.find_by_client_book_id(client_book_id, user_id)

        if not book:
            raise BookNotFoundError(
                message=f"Book with client_book_id '{client_book_id}' not found"
            )

        # Delegate to the existing upload_epub method using book.id
        return self._upload_epub(book.id, content, user_id)

    def delete_epub(self, book_id: int) -> bool:
        """
        Delete the epub file for a book.

        This is called when a book is deleted.
        Does not verify ownership - caller must do that.

        Args:
            book_id: ID of the book

        Returns:
            bool: True if file was deleted, False if file didn't exist
        """
        # Find epub file for this book using glob pattern
        epub_files = list(EPUBS_DIR.glob(f"*_{book_id}.epub"))

        if not epub_files:
            return False

        epub_path = epub_files[0]

        try:
            epub_path.unlink()
            logger.info(f"Deleted epub file for book {book_id}: {epub_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete epub file {epub_path}: {e!s}")
            return False

    def _parse_toc_from_epub(self, epub_path: Path) -> list[tuple[str, int, str | None]]:
        """
        Parse table of contents from an EPUB file.

        Extracts chapter titles, reading order, and hierarchy from the EPUB's TOC.
        Handles both NCX (EPUB 2) and Navigation Document (EPUB 3) formats.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of (chapter_title, chapter_number, parent_name) tuples in reading order.
            parent_name is None for root-level chapters.
            Returns empty list if EPUB has no TOC or TOC is invalid.
        """
        try:
            book = epub.read_epub(str(epub_path))

            # Get TOC from epub (supports both NCX and nav.xhtml)
            toc = book.toc

            if not toc:
                logger.info(f"EPUB at {epub_path} has no table of contents")
                return []

            # Extract hierarchical TOC structure
            chapters = _extract_toc_hierarchy(toc)

            logger.info(f"Parsed {len(chapters)} chapters from EPUB TOC at {epub_path}")
            return chapters

        except Exception as e:
            logger.error(f"Failed to parse TOC from EPUB at {epub_path}: {e!s}")
            return []

    def _save_chapters_from_toc(
        self, book_id: int, user_id: int, chapters: list[tuple[str, int, str | None]]
    ) -> int:
        """
        Save chapters from TOC to the database, preserving hierarchical structure.

        Creates new chapters that don't exist. Updates chapter_number and parent_id
        for existing chapters if they differ from the TOC.

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            chapters: List of (chapter_title, chapter_number, parent_name) tuples

        Returns:
            Number of chapters created (not including updates)
        """
        if not chapters:
            return 0

        # Get existing chapters for this book
        chapter_names = {name for name, _, _ in chapters}
        existing_chapters = self.chapter_repo.get_by_names(book_id, chapter_names, user_id)

        # Track created/existing chapters by name for parent lookups
        chapter_by_name: dict[str, models.Chapter] = existing_chapters.copy()

        # Track chapters by (name, parent_id) to detect true duplicates
        # (same name under same parent = duplicate, different parent = separate chapter)
        chapter_by_name_and_parent: dict[tuple[str, int | None], models.Chapter] = {
            (ch.name, ch.parent_id): ch for ch in existing_chapters.values()
        }

        chapters_to_update = []
        created_count = 0

        # Process chapters in order (parents come before children due to sequential numbering)
        for name, chapter_number, parent_name in chapters:
            # Determine parent_id
            parent_id = None
            if parent_name and parent_name in chapter_by_name:
                parent_id = chapter_by_name[parent_name].id

            # Check if we already have a chapter with this (name, parent_id) combination
            chapter_key = (name, parent_id)
            if chapter_key in chapter_by_name_and_parent:
                # This exact chapter (same name AND parent) already exists
                existing_chapter = chapter_by_name_and_parent[chapter_key]

                # Check if it needs updating
                if name in existing_chapters:
                    needs_update = False

                    if existing_chapter.chapter_number != chapter_number:
                        existing_chapter.chapter_number = chapter_number
                        needs_update = True

                    if existing_chapter.parent_id != parent_id:
                        existing_chapter.parent_id = parent_id
                        needs_update = True

                    if needs_update:
                        chapters_to_update.append(existing_chapter)
                else:
                    # True duplicate in ToC (same name and parent, already created in this loop)
                    logger.warning(
                        f"Duplicate chapter '{name}' in ToC with same parent (parent_id={parent_id}). "
                        f"Skipping duplicate."
                    )
            else:
                # New chapter - create it
                chapter = models.Chapter(
                    book_id=book_id,
                    name=name,
                    chapter_number=chapter_number,
                    parent_id=parent_id,
                )
                self.db.add(chapter)
                self.db.flush()  # Flush to get the ID for potential child chapters
                self.db.refresh(chapter)

                # Add to both tracking dictionaries
                # chapter_by_name: for parent lookups (may overwrite if duplicate names exist)
                # chapter_by_name_and_parent: for duplicate detection (unique key)
                chapter_by_name[name] = chapter
                chapter_by_name_and_parent[chapter_key] = chapter
                created_count += 1

        # Flush updates
        if chapters_to_update:
            self.db.flush()
            logger.info(f"Updated {len(chapters_to_update)} existing chapters")

        logger.info(
            f"Saved TOC for book {book_id}: created {created_count} chapters, "
            f"updated {len(chapters_to_update)} chapters"
        )
        return created_count

    def extract_text_between_xpoints(
        self,
        book_id: int,
        user_id: int,
        start_xpoint: str,
        end_xpoint: str,
    ) -> str:
        """Extract text content between two xpoint positions in an EPUB.

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            start_xpoint: KOReader xpoint string for start position
            end_xpoint: KOReader xpoint string for end position

        Returns:
            The text content between the two positions

        Raises:
            BookNotFoundError: If book not found, user doesn't own it, or EPUB file doesn't exist
            XPointParseError: If xpoint format is invalid
            XPointNavigationError: If cannot navigate to xpoint in EPUB
        """
        epub_path = self.get_epub_path(book_id, user_id)

        start = ParsedXPoint.parse(start_xpoint)
        end = ParsedXPoint.parse(end_xpoint)

        book = epub.read_epub(str(epub_path))

        if start.doc_fragment_index == end.doc_fragment_index:
            return self._extract_within_fragment(book, start, end)
        return self._extract_across_fragments(book, start, end)

    def _get_spine_item_content(
        self,
        book: epub.EpubBook,
        fragment_index: int | None,
    ) -> etree._Element:
        """Get parsed HTML content for a spine item.

        Args:
            book: The loaded EpubBook
            fragment_index: 1-based index into spine, or None for first item

        Returns:
            Parsed lxml element tree for the document

        Raises:
            XPointNavigationError: If index out of range
        """
        spine_index = (fragment_index or 1) - 1

        if spine_index < 0 or spine_index >= len(book.spine):
            raise XPointNavigationError(
                f"DocFragment[{fragment_index or 1}]",
                f"index out of range (spine has {len(book.spine)} items)",
            )

        item_id = book.spine[spine_index][0]
        item = book.get_item_with_id(item_id)

        if item is None:
            raise XPointNavigationError(
                f"DocFragment[{fragment_index or 1}]",
                f"spine item '{item_id}' not found in EPUB",
            )

        content = item.get_content()
        parser = etree.HTMLParser()
        return etree.fromstring(content, parser)

    def _extract_within_fragment(
        self,
        book: epub.EpubBook,
        start: ParsedXPoint,
        end: ParsedXPoint,
    ) -> str:
        """Extract text when start and end are in same DocFragment.

        Uses streaming approach to handle mixed content where
        child elements appear between text nodes.
        """
        tree = self._get_spine_item_content(book, start.doc_fragment_index)

        # Resolve xpoints to actual element/attribute locations
        start_elem = self._find_element(tree, start)
        start_target_elem, start_attr = self._resolve_text_node_location(
            start_elem, start.text_node_index, tree
        )

        end_elem = self._find_element(tree, end)
        end_target_elem, end_attr = self._resolve_text_node_location(
            end_elem, end.text_node_index, tree
        )

        # Get the body element for iteration
        body = tree.xpath("//body")
        if not body:
            return ""

        # Use streaming extraction to maintain document order
        return self._extract_between_locations(
            body[0],
            start_target_elem,
            start_attr,
            start.char_offset,
            end_target_elem,
            end_attr,
            end.char_offset,
        )

    def _convert_xpath(self, xpath: str) -> str:
        """Convert xpoint xpath to lxml-compatible xpath."""
        if xpath.startswith("/body"):
            return "//body" + xpath[5:]
        return xpath

    def _find_element(self, tree: etree._Element, parsed: ParsedXPoint) -> etree._Element:
        """Find element by xpath, raising XPointNavigationError if not found."""
        xpath = self._convert_xpath(parsed.xpath)
        elements = tree.xpath(xpath)
        if not elements:
            raise XPointNavigationError(
                f"{parsed.xpath}/text().{parsed.char_offset}",
                f"XPath '{parsed.xpath}' matched no elements",
            )
        return elements[0]

    def _resolve_text_node_location(
        self,
        element: etree._Element,
        text_node_index: int,
        root: etree._Element | None = None,
    ) -> tuple[etree._Element, str]:
        """Resolve a 1-based text node index to (element, attribute) pair.

        In lxml's tree model, text content is stored in two places:
        - element.text: text before the first child
        - child.tail: text after each child element

        This method maps the XPath text() node index to the actual location.

        Args:
            element: The element containing the text nodes
            text_node_index: 1-based index of the text node (as used by XPath)
            root: Optional root element to allow searching for next text node
                  if the element itself is empty (fallback for empty anchors)

        Returns:
            Tuple of (element, attribute) where attribute is 'text' or 'tail'

        Raises:
            XPointNavigationError: If text_node_index is out of range and no fallback possible
        """
        current_idx = 1  # text_node_index is 1-based

        # First text node is element.text (if it exists)
        if element.text:
            if current_idx == text_node_index:
                return element, "text"
            current_idx += 1

        # Subsequent text nodes are child.tail values
        for child in element:
            if child.tail:
                if current_idx == text_node_index:
                    return child, "tail"
                current_idx += 1

        # Fallback: if element has 0 text nodes and we asked for index 1,
        # it might be an empty anchor acting as a marker.
        # Find the next text node in the document.
        if current_idx == 1 and text_node_index == 1 and root is not None:
            next_loc = self._find_next_text_node(root, element)
            if next_loc:
                return next_loc

        raise XPointNavigationError(
            f"text()[{text_node_index}]",
            f"text node index out of range (element has {current_idx - 1} text nodes)",
        )

    def _find_next_text_node(
        self, root: etree._Element, start_from: etree._Element
    ) -> tuple[etree._Element, str] | None:
        """Find the next text node in document order starting after start_from."""
        found_start = False
        for elem in root.iter():
            if elem == start_from:
                found_start = True
                if elem.tail:
                    return elem, "tail"
                continue

            if found_start:
                if elem.text:
                    return elem, "text"
                if elem.tail:
                    return elem, "tail"
        return None

    def _iter_text_locations(self, root: etree._Element) -> list[tuple[etree._Element, str, str]]:
        """Iterate through all text content in document order.

        Yields tuples of (element, attribute, text) for each text segment.
        This respects document order by following the tree structure.

        Args:
            root: Root element to iterate from

        Returns:
            List of (element, attribute_name, text_content) tuples
        """
        locations = []
        for elem in root.iter():
            if elem.text:
                locations.append((elem, "text", elem.text))
            if elem.tail:
                locations.append((elem, "tail", elem.tail))
        return locations

    def _extract_between_locations(
        self,
        root: etree._Element,
        start_elem: etree._Element | None,
        start_attr: str | None,
        start_offset: int,
        end_elem: etree._Element | None,
        end_attr: str | None,
        end_offset: int | None,
    ) -> str:
        """Extract text between two resolved locations in document order.

        This method correctly handles mixed content by iterating through
        the document in tree order, respecting the text/tail structure.

        Args:
            root: Root element to search within
            start_elem: Element containing start position (None = start from beginning)
            start_attr: Attribute ('text' or 'tail') for start position
            start_offset: Character offset within start text
            end_elem: Element containing end position (None = continue to end)
            end_attr: Attribute ('text' or 'tail') for end position
            end_offset: Character offset within end text

        Returns:
            Extracted text content
        """
        result_parts = []
        capturing = start_elem is None  # If no start specified, capture from beginning

        for elem, attr, text in self._iter_text_locations(root):
            if not capturing:
                # Check if this is the start location
                if elem == start_elem and attr == start_attr:
                    capturing = True
                    # Check if start and end are at the same location
                    if end_elem is not None and elem == end_elem and attr == end_attr:
                        result_parts.append(text[start_offset:end_offset])
                        break
                    result_parts.append(text[start_offset:])
            # Check if this is the end location
            elif end_elem is not None and elem == end_elem and attr == end_attr:
                result_parts.append(text[:end_offset])
                break
            else:
                result_parts.append(text)

        return "".join(result_parts)

    def _extract_across_fragments(
        self,
        book: epub.EpubBook,
        start: ParsedXPoint,
        end: ParsedXPoint,
    ) -> str:
        """Extract text when start and end are in different DocFragments."""
        if start.doc_fragment_index is None or end.doc_fragment_index is None:
            raise XPointNavigationError(
                "cross-fragment",
                "cannot extract across fragments when DocFragment index is missing",
            )

        result_parts = []

        start_tree = self._get_spine_item_content(book, start.doc_fragment_index)
        result_parts.append(self._extract_from_position_to_end(start_tree, start))

        for frag_idx in range(start.doc_fragment_index + 1, end.doc_fragment_index):
            tree = self._get_spine_item_content(book, frag_idx)
            body = tree.xpath("//body")
            if body:
                result_parts.append("".join(body[0].itertext()))

        end_tree = self._get_spine_item_content(book, end.doc_fragment_index)
        result_parts.append(self._extract_from_start_to_position(end_tree, end))

        return "".join(result_parts)

    def _extract_from_position_to_end(
        self,
        tree: etree._Element,
        start: ParsedXPoint,
    ) -> str:
        """Extract text from xpoint position to end of document body.

        Uses streaming approach to correctly handle mixed content.
        """
        # Resolve start xpoint to element/attribute location
        start_elem = self._find_element(tree, start)
        start_target_elem, start_attr = self._resolve_text_node_location(
            start_elem, start.text_node_index, tree
        )

        # Get the body element for iteration
        body = tree.xpath("//body")
        if not body:
            return ""

        # Extract from start to end (None end means extract to end of document)
        return self._extract_between_locations(
            body[0],
            start_target_elem,
            start_attr,
            start.char_offset,
            None,  # No end element - extract to end
            None,
            None,
        )

    def _extract_from_start_to_position(
        self,
        tree: etree._Element,
        end: ParsedXPoint,
    ) -> str:
        """Extract text from start of document body to xpoint position.

        Uses streaming approach to correctly handle mixed content.
        """
        # Resolve end xpoint to element/attribute location
        end_elem = self._find_element(tree, end)
        end_target_elem, end_attr = self._resolve_text_node_location(
            end_elem, end.text_node_index, tree
        )

        # Get the body element for iteration
        body = tree.xpath("//body")
        if not body:
            return ""

        # Extract from start to end (None start means extract from beginning)
        return self._extract_between_locations(
            body[0],
            None,  # No start element - extract from beginning
            None,
            0,
            end_target_elem,
            end_attr,
            end.char_offset,
        )
