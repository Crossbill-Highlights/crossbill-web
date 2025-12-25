"""
Crossbill Anki Plugin

Import flashcards from Crossbill server into Anki.
"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo, qconnect

# Plugin metadata
__version__ = "0.4.0"
__author__ = "Crossbill Contributors"


def show_flashcards_browser():
    """Show the flashcards browser window"""
    # Import here to avoid circular dependencies and load UI only when needed
    from .ui.browser_dialog import FlashcardsBrowserDialog

    config = mw.addonManager.getConfig(__name__)
    if not config:
        showInfo("Failed to load plugin configuration. Please reinstall the plugin.")
        return

    # Show the browser window (non-modal for better tiling WM support)
    # If connection fails, the window will show appropriate error messages
    window = FlashcardsBrowserDialog(mw, config)
    window.show()


def show_settings():
    """Show the settings dialog"""
    from .ui.settings_dialog import show_settings_dialog
    show_settings_dialog()


def init_plugin():
    """Initialize the plugin and register menu actions"""
    # Create menu action for browsing flashcards
    action_browse = QAction("Browse Crossbill Flashcards", mw)
    qconnect(action_browse.triggered, show_flashcards_browser)
    mw.form.menuTools.addAction(action_browse)

    # Create menu action for settings
    action_settings = QAction("Crossbill Settings", mw)
    qconnect(action_settings.triggered, show_settings)
    mw.form.menuTools.addAction(action_settings)


# Initialize plugin when Anki loads
init_plugin()
