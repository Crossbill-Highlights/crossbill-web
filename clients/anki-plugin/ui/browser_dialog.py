"""
Highlights browser dialog for browsing and selecting Crossbill highlights
"""

import sys
import os
from typing import List, Optional

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton,
    QLabel, QMessageBox, QProgressDialog, Qt
)
from aqt.utils import showInfo

# Add plugin directory to path to import our modules
plugin_dir = os.path.dirname(os.path.dirname(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from api import CrossbillAPI, CrossbillAPIError
from models import BookWithHighlightCount, BookDetails, Highlight


class HighlightsBrowserDialog(QDialog):
    """Dialog for browsing and selecting highlights from Crossbill"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or mw.addonManager.getConfig(__name__.split('.')[0])
        self.api = CrossbillAPI(self.config.get('server_host', 'http://localhost:8000'))

        self.books: List[BookWithHighlightCount] = []
        self.current_book: Optional[BookDetails] = None
        self.all_highlights: List[Highlight] = []

        self.setup_ui()
        self.load_books()

    def setup_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Crossbill Highlights Browser")

        # Get dialog size from config
        width = self.config.get('ui_preferences', {}).get('dialog_width', 900)
        height = self.config.get('ui_preferences', {}).get('dialog_height', 700)
        self.resize(width, height)

        layout = QVBoxLayout()

        # Header
        header_label = QLabel("<h2>Browse Crossbill Highlights</h2>")
        layout.addWidget(header_label)

        # Main content area with vertical splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Books section - full width
        books_container = QLabel()  # Container widget for layout
        books_layout = QVBoxLayout()
        books_layout.setContentsMargins(0, 0, 0, 0)

        books_label = QLabel("<b>Books</b>")
        books_layout.addWidget(books_label)

        self.books_list = QListWidget()
        self.books_list.itemClicked.connect(self.on_book_selected)
        books_layout.addWidget(self.books_list)

        books_container.setLayout(books_layout)
        splitter.addWidget(books_container)

        # Highlights section - full width
        highlights_container = QLabel()  # Container widget for layout
        highlights_layout = QVBoxLayout()
        highlights_layout.setContentsMargins(0, 0, 0, 0)

        highlights_label = QLabel("<b>Highlights</b>")
        highlights_layout.addWidget(highlights_label)

        self.highlights_list = QListWidget()
        self.highlights_list.itemClicked.connect(self.on_highlight_selected)
        highlights_layout.addWidget(self.highlights_list)

        highlights_container.setLayout(highlights_layout)
        splitter.addWidget(highlights_container)

        # Details section - full width
        details_container = QLabel()  # Container widget for layout
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("<b>Details</b>")
        details_layout.addWidget(details_label)

        self.highlight_details = QTextEdit()
        self.highlight_details.setReadOnly(True)
        details_layout.addWidget(self.highlight_details)

        details_container.setLayout(details_layout)
        splitter.addWidget(details_container)

        # Set initial splitter proportions (books: highlights: details = 2:3:2)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 2)

        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_books)
        button_layout.addWidget(refresh_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_books(self):
        """Load books from Crossbill server"""
        self.status_label.setText("Loading books...")
        self.books_list.clear()

        try:
            response = self.api.get_books(limit=1000)
            self.books = response.books

            if not self.books:
                self.status_label.setText("No books found")
                QMessageBox.information(
                    self,
                    "No Books",
                    "No books with highlights found on your Crossbill server."
                )
                return

            # Populate books list
            for book in self.books:
                author_text = f" by {book.author}" if book.author else ""
                item_text = f"{book.title}{author_text} ({book.highlight_count} highlights)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, book.id)
                self.books_list.addItem(item)

            self.status_label.setText(f"Loaded {len(self.books)} books")

            # Select last selected book if available
            last_selected = self.config.get('ui_preferences', {}).get('last_selected_book')
            if last_selected:
                for i in range(self.books_list.count()):
                    item = self.books_list.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == last_selected:
                        self.books_list.setCurrentItem(item)
                        self.on_book_selected(item)
                        break

        except CrossbillAPIError as e:
            self.status_label.setText("Error loading books")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load books from Crossbill server:\n{str(e)}"
            )

    def on_book_selected(self, item: QListWidgetItem):
        """Handle book selection"""
        book_id = item.data(Qt.ItemDataRole.UserRole)
        self.status_label.setText(f"Loading highlights for book {book_id}...")

        try:
            self.current_book = self.api.get_book_details(book_id)

            # Save last selected book
            self.config['ui_preferences']['last_selected_book'] = book_id
            mw.addonManager.writeConfig(__name__.split('.')[0], self.config)

            # Collect all highlights from all chapters
            self.all_highlights = []
            for chapter in self.current_book.chapters:
                self.all_highlights.extend(chapter.highlights)

            # Populate highlights list
            self.highlights_list.clear()
            for highlight in self.all_highlights:
                # Create preview text (first 100 chars)
                preview = highlight.text[:100]
                if len(highlight.text) > 100:
                    preview += "..."

                chapter_text = f" [{highlight.chapter}]" if highlight.chapter else ""
                page_text = f" (p. {highlight.page})" if highlight.page else ""

                item_text = f"{preview}{chapter_text}{page_text}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, highlight.id)
                self.highlights_list.addItem(item)

            count = len(self.all_highlights)
            self.status_label.setText(f"Loaded {count} highlights from {self.current_book.title}")

        except CrossbillAPIError as e:
            self.status_label.setText("Error loading highlights")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load book details:\n{str(e)}"
            )

    def on_highlight_selected(self, item: QListWidgetItem):
        """Handle highlight selection"""
        highlight_id = item.data(Qt.ItemDataRole.UserRole)

        # Find the highlight
        highlight = None
        for hl in self.all_highlights:
            if hl.id == highlight_id:
                highlight = hl
                break

        if not highlight:
            return

        # Display highlight details
        details_html = f"<h3>Highlight</h3>"
        details_html += f"<p><i>{highlight.text}</i></p>"

        if highlight.note:
            details_html += f"<h4>Your Note</h4>"
            details_html += f"<p>{highlight.note}</p>"

        details_html += f"<h4>Source</h4>"
        details_html += f"<p><b>Book:</b> {self.current_book.title}</p>"

        if self.current_book.author:
            details_html += f"<p><b>Author:</b> {self.current_book.author}</p>"

        if highlight.chapter:
            details_html += f"<p><b>Chapter:</b> {highlight.chapter}</p>"

        if highlight.page:
            details_html += f"<p><b>Page:</b> {highlight.page}</p>"

        if highlight.highlight_tags:
            tags = ", ".join([tag.name for tag in highlight.highlight_tags])
            details_html += f"<p><b>Tags:</b> {tags}</p>"

        self.highlight_details.setHtml(details_html)

    def closeEvent(self, event):
        """Save dialog size when closing"""
        self.config['ui_preferences']['dialog_width'] = self.width()
        self.config['ui_preferences']['dialog_height'] = self.height()
        mw.addonManager.writeConfig(__name__.split('.')[0], self.config)
        event.accept()
