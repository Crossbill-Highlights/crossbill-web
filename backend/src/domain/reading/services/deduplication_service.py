"""
Domain service for highlight deduplication logic.

This is a pure domain service with no infrastructure dependencies.
"""

from src.domain.common.value_objects import ContentHash
from src.domain.reading.entities.highlight import Highlight


class HighlightDeduplicationService:
    """
    Domain service for identifying duplicate highlights.

    Deduplication is based on content_hash - highlights with
    the same hash are considered duplicates.
    """

    def find_duplicates(
        self,
        new_highlights: list[Highlight],
        existing_hashes: set[ContentHash],
    ) -> tuple[list[Highlight], list[Highlight]]:
        """
        Separate new highlights into unique and duplicates.

        Args:
            new_highlights: List of highlights to check
            existing_hashes: Set of content hashes that already exist

        Returns:
            Tuple of (unique_highlights, duplicate_highlights)
        """
        unique: list[Highlight] = []
        duplicates: list[Highlight] = []

        # Track hashes we've seen in this batch
        seen_in_batch: set[ContentHash] = set(existing_hashes)

        for highlight in new_highlights:
            if highlight.content_hash in seen_in_batch:
                duplicates.append(highlight)
            else:
                unique.append(highlight)
                seen_in_batch.add(highlight.content_hash)

        return unique, duplicates

    def find_duplicate_pairs(
        self,
        highlights: list[Highlight],
    ) -> list[tuple[Highlight, Highlight]]:
        """
        Find pairs of duplicates within a list of highlights.

        Useful for cleanup operations.

        Args:
            highlights: List of highlights to check

        Returns:
            List of duplicate pairs
        """
        hash_to_highlights: dict[ContentHash, list[Highlight]] = {}

        for highlight in highlights:
            if highlight.content_hash not in hash_to_highlights:
                hash_to_highlights[highlight.content_hash] = []
            hash_to_highlights[highlight.content_hash].append(highlight)

        pairs: list[tuple[Highlight, Highlight]] = []
        for highlights_group in hash_to_highlights.values():
            if len(highlights_group) > 1:
                # Create pairs from duplicates
                for i in range(len(highlights_group) - 1):
                    pairs.append((highlights_group[i], highlights_group[i + 1]))

        return pairs
