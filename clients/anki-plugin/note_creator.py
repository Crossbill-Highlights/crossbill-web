"""
Note Creator for Crossbill Anki Plugin

Handles creation of Anki notes from Crossbill highlights.
"""

from typing import List, Optional, Set
import re
from aqt import mw
from anki.notes import Note
from models import Highlight, BookDetails, PluginConfig


class NoteCreator:
    """Creates Anki notes from Crossbill highlights"""

    def __init__(self, config: PluginConfig):
        """
        Initialize note creator

        Args:
            config: Plugin configuration
        """
        self.config = config

    def create_note_from_highlight(
        self,
        highlight: Highlight,
        book: BookDetails,
        deck_name: str,
        note_type_name: Optional[str] = None
    ) -> Optional[Note]:
        """
        Create an Anki note from a Crossbill highlight

        Args:
            highlight: The highlight to convert
            book: The book containing the highlight
            deck_name: Name of the deck to add the note to
            note_type_name: Name of the note type to use (defaults to config)

        Returns:
            The created Note object, or None if creation failed
        """
        if not note_type_name:
            note_type_name = self.config.default_note_type

        # Get the deck
        deck_id = mw.col.decks.id(deck_name)
        if not deck_id:
            return None

        # Get the note type (model)
        model = mw.col.models.by_name(note_type_name)
        if not model:
            return None

        # Create the note
        note = Note(mw.col, model)
        note.note_type()['did'] = deck_id

        # Format the note based on note type
        if note_type_name == "Basic" or note_type_name == "Basic (and reversed card)":
            self._format_basic_note(note, highlight, book)
        else:
            # Try to use a custom note type with similar fields
            self._format_custom_note(note, highlight, book)

        # Add tags
        if self.config.auto_tag:
            tags = self._generate_tags(highlight, book)
            for tag in tags:
                note.add_tag(tag)

        # Add Crossbill metadata tag to track imports
        note.add_tag(f"{self.config.tag_prefix}::imported")
        note.add_tag(f"{self.config.tag_prefix}::highlight-{highlight.id}")

        return note

    def _format_basic_note(self, note: Note, highlight: Highlight, book: BookDetails):
        """
        Format a Basic note type

        Args:
            note: The note to format
            highlight: The highlight data
            book: The book data
        """
        # Front: The highlight text
        front = self._sanitize_html(highlight.text)

        # Back: Context and metadata
        back_parts = []

        # Add book title and author
        back_parts.append(f"<b>From:</b> {self._sanitize_html(book.title)}")
        if book.author:
            back_parts.append(f"<b>Author:</b> {self._sanitize_html(book.author)}")

        # Add chapter if available
        if highlight.chapter:
            back_parts.append(f"<b>Chapter:</b> {self._sanitize_html(highlight.chapter)}")

        # Add page if available
        if highlight.page:
            back_parts.append(f"<b>Page:</b> {highlight.page}")

        # Add user's note if available
        if highlight.note:
            back_parts.append("")  # Empty line for spacing
            back_parts.append(f"<b>Note:</b>")
            back_parts.append(self._sanitize_html(highlight.note))

        back = "<br>".join(back_parts)

        # Set the fields
        note['Front'] = front
        note['Back'] = back

    def _format_custom_note(self, note: Note, highlight: Highlight, book: BookDetails):
        """
        Format a custom note type by mapping fields intelligently

        Args:
            note: The note to format
            highlight: The highlight data
            book: The book data
        """
        fields = list(note.keys())

        # Try to find Front field
        front_field = None
        for field in fields:
            if field.lower() in ['front', 'question', 'text']:
                front_field = field
                break

        if front_field:
            note[front_field] = self._sanitize_html(highlight.text)

        # Try to find Back field
        back_field = None
        for field in fields:
            if field.lower() in ['back', 'answer', 'extra']:
                back_field = field
                break

        if back_field:
            # Create context similar to Basic note
            back_parts = []
            back_parts.append(f"<b>From:</b> {self._sanitize_html(book.title)}")
            if book.author:
                back_parts.append(f"<b>Author:</b> {self._sanitize_html(book.author)}")
            if highlight.chapter:
                back_parts.append(f"<b>Chapter:</b> {self._sanitize_html(highlight.chapter)}")
            if highlight.page:
                back_parts.append(f"<b>Page:</b> {highlight.page}")
            if highlight.note:
                back_parts.append("")
                back_parts.append(f"<b>Note:</b>")
                back_parts.append(self._sanitize_html(highlight.note))

            note[back_field] = "<br>".join(back_parts)

        # If there's a Source field, use it
        for field in fields:
            if field.lower() in ['source', 'reference']:
                source = book.title
                if book.author:
                    source += f" by {book.author}"
                note[field] = self._sanitize_html(source)
                break

    def _generate_tags(self, highlight: Highlight, book: BookDetails) -> List[str]:
        """
        Generate tags for the note

        Args:
            highlight: The highlight data
            book: The book data

        Returns:
            List of tags to add
        """
        tags = []

        # Add book title as tag (sanitized)
        book_tag = self._sanitize_tag(book.title)
        if book_tag:
            tags.append(f"{self.config.tag_prefix}::book::{book_tag}")

        # Add author as tag if available
        if book.author:
            author_tag = self._sanitize_tag(book.author)
            if author_tag:
                tags.append(f"{self.config.tag_prefix}::author::{author_tag}")

        # Add highlight tags from Crossbill
        for hl_tag in highlight.highlight_tags:
            tag = self._sanitize_tag(hl_tag.name)
            if tag:
                tags.append(f"{self.config.tag_prefix}::tag::{tag}")

        return tags

    def _sanitize_tag(self, tag: str) -> str:
        """
        Sanitize a tag name for Anki

        Args:
            tag: The tag to sanitize

        Returns:
            Sanitized tag name
        """
        # Remove special characters and replace spaces with underscores
        tag = re.sub(r'[^\w\s-]', '', tag)
        tag = re.sub(r'\s+', '_', tag.strip())
        return tag.lower()

    def _sanitize_html(self, text: str) -> str:
        """
        Sanitize text for HTML display in Anki

        Args:
            text: The text to sanitize

        Returns:
            Sanitized HTML
        """
        if not text:
            return ""

        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')

        # Convert newlines to <br> tags
        text = text.replace('\n', '<br>')

        return text

    def get_imported_highlight_ids(self) -> Set[int]:
        """
        Get the set of highlight IDs that have already been imported

        Returns:
            Set of highlight IDs
        """
        imported_ids = set()

        # Search for notes with the imported tag
        query = f"tag:{self.config.tag_prefix}::imported"
        note_ids = mw.col.find_notes(query)

        # Extract highlight IDs from tags
        for note_id in note_ids:
            note = mw.col.get_note(note_id)
            for tag in note.tags:
                if tag.startswith(f"{self.config.tag_prefix}::highlight-"):
                    try:
                        highlight_id = int(tag.split('-')[1])
                        imported_ids.add(highlight_id)
                    except (ValueError, IndexError):
                        continue

        return imported_ids

    def is_highlight_imported(self, highlight_id: int) -> bool:
        """
        Check if a highlight has already been imported

        Args:
            highlight_id: The highlight ID to check

        Returns:
            True if already imported, False otherwise
        """
        query = f"tag:{self.config.tag_prefix}::highlight-{highlight_id}"
        note_ids = mw.col.find_notes(query)
        return len(note_ids) > 0

    def import_highlights(
        self,
        highlights: List[Highlight],
        book: BookDetails,
        deck_name: str,
        note_type_name: Optional[str] = None,
        skip_duplicates: bool = True
    ) -> dict:
        """
        Import multiple highlights as notes

        Args:
            highlights: List of highlights to import
            book: The book containing the highlights
            deck_name: Name of the deck to add notes to
            note_type_name: Name of the note type to use
            skip_duplicates: Whether to skip already imported highlights

        Returns:
            Dictionary with import statistics:
            {
                'created': int,
                'skipped': int,
                'failed': int,
                'errors': List[str]
            }
        """
        stats = {
            'created': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }

        for highlight in highlights:
            # Check for duplicates
            if skip_duplicates and self.is_highlight_imported(highlight.id):
                stats['skipped'] += 1
                continue

            try:
                note = self.create_note_from_highlight(
                    highlight, book, deck_name, note_type_name
                )

                if note:
                    # Add the note to the collection
                    mw.col.add_note(note, deck_id=mw.col.decks.id(deck_name))
                    stats['created'] += 1
                else:
                    stats['failed'] += 1
                    stats['errors'].append(
                        f"Failed to create note for highlight {highlight.id}"
                    )

            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(
                    f"Error importing highlight {highlight.id}: {str(e)}"
                )

        return stats
