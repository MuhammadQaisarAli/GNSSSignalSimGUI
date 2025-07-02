"""
Preferences Dialog for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides the preferences dialog for application settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget,
    QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QGroupBox, QFormLayout, QDialogButtonBox,
    QHBoxLayout, QPushButton, QLabel, QFileDialog
)
from PyQt6.QtCore import pyqtSignal

from core.utils.logger import info
from core.utils.settings import get_settings_manager, LogLevel


class PreferencesDialog(QDialog):
    """Preferences dialog for application settings."""
    
    preferences_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        """Initialize the preferences dialog."""
        super().__init__(parent)
        self.setWindowTitle("Preferences - GNSSSignalSim GUI")
        self.setModal(True)
        self.resize(600, 500)
        
        # Get settings manager
        self.settings_manager = get_settings_manager()
        
        self.setup_ui()
        self.load_preferences()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_appearance_tab()
        self.create_paths_tab()
        self.create_logging_tab()
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_preferences)
        
        layout.addWidget(button_box)
    
    def create_general_tab(self):
        """Create the general preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Auto-save group
        auto_save_group = QGroupBox("Auto-save")
        auto_save_layout = QFormLayout(auto_save_group)
        
        self.auto_save_enabled = QCheckBox("Enable auto-save")
        auto_save_layout.addRow(self.auto_save_enabled)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setSuffix(" minutes")
        auto_save_layout.addRow("Auto-save interval:", self.auto_save_interval)
        
        layout.addWidget(auto_save_group)
        
        # Validation group
        validation_group = QGroupBox("Validation")
        validation_layout = QFormLayout(validation_group)
        
        self.real_time_validation = QCheckBox("Enable real-time validation")
        validation_layout.addRow(self.real_time_validation)
        
        self.validation_level = QComboBox()
        self.validation_level.addItems(["Basic", "Standard", "Strict"])
        validation_layout.addRow("Validation level:", self.validation_level)
        
        layout.addWidget(validation_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "General")
    
    def create_appearance_tab(self):
        """Create the appearance preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Font group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_family = QComboBox()
        self.font_family.addItems(["System Default", "Arial", "Helvetica", "Times New Roman"])
        font_layout.addRow("Font family:", self.font_family)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        font_layout.addRow("Font size:", self.font_size)
        
        layout.addWidget(font_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Appearance")
    
    def create_paths_tab(self):
        """Create the paths preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Default paths group
        paths_group = QGroupBox("Default Paths")
        paths_layout = QFormLayout(paths_group)
        
        # Default config path
        config_path_layout = QHBoxLayout()
        self.default_config_path = QLineEdit()
        self.default_config_path.setPlaceholderText("data/configs")
        config_path_layout.addWidget(self.default_config_path)
        
        self.browse_config_button = QPushButton("Browse...")
        self.browse_config_button.setMaximumWidth(80)
        self.browse_config_button.clicked.connect(self.browse_config_path)
        config_path_layout.addWidget(self.browse_config_button)
        
        paths_layout.addRow("Default config path:", config_path_layout)
        
        # Default ephemeris path
        ephemeris_path_layout = QHBoxLayout()
        self.default_ephemeris_path = QLineEdit()
        self.default_ephemeris_path.setPlaceholderText("data/ephemeris")
        ephemeris_path_layout.addWidget(self.default_ephemeris_path)
        
        self.browse_ephemeris_button = QPushButton("Browse...")
        self.browse_ephemeris_button.setMaximumWidth(80)
        self.browse_ephemeris_button.clicked.connect(self.browse_ephemeris_path)
        ephemeris_path_layout.addWidget(self.browse_ephemeris_button)
        
        paths_layout.addRow("Default ephemeris path:", ephemeris_path_layout)
        
        # Default IFDataGen executable path
        ifdatagen_path_layout = QHBoxLayout()
        self.default_ifdatagen_path = QLineEdit()
        self.default_ifdatagen_path.setPlaceholderText("data/ifdatagen")
        ifdatagen_path_layout.addWidget(self.default_ifdatagen_path)
        
        self.browse_ifdatagen_button = QPushButton("Browse...")
        self.browse_ifdatagen_button.setMaximumWidth(80)
        self.browse_ifdatagen_button.clicked.connect(self.browse_ifdatagen_path)
        ifdatagen_path_layout.addWidget(self.browse_ifdatagen_button)
        
        paths_layout.addRow("Default IFDataGen path:", ifdatagen_path_layout)
        
        # Default generated outputs path
        generated_path_layout = QHBoxLayout()
        self.default_generated_path = QLineEdit()
        self.default_generated_path.setPlaceholderText("data/generated")
        generated_path_layout.addWidget(self.default_generated_path)
        
        self.browse_generated_button = QPushButton("Browse...")
        self.browse_generated_button.setMaximumWidth(80)
        self.browse_generated_button.clicked.connect(self.browse_generated_path)
        generated_path_layout.addWidget(self.browse_generated_button)
        
        paths_layout.addRow("Default generated path:", generated_path_layout)
        
          
        layout.addWidget(paths_group)
        
        # Add info section
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_label = QLabel(
            "- These paths will be used as default locations when opening file dialogs\n"
            "- Leave empty to use the application's current directory\n"
            "- Paths will be created automatically if they don't exist\n"
            "- IFDataGen path: Directory containing IFDataGen.exe (default: data/ifdatagen)\n"
            "- Generated path: Base directory for simulation outputs (default: data/generated)\n"
            "- Output files are automatically organized in subdirectories by type\n"
        )
        info_label.setStyleSheet("color: #666; font-size: 9px; padding: 5px;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Paths")
    
    def create_logging_tab(self):
        """Create the logging preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File logging group
        file_logging_group = QGroupBox("File Logging")
        file_logging_layout = QFormLayout(file_logging_group)
        
        self.enable_file_logging = QCheckBox("Enable file logging")
        file_logging_layout.addRow(self.enable_file_logging)
        
        self.file_log_level = QComboBox()
        log_levels = [level.value for level in LogLevel]
        self.file_log_level.addItems(log_levels)
        file_logging_layout.addRow("File log level:", self.file_log_level)
        
        # Info about log file location
        log_info_label = QLabel("Log files are saved to: logs/GNSSSignalSimGUI_YYYYMMDD.log")
        log_info_label.setStyleSheet("color: #666; font-style: italic; font-size: 9px;")
        file_logging_layout.addRow(log_info_label)
        
        layout.addWidget(file_logging_group)
        
        # Console logging group
        console_logging_group = QGroupBox("Console Logging")
        console_logging_layout = QFormLayout(console_logging_group)
        
        self.enable_console_logging = QCheckBox("Enable console logging")
        console_logging_layout.addRow(self.enable_console_logging)
        
        self.console_log_level = QComboBox()
        self.console_log_level.addItems(log_levels)
        console_logging_layout.addRow("Console log level:", self.console_log_level)
        
        layout.addWidget(console_logging_group)
        
        # Advanced logging group
        advanced_logging_group = QGroupBox("Advanced")
        advanced_logging_layout = QFormLayout(advanced_logging_group)
        
        self.log_rotation = QCheckBox("Enable log file rotation")
        advanced_logging_layout.addRow(self.log_rotation)
        
        self.max_log_size = QSpinBox()
        self.max_log_size.setRange(1, 100)
        self.max_log_size.setValue(10)
        self.max_log_size.setSuffix(" MB")
        advanced_logging_layout.addRow("Max log file size:", self.max_log_size)
        
        layout.addWidget(advanced_logging_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Logging")
    
    def browse_config_path(self):
        """Browse for default config directory."""
        current_path = self.default_config_path.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Configuration Directory",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.default_config_path.setText(directory)
    
    def browse_ephemeris_path(self):
        """Browse for default ephemeris directory."""
        current_path = self.default_ephemeris_path.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Ephemeris Directory",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.default_ephemeris_path.setText(directory)
    
    
    def browse_ifdatagen_path(self):
        """Browse for default IFDataGen directory."""
        current_path = self.default_ifdatagen_path.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default IFDataGen Directory",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.default_ifdatagen_path.setText(directory)
    
    def browse_generated_path(self):
        """Browse for default generated outputs directory."""
        current_path = self.default_generated_path.text() or "."
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Default Generated Outputs Directory",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        if directory:
            self.default_generated_path.setText(directory)
    
    
    def load_preferences(self):
        """Load preferences from settings."""
        # General tab
        general_settings = self.settings_manager.get_section("general")
        self.auto_save_enabled.setChecked(general_settings.get("auto_save_enabled", True))
        self.auto_save_interval.setValue(general_settings.get("auto_save_interval", 5))
        self.real_time_validation.setChecked(general_settings.get("real_time_validation", True))
        self.validation_level.setCurrentText(general_settings.get("validation_level", "Standard"))
        
        # Appearance tab
        appearance_settings = self.settings_manager.get_section("appearance")
        self.theme_combo.setCurrentText(appearance_settings.get("theme", "System"))
        self.font_family.setCurrentText(appearance_settings.get("font_family", "System Default"))
        self.font_size.setValue(appearance_settings.get("font_size", 10))
        
        # Paths tab
        paths_settings = self.settings_manager.get_section("paths")
        self.default_config_path.setText(paths_settings.get("default_config_path", "data/configs"))
        self.default_ephemeris_path.setText(paths_settings.get("default_ephemeris_path", "data/ephemeris"))
        self.default_ifdatagen_path.setText(paths_settings.get("default_ifdatagen_path", "data/ifdatagen"))
        self.default_generated_path.setText(paths_settings.get("default_generated_path", "data/generated"))
        
        # Logging tab
        logging_settings = self.settings_manager.get_section("logging")
        self.enable_file_logging.setChecked(logging_settings.get("enable_file_logging", True))
        self.file_log_level.setCurrentText(logging_settings.get("file_log_level", "INFO"))
        
        self.enable_console_logging.setChecked(logging_settings.get("enable_console_logging", True))
        self.console_log_level.setCurrentText(logging_settings.get("console_log_level", "WARNING"))
        
        # Advanced logging settings
        self.log_rotation.setChecked(logging_settings.get("log_rotation", False))
        self.max_log_size.setValue(logging_settings.get("max_log_size", 10))
    
    def apply_preferences(self):
        """Apply the current preferences."""
        # Save general settings
        self.settings_manager.set_section("general", {
            "auto_save_enabled": self.auto_save_enabled.isChecked(),
            "auto_save_interval": self.auto_save_interval.value(),
            "real_time_validation": self.real_time_validation.isChecked(),
            "validation_level": self.validation_level.currentText()
        })
        
        # Save appearance settings
        self.settings_manager.set_section("appearance", {
            "theme": self.theme_combo.currentText(),
            "font_family": self.font_family.currentText(),
            "font_size": self.font_size.value()
        })
        
        # Save paths settings
        self.settings_manager.set_section("paths", {
            "default_config_path": self.default_config_path.text(),
            "default_ephemeris_path": self.default_ephemeris_path.text(),
            "default_generated_path": self.default_generated_path.text(),
            "ifdatagen_executable_path": self.ifdatagen_executable_path.text()
        })
        
        # Save logging settings
        self.settings_manager.set_section("logging", {
            "enable_file_logging": self.enable_file_logging.isChecked(),
            "file_log_level": self.file_log_level.currentText(),
            "enable_console_logging": self.enable_console_logging.isChecked(),
            "console_log_level": self.console_log_level.currentText(),
            "log_rotation": self.log_rotation.isChecked(),
            "max_log_size": self.max_log_size.value()
        })
        
        # Save to file
        if self.settings_manager.save_settings():
            info("Preferences saved successfully")
        else:
            info("Failed to save preferences")
        
        self.preferences_changed.emit()
    
    def accept(self):
        """Accept the dialog and apply preferences."""
        self.apply_preferences()
        super().accept()