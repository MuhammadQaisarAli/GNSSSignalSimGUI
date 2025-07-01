"""
Template Dialog for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This dialog allows users to load, save, and manage configuration templates.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QTextEdit,
    QLabel,
    QMessageBox,
    QSplitter,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.config.templates import template_manager
from core.utils.logger import info, debug, log_button_click


class TemplateDialog(QDialog):
    """Dialog for managing configuration templates."""

    template_selected = pyqtSignal(object)  # SignalSimConfig

    def __init__(self, parent=None, current_config=None):
        super().__init__(parent)
        self.current_config = current_config
        self.selected_template = None
        self.init_ui()
        self.refresh_template_list()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Configuration Templates")
        self.setGeometry(200, 200, 800, 600)

        layout = QVBoxLayout(self)

        # Create splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side: Template list
        self.setup_template_list()
        splitter.addWidget(self.template_list_widget)

        # Right side: Template details and actions
        self.setup_template_details()
        splitter.addWidget(self.details_widget)

        # Set splitter proportions (40% list, 60% details)
        splitter.setSizes([320, 480])

        # Bottom buttons
        self.setup_buttons()
        layout.addLayout(self.button_layout)

    def setup_template_list(self):
        """Set up the template list widget."""
        self.template_list_widget = QGroupBox("Available Templates")
        list_layout = QVBoxLayout(self.template_list_widget)

        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        list_layout.addWidget(self.template_list)

        # List action buttons
        list_buttons = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_template_list)
        list_buttons.addWidget(self.refresh_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_template)
        self.delete_button.setEnabled(False)
        list_buttons.addWidget(self.delete_button)

        list_buttons.addStretch()
        list_layout.addLayout(list_buttons)

    def setup_template_details(self):
        """Set up the template details widget."""
        self.details_widget = QGroupBox("Template Details")
        details_layout = QVBoxLayout(self.details_widget)

        # Template info
        info_group = QGroupBox("Information")
        info_layout = QFormLayout(info_group)

        self.name_label = QLabel("No template selected")
        self.name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        info_layout.addRow("Name:", self.name_label)

        self.type_label = QLabel("-")
        info_layout.addRow("Type:", self.type_label)

        self.description_label = QLabel("-")
        self.description_label.setWordWrap(True)
        info_layout.addRow("Description:", self.description_label)

        self.comment_text = QTextEdit()
        self.comment_text.setMaximumHeight(100)
        self.comment_text.setReadOnly(True)
        info_layout.addRow("Comments:", self.comment_text)

        details_layout.addWidget(info_group)

        # Save current config as template
        save_group = QGroupBox("Save Current Configuration")
        save_layout = QVBoxLayout(save_group)

        save_form = QFormLayout()
        self.save_name_edit = QLineEdit()
        self.save_name_edit.setPlaceholderText("Enter template name...")
        save_form.addRow("Template Name:", self.save_name_edit)

        save_layout.addLayout(save_form)

        self.save_template_button = QPushButton("Save as Template")
        self.save_template_button.clicked.connect(self.save_current_as_template)
        self.save_template_button.setEnabled(self.current_config is not None)
        save_layout.addWidget(self.save_template_button)

        details_layout.addWidget(save_group)

        # Add stretch to push content to top
        details_layout.addStretch()

    def setup_buttons(self):
        """Set up the dialog buttons."""
        self.button_layout = QHBoxLayout()

        self.load_button = QPushButton("Load Template")
        self.load_button.clicked.connect(self.load_template)
        self.load_button.setEnabled(False)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.button_layout.addWidget(self.load_button)

        self.button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.button_layout.addWidget(self.cancel_button)

    def refresh_template_list(self):
        """Refresh the template list."""
        log_button_click("Refresh Template List", "Template Dialog")
        self.template_list.clear()

        template_names = template_manager.get_template_names()
        debug(f"Found {len(template_names)} templates")

        for name in template_names:
            item = QListWidgetItem(name)

            # Add icon or styling for built-in vs custom templates
            if template_manager.is_built_in_template(name):
                item.setToolTip(f"Built-in template: {name}")
                # You could add an icon here: item.setIcon(built_in_icon)
            else:
                item.setToolTip(f"Custom template: {name}")
                # You could add an icon here: item.setIcon(custom_icon)

            self.template_list.addItem(item)

        info(f"Template list refreshed: {len(template_names)} templates available")

    def on_template_selected(self):
        """Handle template selection."""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            self.clear_template_details()
            return

        template_name = selected_items[0].text()
        template_info = template_manager.get_template_info(template_name)

        if template_info:
            self.name_label.setText(template_info["name"])
            self.type_label.setText(template_info["type"])
            self.description_label.setText(template_info["description"])
            self.comment_text.setPlainText(template_info["comment"])

            # Enable/disable buttons based on template type
            self.load_button.setEnabled(True)
            self.delete_button.setEnabled(
                not template_manager.is_built_in_template(template_name)
            )

            debug(f"Selected template: {template_name}")
        else:
            self.clear_template_details()

    def clear_template_details(self):
        """Clear template details display."""
        self.name_label.setText("No template selected")
        self.type_label.setText("-")
        self.description_label.setText("-")
        self.comment_text.clear()
        self.load_button.setEnabled(False)
        self.delete_button.setEnabled(False)

    def load_template(self):
        """Load the selected template."""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            return

        template_name = selected_items[0].text()
        log_button_click(f"Load Template: {template_name}", "Template Dialog")

        template_config = template_manager.get_template(template_name)
        if template_config:
            self.selected_template = template_config
            self.template_selected.emit(template_config)
            info(f"Template '{template_name}' loaded successfully")
            self.accept()
        else:
            QMessageBox.warning(
                self, "Load Error", f"Failed to load template '{template_name}'"
            )

    def save_current_as_template(self):
        """Save current configuration as a template."""
        if not self.current_config:
            QMessageBox.warning(
                self,
                "No Configuration",
                "No current configuration to save as template.",
            )
            return

        template_name = self.save_name_edit.text().strip()
        if not template_name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a template name.")
            return

        # Check if template already exists
        if template_name in template_manager.get_template_names():
            reply = QMessageBox.question(
                self,
                "Template Exists",
                f"Template '{template_name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        log_button_click(f"Save Template: {template_name}", "Template Dialog")

        # Create a copy of the current config for the template
        template_config = SignalSimConfig.from_dict(self.current_config.to_dict())
        template_config.description = f"Custom template: {template_name}"
        template_config.comment = "Saved from current configuration"

        if template_manager.save_template(template_name, template_config):
            QMessageBox.information(
                self,
                "Template Saved",
                f"Template '{template_name}' saved successfully.",
            )
            self.save_name_edit.clear()
            self.refresh_template_list()
            info(f"Template '{template_name}' saved successfully")
        else:
            QMessageBox.warning(
                self, "Save Error", f"Failed to save template '{template_name}'"
            )

    def delete_template(self):
        """Delete the selected template."""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            return

        template_name = selected_items[0].text()

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Template",
            f"Are you sure you want to delete template '{template_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            log_button_click(f"Delete Template: {template_name}", "Template Dialog")

            if template_manager.delete_template(template_name):
                QMessageBox.information(
                    self,
                    "Template Deleted",
                    f"Template '{template_name}' deleted successfully.",
                )
                self.refresh_template_list()
                self.clear_template_details()
                info(f"Template '{template_name}' deleted successfully")
            else:
                QMessageBox.warning(
                    self, "Delete Error", f"Failed to delete template '{template_name}'"
                )
