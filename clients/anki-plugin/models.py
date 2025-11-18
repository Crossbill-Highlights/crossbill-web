"""
Data models for Crossbill Anki Plugin

These models match the Crossbill API response schemas and internal plugin data.
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Book:
    """Represents a book in Crossbill"""
    id: int
    title: str
    author: Optional[str]
    isbn: Optional[str]
    created_at: str
    updated_at: str


@dataclass
class BookWithHighlightCount(Book):
    """Book with the count of highlights"""
    highlight_count: int


@dataclass
class HighlightTag:
    """Tag associated with a highlight"""
    id: int
    name: str


@dataclass
class Highlight:
    """Represents a highlight from a book"""
    id: int
    book_id: int
    chapter_id: Optional[int]
    text: str
    chapter: Optional[str]
    page: Optional[int]
    note: Optional[str]
    datetime: str
    highlight_tags: List[HighlightTag]
    created_at: str
    updated_at: str


@dataclass
class Chapter:
    """Represents a chapter in a book"""
    id: int
    book_id: int
    name: str
    created_at: str
    updated_at: str


@dataclass
class ChapterWithHighlights(Chapter):
    """Chapter with its highlights"""
    highlights: List[Highlight]


@dataclass
class BookDetails(Book):
    """Book with all its chapters and highlights"""
    chapters: List[ChapterWithHighlights]


@dataclass
class BooksListResponse:
    """Response from the books list API endpoint"""
    books: List[BookWithHighlightCount]
    total: int
    offset: int
    limit: int


@dataclass
class ImportedHighlight:
    """Tracks a highlight that has been imported to Anki"""
    highlight_id: int  # Crossbill highlight ID
    note_id: int       # Anki note ID
    imported_at: str   # ISO 8601 timestamp


@dataclass
class PluginConfig:
    """Plugin configuration settings"""
    server_host: str
    default_deck: str
    default_note_type: str
    auto_tag: bool
    tag_prefix: str
    suspend_on_import: bool
    last_sync: Optional[str]
    ui_preferences: dict

    @classmethod
    def from_dict(cls, data: dict) -> 'PluginConfig':
        """Create PluginConfig from dictionary"""
        return cls(
            server_host=data.get('server_host', 'http://localhost:8000'),
            default_deck=data.get('default_deck', 'Default'),
            default_note_type=data.get('default_note_type', 'Basic'),
            auto_tag=data.get('auto_tag', True),
            tag_prefix=data.get('tag_prefix', 'crossbill'),
            suspend_on_import=data.get('suspend_on_import', True),
            last_sync=data.get('last_sync'),
            ui_preferences=data.get('ui_preferences', {
                'dialog_width': 900,
                'dialog_height': 600,
                'last_selected_book': None
            })
        )

    def to_dict(self) -> dict:
        """Convert PluginConfig to dictionary"""
        return {
            'server_host': self.server_host,
            'default_deck': self.default_deck,
            'default_note_type': self.default_note_type,
            'auto_tag': self.auto_tag,
            'tag_prefix': self.tag_prefix,
            'suspend_on_import': self.suspend_on_import,
            'last_sync': self.last_sync,
            'ui_preferences': self.ui_preferences
        }
