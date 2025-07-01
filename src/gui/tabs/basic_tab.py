"""
Basic Configuration Tab

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This tab handles basic configuration settings like version, description, and comments.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QGridLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.config.models import GNSSSignalSimConfig


class BasicTab(QWidget):
    """Basic configuration tab."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def init_ui(self):
        """Initialize the responsive user interface."""
        # Main layout with margins
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        # Basic Information Group with responsive layout
        basic_group = QGroupBox("Basic Information")
        basic_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #007acc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #007acc;
            }
        """)
        basic_layout = QGridLayout(basic_group)
        basic_layout.setSpacing(10)

        # Row 0: Version (compact)
        basic_layout.addWidget(QLabel("Version:"), 0, 0)
        self.version_combo = QComboBox()
        self.version_combo.addItems(["1.0", "1.1", "1.2", "2.0"])
        self.version_combo.setEditable(True)
        self.version_combo.setMaximumWidth(120)
        self.version_combo.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        basic_layout.addWidget(self.version_combo, 0, 1)

        # Add stretch to push version to left
        basic_layout.setColumnStretch(2, 1)

        # Row 1: Description (limited width)
        basic_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter configuration description...")
        self.description_edit.setMaximumWidth(400)
        self.description_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        basic_layout.addWidget(self.description_edit, 1, 1, 1, 2)  # Span 2 columns

        # Row 2: Comment (full width but limited height)
        basic_layout.addWidget(QLabel("Comments:"), 2, 0, Qt.AlignmentFlag.AlignTop)
        self.comment_edit = QTextEdit()
        self.comment_edit.setPlaceholderText(
            "Enter comments about this configuration..."
        )
        self.comment_edit.setMaximumHeight(100)
        self.comment_edit.setMaximumWidth(500)
        self.comment_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        basic_layout.addWidget(self.comment_edit, 2, 1, 1, 2)  # Span 2 columns

        main_layout.addWidget(basic_group)

        # Configuration Summary Group
        summary_group = QGroupBox("Configuration Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #28a745;
            }
        """)
        summary_layout = QVBoxLayout(summary_group)

        self.summary_label = QLabel("Configuration summary will be displayed here...")
        self.summary_label.setWordWrap(True)
        self.summary_label.setMaximumWidth(600)  # Limit width
        self.summary_label.setMinimumHeight(120)  # Ensure minimum height
        self.summary_label.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #343a40;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        summary_layout.addWidget(self.summary_label)

        main_layout.addWidget(summary_group)

        # Add spacer to push content to top
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        main_layout.addItem(spacer)

    def connect_signals(self):
        """Connect widget signals to update configuration."""
        self.version_combo.currentTextChanged.connect(self.update_config)
        self.description_edit.textChanged.connect(self.update_config)
        self.comment_edit.textChanged.connect(self.update_config)

    def update_config(self):
        """Update configuration from widget values."""
        try:
            self.config.version = float(self.version_combo.currentText())
        except ValueError:
            self.config.version = 1.0

        self.config.description = self.description_edit.text()
        self.config.comment = self.comment_edit.toPlainText()

        self.update_summary()
        self.config_changed.emit()

    def update_summary(self):
        """Update the configuration summary."""
        summary_parts = []

        summary_parts.append(f"Version: {self.config.version}")

        if self.config.description:
            summary_parts.append(f"Description: {self.config.description}")

        if self.config.comment:
            comment_preview = self.config.comment[:100]
            if len(self.config.comment) > 100:
                comment_preview += "..."
            summary_parts.append(f"Comments: {comment_preview}")

        # Add basic stats
        enabled_systems = [s for s in self.config.output.system_select if s.enable]
        summary_parts.append(f"Enabled Signals: {len(enabled_systems)}")

        summary_text = "\n".join(summary_parts)
        self.summary_label.setText(summary_text)

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals to prevent recursive updates
        self.version_combo.blockSignals(True)
        self.description_edit.blockSignals(True)
        self.comment_edit.blockSignals(True)

        try:
            # Set version
            version_text = str(self.config.version)
            index = self.version_combo.findText(version_text)
            if index >= 0:
                self.version_combo.setCurrentIndex(index)
            else:
                self.version_combo.setCurrentText(version_text)

            # Set description and comment
            self.description_edit.setText(self.config.description)
            self.comment_edit.setPlainText(self.config.comment)

            # Update summary
            self.update_summary()

        finally:
            # Re-enable signals
            self.version_combo.blockSignals(False)
            self.description_edit.blockSignals(False)
            self.comment_edit.blockSignals(False)
