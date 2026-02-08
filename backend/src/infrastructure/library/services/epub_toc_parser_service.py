"""Infrastructure service for parsing EPUB table of contents."""

# pyright: reportPrivateUsage=false

import logging
from io import BytesIO
from pathlib import Path
from typing import Any, cast

from ebooklib import epub
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from src.domain.library.entities.chapter import TocChapter

logger = logging.getLogger(__name__)


def _extract_toc_hierarchy(
    toc_items: list[Any], current_number: int = 1, parent_name: str | None = None
) -> list[tuple[str, int, str | None, str | None]]:
    """
    Extract hierarchical TOC structure into a list preserving parent relationships.

    Args:
        toc_items: List of TOC items from ebooklib (can be Link objects or tuples)
        current_number: Starting chapter number (used for recursion)
        parent_name: Name of the parent chapter (None for root-level chapters)

    Returns:
        List of (chapter_title, chapter_number, parent_name, href) tuples in reading order.
    """
    chapters: list[tuple[str, int, str | None, str | None]] = []

    for item in toc_items:
        if isinstance(item, tuple):
            section, children = item[0], item[1] if len(item) > 1 else []

            if hasattr(section, "title"):
                href = getattr(section, "href", None)
                chapters.append((section.title, current_number, parent_name, href))
                section_name = section.title
                current_number += 1
            else:
                section_name = parent_name

            child_chapters = _extract_toc_hierarchy(children, current_number, section_name)
            chapters.extend(child_chapters)
            current_number += len(child_chapters)

        elif hasattr(item, "title"):
            href = getattr(item, "href", None)
            chapters.append((item.title, current_number, parent_name, href))
            current_number += 1

    return chapters


class EpubTocParserService:
    """Infrastructure service for parsing EPUB table of contents and validation."""

    def validate_epub(self, content: bytes) -> bool:
        """
        Validate epub file using ebooklib.

        Args:
            content: The file content as bytes

        Returns:
            True if valid epub, False otherwise
        """
        try:
            epub_file = BytesIO(content)
            book = epub.read_epub(epub_file)

            if not book.get_metadata("DC", "title"):
                logger.warning("EPUB missing title metadata")

            return True

        except Exception as e:
            logger.error(f"EPUB validation failed: {e!s}")
            return False

    def parse_toc(self, epub_path: Path) -> list[TocChapter]:
        """
        Parse table of contents from an EPUB file.

        Args:
            epub_path: Path to the EPUB file

        Returns:
            List of TocChapter objects in reading order.
            Returns empty list if EPUB has no TOC or TOC is invalid.
        """
        try:
            book = epub.read_epub(str(epub_path))

            toc = book.toc

            if not toc:
                logger.info(f"EPUB at {epub_path} has no table of contents")
                return []

            chapters_with_hrefs = _extract_toc_hierarchy(toc)

            spine_mapping = self._build_href_to_spine_index(book)
            result: list[TocChapter] = []
            html_cache: dict[int, etree._Element] = {}

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
                end_xpoint = None
                for j in range(i + 1, len(start_xpoints)):
                    if start_xpoints[j] is not None:
                        end_xpoint = start_xpoints[j]
                        break
                result.append(
                    TocChapter(
                        name=title,
                        chapter_number=number,
                        parent_name=parent,
                        start_xpoint=start_xpoint,
                        end_xpoint=end_xpoint,
                    )
                )

            logger.info(f"Parsed {len(result)} chapters from EPUB TOC at {epub_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse TOC from EPUB at {epub_path}: {e!s}")
            return []

    @staticmethod
    def _build_href_to_spine_index(book: Any) -> dict[str, int]:  # noqa: ANN401
        """Build a mapping from spine item file names to 1-based spine indices."""
        mapping: dict[str, int] = {}
        spine_items = book.spine
        items_by_id = {item.id: item for item in book.get_items()}

        for idx, (item_id, _linear) in enumerate(spine_items, start=1):
            item = items_by_id.get(item_id)
            if item:
                file_name = item.file_name
                mapping[file_name] = idx
                basename = file_name.rsplit("/", 1)[-1] if "/" in file_name else file_name
                if basename not in mapping:
                    mapping[basename] = idx
        return mapping

    @staticmethod
    def _href_to_spine_index(href: str, mapping: dict[str, int]) -> int | None:
        """Resolve a TOC href to a spine index using the mapping."""
        file_part = href.split("#")[0]

        if file_part in mapping:
            return mapping[file_part]

        basename = file_part.rsplit("/", 1)[-1] if "/" in file_part else file_part
        return mapping.get(basename)

    @staticmethod
    def _resolve_href_to_xpoint(
        book: Any,  # noqa: ANN401
        href: str,
        spine_mapping: dict[str, int],
        html_cache: dict[int, etree._Element],
    ) -> str | None:
        """Resolve a TOC href to a precise XPoint string."""
        parts = href.split("#", 1)
        file_part = parts[0]
        fragment_id = parts[1] if len(parts) > 1 else None

        spine_idx = EpubTocParserService._href_to_spine_index(file_part, spine_mapping)
        if spine_idx is None:
            spine_idx = EpubTocParserService._href_to_spine_index(href.split("#")[0], spine_mapping)
            if spine_idx is None:
                return None

        base_xpoint = f"/body/DocFragment[{spine_idx}]/body"

        if not fragment_id:
            return base_xpoint

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

        xpath_result = tree.xpath(f'//*[@id="{fragment_id}"]')
        if not isinstance(xpath_result, list) or not xpath_result:
            logger.warning(
                f"Fragment #{fragment_id} not found in spine item {spine_idx}, "
                f"falling back to body-level XPoint"
            )
            return base_xpoint

        element = cast(etree._Element, xpath_result[0])

        element_xpath: str = tree.getroottree().getpath(element)
        if element_xpath.startswith("/html"):
            element_xpath = element_xpath[len("/html") :]

        return f"/body/DocFragment[{spine_idx}]{element_xpath}"
