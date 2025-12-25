"""
Flashcards browser dialog for browsing and selecting Crossbill flashcards
"""

import sys
import os
from typing import List, Optional

from aqt import mw
from aqt.qt import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFormLayout,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton, QComboBox, QCheckBox, QLineEdit,
    QLabel, QMessageBox, QProgressDialog, Qt
)
from aqt.utils import showInfo, tooltip

# Add plugin directory to path to import our modules
plugin_dir = os.path.dirname(os.path.dirname(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from api import CrossbillAPI, CrossbillAPIError
from models import BookWithHighlightCount, FlashcardWithHighlight, PluginConfig
from note_creator import NoteCreator


class FlashcardsBrowserDialog(QWidget):
    """Window for browsing and selecting flashcards from Crossbill"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        # Set window flag to make it a proper window (not floating dialog)
        self.setWindowFlags(Qt.WindowType.Window)
        self.config = config or mw.addonManager.getConfig(__name__.split('.')[0])
        self.plugin_config = PluginConfig.from_dict(self.config)

        # Initialize API with authentication credentials
        self.api = CrossbillAPI(
            self.config.get('server_host', 'http://localhost:8000'),
            bearer_token=self.config.get('bearer_token', ''),
            email=self.config.get('email', ''),
            password=self.config.get('password', '')
        )

        # Set up callback to save bearer token when it's updated
        def save_token(token: str):
            self.config['bearer_token'] = token
            mw.addonManager.writeConfig(__name__.split('.')[0], self.config)

        self.api.set_on_token_update(save_token)
        self.note_creator = NoteCreator(self.plugin_config)

        self.books: List[BookWithHighlightCount] = []
        self.current_book_id: Optional[int] = None
        self.current_book_title: str = ""
        self.current_book_author: Optional[str] = None
        self.all_flashcards: List[FlashcardWithHighlight] = []
        self.imported_flashcard_ids = set()

        self.setup_ui()
        self.load_imported_flashcards()
        self.load_books()

    def setup_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Crossbill Flashcards Browser")

        # Get dialog size from config
        width = self.config.get('ui_preferences', {}).get('dialog_width', 900)
        height = self.config.get('ui_preferences', {}).get('dialog_height', 700)
        self.resize(width, height)

        layout = QVBoxLayout()

        # Header
        header_label = QLabel("<h2>Browse Crossbill Flashcards</h2>")
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

        # Flashcards section - full width
        flashcards_container = QLabel()  # Container widget for layout
        flashcards_layout = QVBoxLayout()
        flashcards_layout.setContentsMargins(0, 0, 0, 0)

        # Flashcards header with controls
        flashcards_header = QHBoxLayout()
        flashcards_label = QLabel("<b>Flashcards</b>")
        flashcards_header.addWidget(flashcards_label)
        flashcards_header.addStretch()

        # Selection buttons
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_flashcards)
        flashcards_header.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self.deselect_all_flashcards)
        flashcards_header.addWidget(deselect_all_btn)

        flashcards_layout.addLayout(flashcards_header)

        # Search and filter controls
        filter_layout = QHBoxLayout()

        # Search box
        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search flashcard questions...")
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

        flashcards_layout.addLayout(filter_layout)

        # Flashcards list with checkboxes
        self.flashcards_list = QListWidget()
        self.flashcards_list.itemClicked.connect(self.on_flashcard_clicked)
        self.flashcards_list.itemChanged.connect(self.update_import_button_states)
        flashcards_layout.addWidget(self.flashcards_list)

        flashcards_container.setLayout(flashcards_layout)
        splitter.addWidget(flashcards_container)

        # Details section - full width
        details_container = QLabel()  # Container widget for layout
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("<b>Details</b>")
        details_layout.addWidget(details_label)

        self.flashcard_details = QTextEdit()
        self.flashcard_details.setReadOnly(True)
        details_layout.addWidget(self.flashcard_details)

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

        # Import controls at bottom
        import_controls = QFormLayout()

        # Deck selection
        self.deck_combo = QComboBox()
        self.populate_decks()
        import_controls.addRow("Deck:", self.deck_combo)

        # Note type selection
        self.note_type_combo = QComboBox()
        self.populate_note_types()
        import_controls.addRow("Note Type:", self.note_type_combo)

        layout.addLayout(import_controls)

        # Import buttons at bottom
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

        self.import_btn = QPushButton("Import Selected")
        self.import_btn.clicked.connect(self.import_selected_flashcards)
        self.import_btn.setEnabled(False)
        import_button_layout.addWidget(self.import_btn)

        import_button_layout.addStretch()

        # Refresh and Close buttons
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_books)
        import_button_layout.addWidget(refresh_button)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        import_button_layout.addWidget(close_button)

        layout.addLayout(import_button_layout)

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
                    "No books with flashcards found on your Crossbill server."
                )
                return

            # Populate books list - show flashcard count
            for book in self.books:
                author_text = f" by {book.author}" if book.author else ""
                item_text = f"{book.title}{author_text} ({book.flashcard_count} flashcards)"
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
        self.status_label.setText(f"Loading flashcards for book {book_id}...")

        try:
            # Find book info from our cached books list
            book_info = next((b for b in self.books if b.id == book_id), None)
            if book_info:
                self.current_book_id = book_id
                self.current_book_title = book_info.title
                self.current_book_author = book_info.author

            # Fetch flashcards for this book
            response = self.api.get_flashcards(book_id)
            self.all_flashcards = response.flashcards

            # Save last selected book
            self.config['ui_preferences']['last_selected_book'] = book_id
            mw.addonManager.writeConfig(__name__.split('.')[0], self.config)

            # Populate tag and chapter filters (from flashcard highlights)
            self.populate_tag_filter()
            self.populate_chapter_filter()

            # Clear search and filters
            self.search_input.clear()

            # Populate flashcards list with checkboxes and import status
            self.refresh_flashcards_list()

            # Update import button states based on current selections
            self.update_import_button_states()

            count = len(self.all_flashcards)
            self.status_label.setText(f"Loaded {count} flashcards from {self.current_book_title}")

        except CrossbillAPIError as e:
            self.status_label.setText("Error loading flashcards")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load flashcards:\n{str(e)}"
            )

    def on_flashcard_selected(self, item: QListWidgetItem):
        """Handle flashcard selection"""
        flashcard_id = item.data(Qt.ItemDataRole.UserRole)

        # Find the flashcard
        flashcard = next((fc for fc in self.all_flashcards if fc.id == flashcard_id), None)
        if not flashcard:
            return

        # Display flashcard details
        details_html = f"<h3>Question</h3>"
        details_html += f"<p>{flashcard.question}</p>"

        details_html += f"<h3>Answer</h3>"
        details_html += f"<p>{flashcard.answer}</p>"

        if flashcard.highlight:
            details_html += f"<h4>Source Highlight</h4>"
            details_html += f"<p><i>{flashcard.highlight.text}</i></p>"

            if flashcard.highlight.chapter:
                details_html += f"<p><b>Chapter:</b> {flashcard.highlight.chapter}</p>"

            if flashcard.highlight.page:
                details_html += f"<p><b>Page:</b> {flashcard.highlight.page}</p>"

            if flashcard.highlight.highlight_tags:
                tags = ", ".join([tag.name for tag in flashcard.highlight.highlight_tags])
                details_html += f"<p><b>Tags:</b> {tags}</p>"
        else:
            details_html += "<p><i>(Standalone flashcard - no associated highlight)</i></p>"

        self.flashcard_details.setHtml(details_html)

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

    def load_imported_flashcards(self):
        """Load the set of already imported flashcard IDs"""
        self.imported_flashcard_ids = self.note_creator.get_imported_flashcard_ids()

    def select_all_flashcards(self):
        """Select all flashcards in the list"""
        for i in range(self.flashcards_list.count()):
            item = self.flashcards_list.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Checked)
        self.update_import_button_states()

    def deselect_all_flashcards(self):
        """Deselect all flashcards in the list"""
        for i in range(self.flashcards_list.count()):
            item = self.flashcards_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.update_import_button_states()

    def on_flashcard_clicked(self, item: QListWidgetItem):
        """Handle flashcard click - show details"""
        self.on_flashcard_selected(item)

    def get_selected_flashcards(self) -> List[FlashcardWithHighlight]:
        """Get list of selected flashcards"""
        selected = []
        for i in range(self.flashcards_list.count()):
            item = self.flashcards_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                flashcard_id = item.data(Qt.ItemDataRole.UserRole)
                # Find the flashcard object
                for fc in self.all_flashcards:
                    if fc.id == flashcard_id:
                        selected.append(fc)
                        break
        return selected

    def import_selected_flashcards(self):
        """Import selected flashcards as Anki notes"""
        if not self.current_book_id:
            QMessageBox.warning(
                self,
                "No Book Selected",
                "Please select a book first."
            )
            return

        selected_flashcards = self.get_selected_flashcards()
        if not selected_flashcards:
            QMessageBox.warning(
                self,
                "No Flashcards Selected",
                "Please select at least one flashcard to import."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Confirm import
        count = len(selected_flashcards)
        reply = QMessageBox.question(
            self,
            "Confirm Import",
            f"Import {count} flashcard(s) to deck '{deck_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show progress dialog
        progress = QProgressDialog("Importing flashcards...", "Cancel", 0, count, self)
        progress.setWindowTitle("Import Progress")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Import flashcards
        stats = self.note_creator.import_flashcards(
            selected_flashcards,
            self.current_book_title,
            self.current_book_author,
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
            # Reload imported flashcards
            self.load_imported_flashcards()
            # Refresh the flashcards list to show import status
            if self.current_book_id:
                self.refresh_flashcards_list()
                self.update_import_button_states()
        else:
            QMessageBox.warning(self, "Import Results", result_msg)

    def refresh_flashcards_list(self):
        """Refresh the flashcards list to update import status and apply filters"""
        if not self.all_flashcards:
            return

        # Remember current selections
        selected_ids = set()
        for i in range(self.flashcards_list.count()):
            item = self.flashcards_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_ids.add(item.data(Qt.ItemDataRole.UserRole))

        # Get filter values
        search_text = self.search_input.text().lower()
        selected_tag = self.tag_filter_combo.currentData()
        selected_chapter = self.chapter_filter_combo.currentData()

        # Rebuild list with filtering
        self.flashcards_list.clear()
        displayed_count = 0

        for flashcard in self.all_flashcards:
            # Apply search filter to question and answer
            if search_text:
                if search_text not in flashcard.question.lower() and search_text not in flashcard.answer.lower():
                    continue

            # Apply tag filter (only works if flashcard has highlight with tags)
            if selected_tag:
                if not flashcard.highlight:
                    continue
                tag_names = [tag.name for tag in flashcard.highlight.highlight_tags]
                if selected_tag not in tag_names:
                    continue

            # Apply chapter filter (only works if flashcard has highlight with chapter)
            if selected_chapter:
                if not flashcard.highlight or flashcard.highlight.chapter_id != selected_chapter:
                    continue

            displayed_count += 1
            # Create preview text (first 100 chars of question)
            preview = flashcard.question[:100]
            if len(flashcard.question) > 100:
                preview += "..."

            # Show chapter/page from highlight if available
            chapter_text = ""
            page_text = ""
            if flashcard.highlight:
                if flashcard.highlight.chapter:
                    chapter_text = f" [{flashcard.highlight.chapter}]"
                if flashcard.highlight.page:
                    page_text = f" (p. {flashcard.highlight.page})"

            # Add import status
            is_imported = flashcard.id in self.imported_flashcard_ids
            status_text = " ✓ Imported" if is_imported else ""

            item_text = f"{preview}{chapter_text}{page_text}{status_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, flashcard.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)

            # Restore selection state
            if flashcard.id in selected_ids:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

            # Gray out imported flashcards
            if is_imported:
                item.setForeground(Qt.GlobalColor.gray)

            self.flashcards_list.addItem(item)

        # Update status with filter info
        if displayed_count < len(self.all_flashcards):
            self.status_label.setText(
                f"Showing {displayed_count} of {len(self.all_flashcards)} flashcards (filtered)"
            )
        elif self.current_book_id:
            self.status_label.setText(
                f"Showing {displayed_count} flashcards from {self.current_book_title}"
            )

    def populate_tag_filter(self):
        """Populate the tag filter dropdown with all unique tags from flashcard highlights"""
        # Clear existing items except "All Tags"
        self.tag_filter_combo.clear()
        self.tag_filter_combo.addItem("All Tags", None)

        if not self.all_flashcards:
            return

        # Collect all unique tags from flashcard highlights
        tags = set()
        for flashcard in self.all_flashcards:
            if flashcard.highlight:
                for tag in flashcard.highlight.highlight_tags:
                    tags.add(tag.name)

        # Add tags to dropdown
        for tag in sorted(tags):
            self.tag_filter_combo.addItem(tag, tag)

    def populate_chapter_filter(self):
        """Populate the chapter filter dropdown with all unique chapters from flashcard highlights"""
        # Clear existing items except "All Chapters"
        self.chapter_filter_combo.clear()
        self.chapter_filter_combo.addItem("All Chapters", None)

        if not self.all_flashcards:
            return

        # Collect unique chapters from flashcard highlights
        chapters = {}  # chapter_id -> chapter_name
        for flashcard in self.all_flashcards:
            if flashcard.highlight and flashcard.highlight.chapter_id:
                chapters[flashcard.highlight.chapter_id] = flashcard.highlight.chapter

        # Add chapters to dropdown
        for chapter_id, chapter_name in sorted(chapters.items(), key=lambda x: x[1] or ""):
            if chapter_name:
                self.chapter_filter_combo.addItem(chapter_name, chapter_id)

    def on_search_changed(self, text):
        """Handle search text change"""
        self.refresh_flashcards_list()

    def on_filter_changed(self, index):
        """Handle filter dropdown change"""
        self.refresh_flashcards_list()
        self.update_import_button_states()

    def update_import_button_states(self):
        """Update the enabled/disabled state of import buttons based on current state"""
        # Import All from Book: enabled if book is selected
        has_book = self.current_book_id is not None and len(self.all_flashcards) > 0
        self.import_all_btn.setEnabled(has_book)

        # Import All from Chapter: enabled if book is selected AND a specific chapter is selected
        has_chapter = has_book and self.chapter_filter_combo.currentData() is not None
        self.import_chapter_btn.setEnabled(has_chapter)

        # Import Selected: enabled if book is selected AND at least one flashcard is checked
        has_selected = False
        if has_book:
            for i in range(self.flashcards_list.count()):
                item = self.flashcards_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    has_selected = True
                    break
        self.import_btn.setEnabled(has_selected)

    def clear_filters(self):
        """Clear all filters and search"""
        self.search_input.clear()
        self.tag_filter_combo.setCurrentIndex(0)  # "All Tags"
        self.chapter_filter_combo.setCurrentIndex(0)  # "All Chapters"
        self.refresh_flashcards_list()

    def import_all_from_book(self):
        """Import all flashcards from the current book"""
        if not self.current_book_id or not self.all_flashcards:
            QMessageBox.warning(
                self,
                "No Book Selected",
                "Please select a book first."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Count flashcards that haven't been imported yet
        new_flashcards = [fc for fc in self.all_flashcards
                         if fc.id not in self.imported_flashcard_ids]
        total_count = len(self.all_flashcards)
        new_count = len(new_flashcards)

        # Confirm import
        if new_count == 0:
            QMessageBox.information(
                self,
                "All Imported",
                f"All {total_count} flashcards from this book have already been imported."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Import",
            f"Import all {total_count} flashcards from '{self.current_book_title}'?\n"
            f"({new_count} new, {total_count - new_count} already imported)\n\n"
            f"Deck: {deck_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Import all flashcards
        self._do_batch_import(self.all_flashcards, deck_name, note_type_name)

    def import_all_from_chapter(self):
        """Import all flashcards from the currently filtered chapter"""
        if not self.current_book_id or not self.all_flashcards:
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

        # Filter flashcards by chapter ID (from their associated highlights)
        chapter_flashcards = [fc for fc in self.all_flashcards
                            if fc.highlight and fc.highlight.chapter_id == selected_chapter_id]

        if not chapter_flashcards:
            QMessageBox.warning(
                self,
                "No Flashcards",
                f"No flashcards found in chapter '{selected_chapter_name}'."
            )
            return

        # Get selected deck and note type
        deck_name = self.deck_combo.currentText()
        note_type_name = self.note_type_combo.currentText()

        # Count new flashcards
        new_flashcards = [fc for fc in chapter_flashcards
                         if fc.id not in self.imported_flashcard_ids]
        total_count = len(chapter_flashcards)
        new_count = len(new_flashcards)

        # Confirm import
        if new_count == 0:
            QMessageBox.information(
                self,
                "All Imported",
                f"All {total_count} flashcards from chapter '{selected_chapter_name}' "
                f"have already been imported."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Import",
            f"Import all {total_count} flashcards from chapter '{selected_chapter_name}'?\n"
            f"({new_count} new, {total_count - new_count} already imported)\n\n"
            f"Deck: {deck_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Import chapter flashcards
        self._do_batch_import(chapter_flashcards, deck_name, note_type_name)

    def _do_batch_import(self, flashcards: List[FlashcardWithHighlight], deck_name: str, note_type_name: str):
        """Execute batch import of flashcards"""
        count = len(flashcards)

        # Show progress dialog
        progress = QProgressDialog("Importing flashcards...", "Cancel", 0, count, self)
        progress.setWindowTitle("Batch Import")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        # Import flashcards
        stats = self.note_creator.import_flashcards(
            flashcards,
            self.current_book_title,
            self.current_book_author,
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
            # Reload imported flashcards
            self.load_imported_flashcards()
            # Refresh the flashcards list
            self.refresh_flashcards_list()
            self.update_import_button_states()
        else:
            QMessageBox.warning(self, "Batch Import Results", result_msg)

    def closeEvent(self, event):
        """Save dialog size when closing"""
        self.config['ui_preferences']['dialog_width'] = self.width()
        self.config['ui_preferences']['dialog_height'] = self.height()
        mw.addonManager.writeConfig(__name__.split('.')[0], self.config)
        event.accept()
