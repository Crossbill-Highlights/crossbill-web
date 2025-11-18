"""
Highlights browser dialog for browsing and selecting Crossbill highlights
"""

import sys
import os
from typing import List, Optional

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QFormLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QComboBox, QCheckBox, QLineEdit,
    QLabel, QMessageBox, QProgressDialog, Qt
)
from aqt.utils import showInfo, tooltip

# Add plugin directory to path to import our modules
plugin_dir = os.path.dirname(os.path.dirname(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from api import CrossbillAPI, CrossbillAPIError
from models import BookWithHighlightCount, BookDetails, Highlight, PluginConfig
from note_creator import NoteCreator


class HighlightsBrowserDialog(QDialog):
    """Dialog for browsing and selecting highlights from Crossbill"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or mw.addonManager.getConfig(__name__.split('.')[0])
        self.plugin_config = PluginConfig.from_dict(self.config)
        self.api = CrossbillAPI(self.config.get('server_host', 'http://localhost:8000'))
        self.note_creator = NoteCreator(self.plugin_config)

        self.books: List[BookWithHighlightCount] = []
        self.current_book: Optional[BookDetails] = None
        self.all_highlights: List[Highlight] = []
        self.imported_highlight_ids = set()

        self.setup_ui()
        self.load_imported_highlights()
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

        # Highlights header with controls
        highlights_header = QHBoxLayout()
        highlights_label = QLabel("<b>Highlights</b>")
        highlights_header.addWidget(highlights_label)
        highlights_header.addStretch()

        # Selection buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_highlights)
        highlights_header.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_highlights)
        highlights_header.addWidget(deselect_all_btn)

        highlights_layout.addLayout(highlights_header)

        # Search and filter controls
        filter_layout = QHBoxLayout()

        # Search box
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search highlight text...")
        self.search_input.textChanged.connect(self.on_search_changed)
        filter_layout.addWidget(self.search_input)

        # Tag filter
        filter_layout.addWidget(QLabel("Tag:"))
        self.tag_filter_combo = QComboBox()
        self.tag_filter_combo.addItem("All Tags", None)
        self.tag_filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.tag_filter_combo)

        # Chapter filter
        filter_layout.addWidget(QLabel("Chapter:"))
        self.chapter_filter_combo = QComboBox()
        self.chapter_filter_combo.addItem("All Chapters", None)
        self.chapter_filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.chapter_filter_combo)

        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)

        highlights_layout.addLayout(filter_layout)

        # Highlights list with checkboxes
        self.highlights_list = QListWidget()
        self.highlights_list.itemClicked.connect(self.on_highlight_clicked)
        highlights_layout.addWidget(self.highlights_list)

        # Import controls
        import_controls = QFormLayout()

        # Deck selection
        self.deck_combo = QComboBox()
        self.populate_decks()
        import_controls.addRow("Deck:", self.deck_combo)

        # Note type selection
        self.note_type_combo = QComboBox()
        self.populate_note_types()
        import_controls.addRow("Note Type:", self.note_type_combo)

        highlights_layout.addLayout(import_controls)

        # Import buttons
        import_button_layout = QHBoxLayout()

        # Batch import buttons
        self.import_all_btn = QPushButton("Import All from Book")
        self.import_all_btn.clicked.connect(self.import_all_from_book)
        self.import_all_btn.setEnabled(False)
        import_button_layout.addWidget(self.import_all_btn)

        self.import_chapter_btn = QPushButton("Import All from Chapter")
        self.import_chapter_btn.clicked.connect(self.import_all_from_chapter)
        self.import_chapter_btn.setEnabled(False)
        import_button_layout.addWidget(self.import_chapter_btn)

        import_button_layout.addStretch()

        # Selected import button
        self.import_btn = QPushButton("Import Selected")
        self.import_btn.clicked.connect(self.import_selected_highlights)
        self.import_btn.setEnabled(False)  # Disabled until book is selected
        import_button_layout.addWidget(self.import_btn)

        highlights_layout.addLayout(import_button_layout)

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

            # Populate tag and chapter filters
            self.populate_tag_filter()
            self.populate_chapter_filter()

            # Clear search and filters
            self.search_input.clear()

            # Populate highlights list with checkboxes and import status
            self.refresh_highlights_list()

            # Enable import buttons
            self.import_btn.setEnabled(True)
            self.import_all_btn.setEnabled(True)
            self.import_chapter_btn.setEnabled(True)

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

    def populate_decks(self):
        """Populate the deck selection dropdown"""
        deck_names = sorted(mw.col.decks.all_names())
        self.deck_combo.addItems(deck_names)

        # Set default deck from config
        default_deck = self.config.get('default_deck', 'Default')
        index = self.deck_combo.findText(default_deck)
        if index >= 0:
            self.deck_combo.setCurrentIndex(index)

    def populate_note_types(self):
        """Populate the note type selection dropdown"""
        model_names = sorted(mw.col.models.all_names())
        self.note_type_combo.addItems(model_names)

        # Set default note type from config
        default_note_type = self.config.get('default_note_type', 'Basic')
        index = self.note_type_combo.findText(default_note_type)
        if index >= 0:
            self.note_type_combo.setCurrentIndex(index)

    def load_imported_highlights(self):
        """Load the set of already imported highlight IDs"""
        self.imported_highlight_ids = self.note_creator.get_imported_highlight_ids()

    def select_all_highlights(self):
        """Select all highlights in the list"""
        for i in range(self.highlights_list.count()):
            item = self.highlights_list.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Checked)

    def deselect_all_highlights(self):
        """Deselect all highlights in the list"""
        for i in range(self.highlights_list.count()):
            item = self.highlights_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)

    def on_highlight_clicked(self, item: QListWidgetItem):
        """Handle highlight click - show details"""
        self.on_highlight_selected(item)

    def get_selected_highlights(self) -> List[Highlight]:
        """Get list of selected highlights"""
        selected = []
        for i in range(self.highlights_list.count()):
            item = self.highlights_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                highlight_id = item.data(Qt.ItemDataRole.UserRole)
                # Find the highlight object
                for hl in self.all_highlights:
                    if hl.id == highlight_id:
                        selected.append(hl)
                        break
        return selected

    def import_selected_highlights(self):
        """Import selected highlights as Anki notes"""
        if not self.current_book:
            QMessageBox.warning(
                self,
                "No Book Selected",
                "Please select a book first."
            )
            return

        selected_highlights = self.get_selected_highlights()
        if not selected_highlights:
            QMessageBox.warning(
                self,
                "No Highlights Selected",
                "Please select at least one highlight to import."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Confirm import
        count = len(selected_highlights)
        reply = QMessageBox.question(
            self,
            "Confirm Import",
            f"Import {count} highlight(s) to deck '{deck_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show progress dialog
        progress = QProgressDialog("Importing highlights...", "Cancel", 0, count, self)
        progress.setWindowTitle("Import Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Import highlights
        stats = self.note_creator.import_highlights(
            selected_highlights,
            self.current_book,
            deck_name,
            note_type_name,
            skip_duplicates=True
        )

        progress.close()

        # Show results
        result_msg = f"Import complete!\n\n"
        result_msg += f"Created: {stats['created']} notes\n"
        if stats['skipped'] > 0:
            result_msg += f"Skipped (already imported): {stats['skipped']}\n"
        if stats['failed'] > 0:
            result_msg += f"Failed: {stats['failed']}\n"

        if stats['errors']:
            result_msg += f"\nErrors:\n"
            for error in stats['errors'][:5]:  # Show first 5 errors
                result_msg += f"- {error}\n"
            if len(stats['errors']) > 5:
                result_msg += f"... and {len(stats['errors']) - 5} more errors"

        if stats['created'] > 0:
            QMessageBox.information(self, "Import Successful", result_msg)
            # Reload imported highlights
            self.load_imported_highlights()
            # Refresh the highlights list to show import status
            if self.current_book:
                self.refresh_highlights_list()
        else:
            QMessageBox.warning(self, "Import Results", result_msg)

    def refresh_highlights_list(self):
        """Refresh the highlights list to update import status and apply filters"""
        if not self.all_highlights:
            return

        # Remember current selections
        selected_ids = set()
        for i in range(self.highlights_list.count()):
            item = self.highlights_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ids.add(item.data(Qt.ItemDataRole.UserRole))

        # Get filter values
        search_text = self.search_input.text().lower()
        selected_tag = self.tag_filter_combo.currentData()
        selected_chapter = self.chapter_filter_combo.currentData()

        # Rebuild list with filtering
        self.highlights_list.clear()
        displayed_count = 0

        for highlight in self.all_highlights:
            # Apply filters
            if search_text and search_text not in highlight.text.lower():
                if not highlight.note or search_text not in highlight.note.lower():
                    continue

            if selected_tag and selected_tag not in [tag.name for tag in highlight.highlight_tags]:
                continue

            if selected_chapter and highlight.chapter_id != selected_chapter:
                continue

            displayed_count += 1
            # Create preview text (first 100 chars)
            preview = highlight.text[:100]
            if len(highlight.text) > 100:
                preview += "..."

            chapter_text = f" [{highlight.chapter}]" if highlight.chapter else ""
            page_text = f" (p. {highlight.page})" if highlight.page else ""

            # Add import status
            is_imported = highlight.id in self.imported_highlight_ids
            status_text = " ✓ Imported" if is_imported else ""

            item_text = f"{preview}{chapter_text}{page_text}{status_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, highlight.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Restore selection state
            if highlight.id in selected_ids:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            # Gray out imported highlights
            if is_imported:
                item.setForeground(Qt.GlobalColor.gray)

            self.highlights_list.addItem(item)

        # Update status with filter info
        if displayed_count < len(self.all_highlights):
            self.status_label.setText(
                f"Showing {displayed_count} of {len(self.all_highlights)} highlights (filtered)"
            )
        elif self.current_book:
            self.status_label.setText(
                f"Showing {displayed_count} highlights from {self.current_book.title}"
            )

    def populate_tag_filter(self):
        """Populate the tag filter dropdown with all unique tags from current highlights"""
        # Clear existing items except "All Tags"
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Tags", None)

        if not self.all_highlights:
            return

        # Collect all unique tags
        tags = set()
        for highlight in self.all_highlights:
            for tag in highlight.highlight_tags:
                tags.add(tag.name)

        # Add tags to dropdown
        for tag in sorted(tags):
            self.tag_filter_combo.addItem(tag, tag)

    def populate_chapter_filter(self):
        """Populate the chapter filter dropdown with all unique chapters"""
        # Clear existing items except "All Chapters"
        self.chapter_filter_combo.clear()
        self.chapter_filter_combo.addItem("All Chapters", None)

        if not self.current_book:
            return

        # Add chapters to dropdown
        for chapter in self.current_book.chapters:
            if chapter.highlights:  # Only show chapters with highlights
                self.chapter_filter_combo.addItem(chapter.name, chapter.id)

    def on_search_changed(self, text):
        """Handle search text change"""
        self.refresh_highlights_list()

    def on_filter_changed(self, index):
        """Handle filter dropdown change"""
        self.refresh_highlights_list()

    def clear_filters(self):
        """Clear all filters and search"""
        self.search_input.clear()
        self.tag_filter_combo.setCurrentIndex(0)  # "All Tags"
        self.chapter_filter_combo.setCurrentIndex(0)  # "All Chapters"
        self.refresh_highlights_list()

    def import_all_from_book(self):
        """Import all highlights from the current book"""
        if not self.current_book or not self.all_highlights:
            QMessageBox.warning(
                self,
                "No Book Selected",
                "Please select a book first."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Count highlights that haven't been imported yet
        new_highlights = [hl for hl in self.all_highlights
                         if hl.id not in self.imported_highlight_ids]
        total_count = len(self.all_highlights)
        new_count = len(new_highlights)

        # Confirm import
        if new_count == 0:
            QMessageBox.information(
                self,
                "All Imported",
                f"All {total_count} highlights from this book have already been imported."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Import",
            f"Import all {total_count} highlights from '{self.current_book.title}'?\n"
            f"({new_count} new, {total_count - new_count} already imported)\n\n"
            f"Deck: {deck_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Import all highlights
        self._do_batch_import(self.all_highlights, deck_name, note_type_name)

    def import_all_from_chapter(self):
        """Import all highlights from the currently filtered chapter"""
        if not self.current_book or not self.all_highlights:
            QMessageBox.warning(
                self,
                "No Book Selected",
                "Please select a book first."
            )
            return

        # Get current chapter filter (chapter ID)
        selected_chapter_id = self.chapter_filter_combo.currentData()
        if not selected_chapter_id:
            QMessageBox.information(
                self,
                "No Chapter Selected",
                "Please select a chapter from the Chapter filter dropdown first."
            )
            return

        # Get chapter name for display
        selected_chapter_name = self.chapter_filter_combo.currentText()

        # Filter highlights by chapter ID
        chapter_highlights = [hl for hl in self.all_highlights
                            if hl.chapter_id == selected_chapter_id]

        if not chapter_highlights:
            QMessageBox.warning(
                self,
                "No Highlights",
                f"No highlights found in chapter '{selected_chapter_name}'."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Count new highlights
        new_highlights = [hl for hl in chapter_highlights
                         if hl.id not in self.imported_highlight_ids]
        total_count = len(chapter_highlights)
        new_count = len(new_highlights)

        # Confirm import
        if new_count == 0:
            QMessageBox.information(
                self,
                "All Imported",
                f"All {total_count} highlights from chapter '{selected_chapter_name}' "
                f"have already been imported."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Import",
            f"Import all {total_count} highlights from chapter '{selected_chapter_name}'?\n"
            f"({new_count} new, {total_count - new_count} already imported)\n\n"
            f"Deck: {deck_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Import chapter highlights
        self._do_batch_import(chapter_highlights, deck_name, note_type_name)

    def _do_batch_import(self, highlights: List[Highlight], deck_name: str, note_type_name: str):
        """Execute batch import of highlights"""
        count = len(highlights)

        # Show progress dialog
        progress = QProgressDialog("Importing highlights...", "Cancel", 0, count, self)
        progress.setWindowTitle("Batch Import")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Import highlights
        stats = self.note_creator.import_highlights(
            highlights,
            self.current_book,
            deck_name,
            note_type_name,
            skip_duplicates=True
        )

        progress.close()

        # Show results
        result_msg = f"Batch import complete!\n\n"
        result_msg += f"Created: {stats['created']} notes\n"
        if stats['skipped'] > 0:
            result_msg += f"Skipped (already imported): {stats['skipped']}\n"
        if stats['failed'] > 0:
            result_msg += f"Failed: {stats['failed']}\n"

        if stats['errors']:
            result_msg += f"\nErrors:\n"
            for error in stats['errors'][:5]:
                result_msg += f"- {error}\n"
            if len(stats['errors']) > 5:
                result_msg += f"... and {len(stats['errors']) - 5} more errors"

        if stats['created'] > 0:
            QMessageBox.information(self, "Batch Import Successful", result_msg)
            # Reload imported highlights
            self.load_imported_highlights()
            # Refresh the highlights list
            self.refresh_highlights_list()
        else:
            QMessageBox.warning(self, "Batch Import Results", result_msg)

    def closeEvent(self, event):
        """Save dialog size when closing"""
        self.config['ui_preferences']['dialog_width'] = self.width()
        self.config['ui_preferences']['dialog_height'] = self.height()
        mw.addonManager.writeConfig(__name__.split('.')[0], self.config)
        event.accept()
