"""Application service for ebook text extraction operations."""

# pyright: reportPrivateUsage=false, reportArgumentType=false
# pyright: reportReturnType=false, reportGeneralTypeIssues=false
# pyright: reportIndexIssue=false, reportAttributeAccessIssue=false
# pyright: reportCallIssue=false
# The above ignores are needed because lxml type stubs don't accurately
# represent xpath() return types which depend on the query string content.

import logging

from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]
from sqlalchemy.orm import Session

from src.domain.common.value_objects.ids import BookId, UserId
from src.domain.common.value_objects.xpoint import XPoint
from src.exceptions import BookNotFoundError, XPointNavigationError
from src.infrastructure.library.repositories import BookRepository
from src.infrastructure.library.repositories.file_repository import FileRepository

logger = logging.getLogger(__name__)


class EbookTextExtractionService:
    """Application service for extracting text from ebook files."""

    def __init__(self, db: Session) -> None:
        """Initialize service with database session."""
        self.db = db
        self.book_repo = BookRepository(db)
        self.file_repo = FileRepository()

    def extract_text(
        self,
        book_id: BookId,
        user_id: UserId,
        start: str | int,
        end: str | int,
    ) -> str:
        """
        Extract text content between two positions in an ebook.

        Supports both XPoint-based extraction (for EPUB) and page-based extraction (for PDF).

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            start: Start position (XPoint string for EPUB, page number for PDF)
            end: End position (XPoint string for EPUB, page number for PDF)

        Returns:
            The text content between the two positions

        Raises:
            BookNotFoundError: If book not found, user doesn't own it, or file doesn't exist
            XPointNavigationError: If cannot navigate to xpoint in EPUB
            NotImplementedError: If PDF extraction is requested (not yet implemented)
        """
        # Route by parameter type
        if isinstance(start, str) and isinstance(end, str):
            # XPoint-based extraction for EPUB
            return self._extract_epub_text(book_id, user_id, start, end)
        if isinstance(start, int) and isinstance(end, int):
            # Page-based extraction for PDF
            raise NotImplementedError("PDF text extraction not yet implemented")
        raise ValueError("Start and end must both be strings (XPoints) or both be integers (pages)")

    def _extract_epub_text(
        self,
        book_id: BookId,
        user_id: UserId,
        start_xpoint: str,
        end_xpoint: str,
    ) -> str:
        """
        Extract text content between two XPoint positions in an EPUB.

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            start_xpoint: KOReader xpoint string for start position
            end_xpoint: KOReader xpoint string for end position

        Returns:
            The text content between the two positions

        Raises:
            BookNotFoundError: If book not found, user doesn't own it, or EPUB file doesn't exist
            XPointNavigationError: If cannot navigate to xpoint in EPUB
        """
        # Verify book ownership
        book = self.book_repo.find_by_id(book_id, user_id)
        if not book or not book.file_path or book.file_type != "epub":
            logger.error(
                f"EPUB lookup failed: book_id={book_id.value}, user_id={user_id.value}, "
                f"book={'found' if book else 'None'}, "
                f"file_path={book.file_path if book else 'N/A'}, "
                f"file_type={book.file_type if book else 'N/A'}"
            )
            raise BookNotFoundError(book_id.value, message="EPUB file not found for this book")

        # Get EPUB file path
        epub_path = self.file_repo.find_epub(book.id)
        logger.error(f"Epub path {epub_path}")
        if not epub_path or not epub_path.exists():
            raise BookNotFoundError(book_id.value, message="EPUB file not found on disk")

        # Parse XPoints using domain object
        start = XPoint.parse(start_xpoint)
        end = XPoint.parse(end_xpoint)

        # Load EPUB
        epub_book = epub.read_epub(str(epub_path))

        # Extract text based on whether positions are in same fragment
        if start.doc_fragment_index == end.doc_fragment_index:
            return self._extract_within_fragment(epub_book, start, end)
        return self._extract_across_fragments(epub_book, start, end)

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
        start: XPoint,
        end: XPoint,
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

    def _find_element(self, tree: etree._Element, xpoint: XPoint) -> etree._Element:
        """Find element by xpath, raising XPointNavigationError if not found."""
        xpath = self._convert_xpath(xpoint.xpath)
        elements = tree.xpath(xpath)
        if not elements:
            raise XPointNavigationError(
                f"{xpoint.xpath}/text().{xpoint.char_offset}",
                f"XPath '{xpoint.xpath}' matched no elements",
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
        start: XPoint,
        end: XPoint,
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
        start: XPoint,
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

    def _extract_text_by_element_range(
        self,
        body: etree._Element,
        start_elem: etree._Element | None,
        end_elem: etree._Element | None,
    ) -> str:
        """Extract text from elements in document order between start and end elements.

        Collects text from all elements in [start_elem, end_elem) range (end exclusive).
        Uses _iter_text_locations for proper text/tail handling.

        Args:
            body: The <body> element to iterate over
            start_elem: Element where extraction starts (None = start from body)
            end_elem: Element where extraction stops (exclusive). None = to end of body.

        Returns:
            Extracted text content
        """
        if start_elem is not None and start_elem is end_elem:
            # Both point to same element — return all its text
            return "".join(start_elem.itertext())

        # Build document-order list of all elements
        all_elements = list(body.iter())

        # Find indices
        if start_elem is not None:
            try:
                start_idx = all_elements.index(start_elem)
            except ValueError:
                start_idx = 0
        else:
            start_idx = 0

        if end_elem is not None:
            try:
                end_idx = all_elements.index(end_elem)
            except ValueError:
                end_idx = len(all_elements)
        else:
            end_idx = len(all_elements)

        # Build set of elements in range [start_idx, end_idx)
        elements_in_range = set(all_elements[start_idx:end_idx])

        # Collect text from those elements
        result_parts: list[str] = []
        for elem, _attr, text in self._iter_text_locations(body):
            if elem in elements_in_range:
                result_parts.append(text)

        return "".join(result_parts)

    def extract_chapter_text(  # noqa: PLR0912
        self,
        book_id: BookId,
        user_id: UserId,
        start_xpoint: str,
        end_xpoint: str | None,
    ) -> str:
        """Extract all text for a chapter defined by XPoints.

        Handles three cases:
        1. Same fragment: both XPoints in same spine item — extract element range
        2. Cross-fragment: XPoints in different spine items — element range + full fragments
        3. Last chapter (no end_xpoint): extract from start element to end of spine

        Args:
            book_id: ID of the book
            user_id: ID of the user (for ownership verification)
            start_xpoint: XPoint string for chapter start
            end_xpoint: XPoint string for next chapter's start, or None for last chapter

        Returns:
            The full text content of the chapter
        """
        start = XPoint.parse(start_xpoint)
        end = XPoint.parse(end_xpoint) if end_xpoint else None

        if start.doc_fragment_index is None:
            raise XPointNavigationError(
                start_xpoint, "chapter XPoint must have a DocFragment index"
            )

        # Verify book ownership and get EPUB
        book = self.book_repo.find_by_id(book_id, user_id)
        if not book or not book.file_path or book.file_type != "epub":
            raise BookNotFoundError(book_id.value, message="EPUB file not found for this book")

        epub_path = self.file_repo.find_epub(book.id)
        if not epub_path or not epub_path.exists():
            raise BookNotFoundError(book_id.value, message="EPUB file not found on disk")

        epub_book = epub.read_epub(str(epub_path))

        start_frag = start.doc_fragment_index
        end_frag = end.doc_fragment_index if end else None

        # Case 1: Same fragment
        if end_frag is not None and start_frag == end_frag:
            tree = self._get_spine_item_content(epub_book, start_frag)
            body = tree.xpath("//body")
            if not body:
                return ""
            start_elem = self._find_element(tree, start)
            end_elem = self._find_element(tree, end)  # pyright: ignore[reportArgumentType]
            return self._extract_text_by_element_range(body[0], start_elem, end_elem)

        # Case 2: Cross-fragment (or last chapter)
        result_parts: list[str] = []

        # First fragment: from start element to end of fragment
        first_tree = self._get_spine_item_content(epub_book, start_frag)
        first_body = first_tree.xpath("//body")
        if first_body:
            start_elem = self._find_element(first_tree, start)
            result_parts.append(
                self._extract_text_by_element_range(first_body[0], start_elem, None)
            )

        # Determine range of middle/remaining fragments
        if end_frag is not None:
            # Cross-fragment: middle fragments are full, end fragment needs element range
            for frag_idx in range(start_frag + 1, end_frag):
                tree = self._get_spine_item_content(epub_book, frag_idx)
                body = tree.xpath("//body")
                if body:
                    result_parts.append("".join(body[0].itertext()))

            # Last fragment: only if end XPoint has a precise xpath (not just /body)
            if end.xpath != "/body":  # pyright: ignore[reportOptionalMemberAccess]
                end_tree = self._get_spine_item_content(epub_book, end_frag)
                end_body = end_tree.xpath("//body")
                if end_body:
                    end_elem = self._find_element(end_tree, end)  # pyright: ignore[reportArgumentType]
                    result_parts.append(
                        self._extract_text_by_element_range(end_body[0], None, end_elem)
                    )
            # If end.xpath == "/body", skip end fragment entirely
            # (next chapter starts at beginning of that fragment)
        else:
            # Last chapter: all remaining fragments to end of spine
            for frag_idx in range(start_frag + 1, len(epub_book.spine) + 1):
                tree = self._get_spine_item_content(epub_book, frag_idx)
                body = tree.xpath("//body")
                if body:
                    result_parts.append("".join(body[0].itertext()))

        return "".join(result_parts)

    def _extract_from_start_to_position(
        self,
        tree: etree._Element,
        end: XPoint,
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
