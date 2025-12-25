"""
Settings dialog for Crossbill plugin configuration
"""

from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox, QCheckBox
)
from aqt.utils import showInfo


class SettingsDialog(QDialog):
    """Dialog for configuring Crossbill plugin settings"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = mw.addonManager.getConfig(__name__.split('.')[0])
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Crossbill Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Form layout for settings
        form_layout = QFormLayout()

        # Server host
        self.server_host_input = QLineEdit()
        self.server_host_input.setText(self.config.get('server_host', 'http://localhost:8000'))
        self.server_host_input.setPlaceholderText("e.g., http://localhost:8000")
        form_layout.addRow("Server URL:", self.server_host_input)

        # Authentication section label
        auth_label = QLabel("<b>Authentication</b>")
        form_layout.addRow("", auth_label)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setText(self.config.get('email', ''))
        self.email_input.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.email_input)

        # Password
        self.password_input = QLineEdit()
        self.password_input.setText(self.config.get('password', ''))
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)

        # Add spacing
        spacer_label = QLabel("")
        form_layout.addRow("", spacer_label)

        # Default deck
        self.default_deck_input = QLineEdit()
        self.default_deck_input.setText(self.config.get('default_deck', 'Default'))
        self.default_deck_input.setPlaceholderText("e.g., Default")
        form_layout.addRow("Default Deck:", self.default_deck_input)

        # Default note type
        self.default_note_type_input = QLineEdit()
        self.default_note_type_input.setText(self.config.get('default_note_type', 'Basic'))
        self.default_note_type_input.setPlaceholderText("e.g., Basic")
        form_layout.addRow("Default Note Type:", self.default_note_type_input)

        # Suspend on import
        self.suspend_on_import_checkbox = QCheckBox()
        self.suspend_on_import_checkbox.setChecked(self.config.get('suspend_on_import', True))
        form_layout.addRow("Suspend cards on import:", self.suspend_on_import_checkbox)

        layout.addLayout(form_layout)

        # Help text
        help_label = QLabel(
            "<small>Configure your Crossbill server connection. "
            "Make sure the server URL is accessible from this computer.<br><br>"
            "<b>Authentication:</b> Enter your credentials. Authentication happens automatically "
            "when you use the plugin.<br><br>"
            "<b>Suspend on import:</b> When enabled, imported cards will be suspended "
            "(not appear in reviews) until you manually unsuspend them. "
            "This allows you to review and edit cards before studying them.</small>"
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Buttons
        button_layout = QHBoxLayout()

        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(test_button)

        button_layout.addStretch()

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        save_button.setDefault(True)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def test_connection(self):
        """Test connection to Crossbill server"""
        server_host = self.server_host_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not server_host:
            QMessageBox.warning(self, "Error", "Please enter a server URL")
            return

        if not email or not password:
            QMessageBox.warning(self, "Error", "Please enter email and password to test connection")
            return

        try:
            # Import API client
            import sys
            import os

            # Add plugin directory to path to import api module
            plugin_dir = os.path.dirname(os.path.dirname(__file__))
            if plugin_dir not in sys.path:
                sys.path.insert(0, plugin_dir)

            from api import CrossbillAPI

            api = CrossbillAPI(server_host, email=email, password=password)
            success, message = api.test_connection()
            if success:
                QMessageBox.information(
                    self,
                    "Success",
                    "Successfully connected and authenticated with Crossbill server!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Failed",
                    f"Could not connect to Crossbill server:\n\n{message}"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to connect to server:\n{str(e)}"
            )

    def save_settings(self):
        """Save settings to config"""
        server_host = self.server_host_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        default_deck = self.default_deck_input.text().strip()
        default_note_type = self.default_note_type_input.text().strip()
        suspend_on_import = self.suspend_on_import_checkbox.isChecked()

        if not server_host:
            QMessageBox.warning(self, "Error", "Server URL is required")
            return

        if not default_deck:
            default_deck = "Default"

        if not default_note_type:
            default_note_type = "Basic"

        # Update config
        self.config['server_host'] = server_host
        self.config['email'] = email
        self.config['password'] = password
        # Keep existing bearer_token if present
        if 'bearer_token' not in self.config:
            self.config['bearer_token'] = ''
        self.config['default_deck'] = default_deck
        self.config['default_note_type'] = default_note_type
        self.config['suspend_on_import'] = suspend_on_import

        # Save config
        mw.addonManager.writeConfig(__name__.split('.')[0], self.config)

        self.accept()


def show_settings_dialog():
    """Show the settings dialog"""
    dialog = SettingsDialog(mw)
    dialog.exec()
