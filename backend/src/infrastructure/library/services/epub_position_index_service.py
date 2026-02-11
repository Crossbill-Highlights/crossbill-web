"""Infrastructure service for building document-order position indices from EPUB files."""

import logging
from pathlib import Path

from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from src.domain.common.value_objects.position_index import PositionIndex

logger = logging.getLogger(__name__)


class EpubPositionIndexService:
    """Builds a position index by walking EPUB DOM in document order."""

    def build_position_index(self, epub_path: Path) -> PositionIndex:
        """
        Build a position index from an EPUB file.

        Walks all spine items in order, parsing each HTML document's DOM
        in document order, and assigns a sequential integer to each element.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            PositionIndex mapping (doc_fragment_index, xpath) -> element_index
        """
        book = epub.read_epub(str(epub_path))
        items_by_id = {item.id: item for item in book.get_items()}

        element_positions: dict[tuple[int, str], int] = {}
        current_index = 1

        for spine_index, (item_id, _linear) in enumerate(book.spine, start=1):
            item = items_by_id.get(item_id)
            if item is None:
                continue

            content = item.get_content()
            parser = etree.HTMLParser()
            tree = etree.fromstring(content, parser)
            root_tree = tree.getroottree()

            # Walk DOM in document order
            for element in tree.iter():
                if not isinstance(element.tag, str):
                    continue  # Skip comments, processing instructions

                element_xpath: str = root_tree.getpath(element)
                # lxml gives paths like /html/body/div[1]/p[2]
                # We need /body/div[1]/p[2] (strip /html prefix)
                if element_xpath.startswith("/html"):
                    element_xpath = element_xpath[len("/html"):]

                key = (spine_index, element_xpath)
                element_positions[key] = current_index
                current_index += 1

        logger.info(
            "Built position index from EPUB",
            extra={
                "epub_path": str(epub_path),
                "total_elements": current_index - 1,
            },
        )

        return PositionIndex(element_positions)
