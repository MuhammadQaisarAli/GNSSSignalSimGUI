"""
Main Window for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module contains the main application window with tabbed interface
and menu system.
"""

import os
import json

from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QFileDialog,
    QPushButton,
    QSplitter,
    QTextEdit,
    QLabel,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QIcon

from core.config.models import GNSSSignalSimConfig, get_default_system_select
from core.utils.logger import info, debug, log_button_click, error, configure_logging_from_settings
from core.utils.settings import get_settings_manager, get_default_path
from core.utils.version import get_app_title, get_cached_project_info
from core.integration.ifdatagen import IFDataGenIntegration
from core.workflow.manager import get_workflow_manager, WorkflowStep, ValidationStatus
from core.workflow.smart_workflow import get_smart_workflow_manager, ValidationLevel, register_smart_validation_callback
from gui.tabs.basic_tab import BasicTab
from gui.tabs.ephemeris_time_tab import EphemerisTimeTab
from gui.tabs.trajectory_tab import TrajectoryTab
from gui.tabs.signal_selection_tab import SignalSelectionTab
from gui.tabs.power_tab import PowerTab
from gui.tabs.output_settings_tab import OutputSettingsTab
from gui.tabs.almanac_tab import AlmanacTab
from gui.dialogs.template_dialog import TemplateDialog
from gui.dialogs.about import AboutDialog
from gui.dialogs.preferences import PreferencesDialog



class MainWindow(QMainWindow):
    """Main application window."""

    config_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        info("Initializing GNSSSignalSim GUI Main Window")

        # Initialize settings manager
        self.settings_manager = get_settings_manager()
        
        self.config = GNSSSignalSimConfig()
        self.config.output.system_select = get_default_system_select()
        self.current_file = None
        self.is_modified = False

        # Initialize workflow managers
        self.workflow_manager = get_workflow_manager()  # Keep old one for compatibility
        self.smart_workflow = get_smart_workflow_manager()  # New smart workflow

        debug(
            f"Default configuration created with {len(self.config.output.system_select)} system selections"
        )

        self.init_ui()
        self.setup_icon()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        self.connect_signals()
        self.setup_workflow()
        self.setup_smart_workflow()

        # Auto-save timer (create before applying settings)
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        
        # Apply settings (this will configure the auto-save timer)
        self.apply_settings()

    def init_ui(self):
        """Initialize the responsive user interface."""
        self.setWindowTitle(get_app_title())

        # Set minimum and initial window size
        self.setMinimumSize(1200, 700)
        self.setGeometry(100, 100, 1400, 900)

        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with margins
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create splitter for main content and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Prevent collapsing
        main_layout.addWidget(splitter)

        # Left side: Configuration tabs
        self.setup_tabs()
        splitter.addWidget(self.tab_widget)

        # Right side: JSON preview and controls
        self.setup_preview_panel()
        splitter.addWidget(self.preview_widget)

        # Set splitter proportions and constraints
        splitter.setSizes([1000, 400])
        splitter.setStretchFactor(0, 1)  # Tabs can stretch
        splitter.setStretchFactor(1, 0)  # Preview has fixed proportion

    def setup_tabs(self):
        """Set up the configuration tabs."""
        self.tab_widget = QTabWidget()

        # Configuration flag for almanac tab visibility
        self.show_almanac_tab = False  # Set to True to enable almanac tab

        # Create tabs in workflow order
        self.basic_tab = BasicTab(self.config)
        self.ephemeris_time_tab = EphemerisTimeTab(self.config)
        self.trajectory_tab = TrajectoryTab(self.config)
        self.signal_selection_tab = SignalSelectionTab(self.config)
        self.power_tab = PowerTab(self.config)
        self.output_settings_tab = OutputSettingsTab(self.config)
        self.almanac_tab = AlmanacTab(self.config)  # Keep for future use

        # Add tabs to widget in workflow sequence
        self.tab_widget.addTab(self.basic_tab, "Basic")
        self.tab_widget.addTab(self.ephemeris_time_tab, "Ephemeris and Time")
        self.tab_widget.addTab(self.trajectory_tab, "Trajectory")
        self.tab_widget.addTab(self.signal_selection_tab, "Signal Selection")
        self.tab_widget.addTab(self.power_tab, "Signal Power")
        self.tab_widget.addTab(self.output_settings_tab, "Output Settings")
        
        # Conditionally add almanac tab (hidden for now)
        if self.show_almanac_tab:
            self.tab_widget.addTab(self.almanac_tab, "Almanac")

    def setup_preview_panel(self):
        """Set up the JSON preview panel with size constraints."""
        self.preview_widget = QWidget()
        self.preview_widget.setMinimumWidth(350)
        self.preview_widget.setMaximumWidth(500)
        self.preview_widget.setStyleSheet("""
            QWidget {
                border: 2px solid #6f42c1;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self.preview_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Preview label
        preview_label = QLabel("Configuration Preview")
        preview_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        preview_label.setStyleSheet("""
            QLabel {
                color: #6f42c1;
                font-weight: bold;
                padding: 5px;
                border: none;
                background: transparent;
            }
        """)
        layout.addWidget(preview_label)

        # JSON preview text area
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setFont(QFont("Consolas", 9))
        self.json_preview.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.json_preview.setStyleSheet("""
            QTextEdit {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 8px;
            background-color: #343a40;
            }
        """)

        layout.addWidget(self.json_preview)

        # Control buttons
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Config")
        self.save_button.clicked.connect(lambda: self.save_config_with_logging())
        button_layout.addWidget(self.save_button)

        self.load_button = QPushButton("Load Config")
        self.load_button.clicked.connect(lambda: self.load_config_with_logging())
        button_layout.addWidget(self.load_button)

        self.generate_button = QPushButton("Generate Signals")
        self.generate_button.clicked.connect(
            lambda: self.generate_signals_with_logging()
        )
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(self.generate_button)

        layout.addLayout(button_layout)

        # Update preview initially
        self.update_preview()

    def setup_icon(self):
        """Set up the application icon."""
        try:
            # Try to load the icon from resources
            icon_path = "src/gui/resources/icons/gnsssignalsimgui.ico"
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
                self.setWindowIcon(icon)
                info(f"Application icon loaded from {icon_path}")
            else:
                debug(f"Icon file not found at {icon_path}")
        except Exception as e:
            debug(f"Failed to load application icon: {e}")

    def setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_config)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.load_config)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_config)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_config_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Templates menu
        templates_menu = menubar.addMenu("Templates")

        load_template_action = QAction("Load Template...", self)
        load_template_action.setShortcut("Ctrl+T")
        load_template_action.triggered.connect(self.load_template)
        templates_menu.addAction(load_template_action)

        save_template_action = QAction("Save as Template...", self)
        save_template_action.triggered.connect(self.save_as_template)
        templates_menu.addAction(save_template_action)

        templates_menu.addSeparator()

        manage_templates_action = QAction("Manage Templates...", self)
        manage_templates_action.triggered.connect(self.manage_templates)
        templates_menu.addAction(manage_templates_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        validate_action = QAction("Validate Configuration", self)
        validate_action.triggered.connect(self.validate_config)
        tools_menu.addAction(validate_action)

        generate_action = QAction("Generate Signals", self)
        generate_action.setShortcut("F5")
        generate_action.triggered.connect(self.generate_signals)
        tools_menu.addAction(generate_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        preferences_action = QAction("Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = self.addToolBar("Main")

        # Add common actions to toolbar
        toolbar.addAction("New", self.new_config)
        toolbar.addAction("Open", self.load_config)
        toolbar.addAction("Save", self.save_config)
        toolbar.addSeparator()
        toolbar.addAction("Generate", self.generate_signals)

    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = self.statusBar()

        # Add permanent widgets to status bar
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.file_label = QLabel("No file loaded")
        self.status_bar.addPermanentWidget(self.file_label)

    def connect_signals(self):
        """Connect signals between components."""
        # Connect all created tabs, regardless of whether they're added to the widget
        tabs_to_connect = [
            self.basic_tab,
            self.ephemeris_time_tab,
            self.trajectory_tab,
            self.signal_selection_tab,
            self.power_tab,
            self.output_settings_tab,
            self.almanac_tab,  # Connect even if hidden
        ]
        
        for tab in tabs_to_connect:
            if hasattr(tab, "config_changed"):
                tab.config_changed.connect(self.on_config_changed)

        # Connect tab change to refresh current tab
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

    def setup_workflow(self):
        """Set up workflow management and validation callbacks."""
        # Connect workflow manager signals
        self.workflow_manager.step_status_changed.connect(self.on_workflow_step_changed)
        self.workflow_manager.workflow_progress_changed.connect(self.on_workflow_progress_changed)
        self.workflow_manager.tab_state_changed.connect(self.on_tab_state_changed)
        
        # Register validation callbacks for each workflow step
        from core.workflow.manager import register_validation_callback
        
        # Basic info validation (always valid)
        register_validation_callback(WorkflowStep.BASIC_INFO, self.validate_basic_info)
        
        # Ephemeris loading validation
        register_validation_callback(WorkflowStep.EPHEMERIS_LOADING, self.validate_ephemeris_loading)
        
        # Time validation
        register_validation_callback(WorkflowStep.TIME_VALIDATION, self.validate_time_configuration)
        
        # Trajectory validation
        register_validation_callback(WorkflowStep.TRAJECTORY_CONFIG, self.validate_trajectory_configuration)
        
        # Signal selection validation
        register_validation_callback(WorkflowStep.SIGNAL_SELECTION, self.validate_signal_selection)
        
        # Power configuration validation
        register_validation_callback(WorkflowStep.POWER_CONFIG, self.validate_power_configuration)
        
        # Output settings validation
        register_validation_callback(WorkflowStep.OUTPUT_SETTINGS, self.validate_output_settings)
        
        # Temporarily disable initial workflow validation to fix tab navigation
        # TODO: Re-enable once workflow logic is properly debugged
        # self.workflow_manager.validate_all_steps()
        
        info("Workflow management setup complete")

    def setup_smart_workflow(self):
        """Set up smart workflow management with helpful guidance."""
        # Connect smart workflow signals
        self.smart_workflow.step_feedback_changed.connect(self.on_step_feedback_changed)
        self.smart_workflow.overall_progress_changed.connect(self.on_smart_progress_changed)
        self.smart_workflow.workflow_summary_changed.connect(self.on_workflow_summary_changed)
        
        # Register smart validation callbacks
        register_smart_validation_callback(WorkflowStep.BASIC_INFO, self.smart_validate_basic_info)
        register_smart_validation_callback(WorkflowStep.EPHEMERIS_LOADING, self.smart_validate_ephemeris_loading)
        register_smart_validation_callback(WorkflowStep.TIME_VALIDATION, self.smart_validate_time_configuration)
        register_smart_validation_callback(WorkflowStep.TRAJECTORY_CONFIG, self.smart_validate_trajectory_configuration)
        register_smart_validation_callback(WorkflowStep.SIGNAL_SELECTION, self.smart_validate_signal_selection)
        register_smart_validation_callback(WorkflowStep.POWER_CONFIG, self.smart_validate_power_configuration)
        register_smart_validation_callback(WorkflowStep.OUTPUT_SETTINGS, self.smart_validate_output_settings)
        
        # Initial smart validation with delay to ensure UI is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.smart_workflow.validate_all_steps)
        
        info("Smart workflow management setup complete")

    def on_step_feedback_changed(self, step: WorkflowStep, level: ValidationLevel, title: str, message: str):
        """Handle smart workflow step feedback changes."""
        debug(f"Smart workflow feedback: {step.value} -> {level.value}: {title}")
        # We can add visual indicators to tabs here if needed
        
    def on_smart_progress_changed(self, progress: int):
        """Handle smart workflow progress changes."""
        # Update progress bar with smart workflow progress
        self.progress_bar.setValue(progress)
        if progress < 100:
            self.progress_bar.setVisible(True)
        else:
            self.progress_bar.setVisible(False)
        debug(f"Smart workflow progress: {progress}%")

    def on_workflow_summary_changed(self, summary: str):
        """Handle workflow summary changes for status bar."""
        self.status_label.setText(summary)
        debug(f"Workflow summary: {summary}")

    def on_workflow_step_changed(self, step: WorkflowStep, status: ValidationStatus, message: str):
        """Handle workflow step status changes."""
        debug(f"Workflow step {step.value} changed to {status.value}: {message}")
        
        # Update status bar with current step information
        if status == ValidationStatus.INVALID or status == ValidationStatus.ERROR:
            self.status_label.setText(f"Warning: {step.value.replace('_', ' ').title()}: {message}")
        elif status == ValidationStatus.VALID:
            next_step = self.workflow_manager.get_next_required_step()
            if next_step:
                self.status_label.setText(f"Complete: {step.value.replace('_', ' ').title()}. Next: {next_step.value.replace('_', ' ').title()}")
            else:
                self.status_label.setText("All workflow steps complete!")

    def on_workflow_progress_changed(self, progress: int):
        """Handle overall workflow progress changes."""
        self.progress_bar.setVisible(progress < 100)
        self.progress_bar.setValue(progress)
        debug(f"Workflow progress: {progress}%")

    def on_tab_state_changed(self, tab_name: str, enabled: bool):
        """Handle tab enabled/disabled state changes."""
        debug(f"Received tab state change: '{tab_name}' -> {'enabled' if enabled else 'disabled'}")
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setTabEnabled(i, enabled)
                debug(f"Applied: Tab '{tab_name}' at index {i} {'enabled' if enabled else 'disabled'}")
                break
        else:
            debug(f"Warning: Tab '{tab_name}' not found in tab widget")

    def on_config_changed(self):
        """Handle configuration changes."""
        self.is_modified = True
        self.update_window_title()
        self.update_preview()
        self.config_changed.emit()
        
        # Use smart workflow validation with throttling
        if hasattr(self, 'smart_workflow'):
            self.smart_workflow.request_validation(1000)  # 1 second delay

    def on_tab_changed(self, index):
        """Handle tab change to refresh current tab."""
        tab = self.tab_widget.widget(index)
        tab_name = self.tab_widget.tabText(index)
        debug(f"Tab changed to: {tab_name}")

        if hasattr(tab, "refresh_from_config"):
            debug(f"Refreshing tab: {tab_name}")
            tab.refresh_from_config()

    def update_window_title(self):
        """Update window title based on current file and modification status."""
        title = get_app_title()
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def update_preview(self):
        """Update the JSON preview."""
        try:
            config_dict = self.config.to_dict()
            json_text = json.dumps(config_dict, indent=2, ensure_ascii=False)
            self.json_preview.setPlainText(json_text)
        except Exception as e:
            self.json_preview.setPlainText(f"Error generating preview: {str(e)}")

    def new_config(self):
        """Create a new configuration."""
        if self.check_save_changes():
            self.config = GNSSSignalSimConfig()
            self.config.output.system_select = get_default_system_select()
            self.current_file = None
            self.is_modified = False
            self.update_window_title()
            self.update_preview()
            self.refresh_tabs()
            self.status_label.setText("New configuration created")

    def load_config(self):
        """Load configuration from file."""
        if not self.check_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Configuration", get_default_path("config"), "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.config = GNSSSignalSimConfig.from_dict(data)
                self.current_file = file_path
                self.is_modified = False
                self.update_window_title()
                self.update_preview()
                self.refresh_tabs()
                self.file_label.setText(os.path.basename(file_path))
                self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")

            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to load configuration:\n{str(e)}"
                )

    def save_config(self):
        """Save current configuration."""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_config_as()

    def save_config_as(self):
        """Save configuration to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Configuration",
            get_default_path("config") + "/config.json",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            self.save_to_file(file_path)

    def save_to_file(self, file_path: str):
        """Save configuration to specified file."""
        try:
            config_dict = self.config.to_dict()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.current_file = file_path
            self.is_modified = False
            self.update_window_title()
            self.file_label.setText(os.path.basename(file_path))
            self.status_label.setText(f"Saved: {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to save configuration:\n{str(e)}"
            )

    def auto_save(self):
        """Auto-save configuration if modified."""
        if self.is_modified and self.current_file:
            try:
                backup_path = self.current_file + ".backup"
                self.save_to_file(backup_path)
            except Exception as e:
                debug(f"Auto-save failed: {e}")  # Log the error for debugging
                pass  # Ignore auto-save errors

    def validate_config(self):
        """Validate current configuration."""
        # TODO: Implement comprehensive validation
        QMessageBox.information(
            self, "Validation", "Configuration validation will be implemented."
        )

    def generate_signals(self):
        """Generate signals using IFDataGen.exe."""
        # Check if IFDataGen is available
        if not IFDataGenIntegration.is_available():
            reply = QMessageBox.question(
                self,
                "IFDataGen Not Found",
                "IFDataGen.exe was not found. Would you like to locate it manually?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                from PyQt6.QtWidgets import QFileDialog

                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Locate IFDataGen.exe",
                    get_default_path("config"),
                    "Executable Files (*.exe);;All Files (*)",
                )
                if file_path:
                    IFDataGenIntegration.set_ifdatagen_path(file_path)
                else:
                    return
            else:
                return

        # Check if we need to save the configuration first
        if self.is_modified or not self.current_file:
            reply = QMessageBox.question(
                self,
                "Save Required",
                "Configuration must be saved before generating signals. Save now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                if not self.current_file:
                    self.save_config_as()
                else:
                    self.save_config()

                if self.is_modified:  # Save failed
                    return
            else:
                return

        # Connect IFDataGen signals
        IFDataGenIntegration.progress_updated.connect(self.on_generation_progress)
        IFDataGenIntegration.status_updated.connect(self.on_generation_status)
        IFDataGenIntegration.generation_finished.connect(self.on_generation_finished)

        # Start signal generation
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting signal generation...")

        # Disable generate button to prevent multiple runs
        self.generate_button.setEnabled(False)

        # Get output directory from config
        output_dir = os.path.dirname(self.current_file) if self.current_file else None

        success = IFDataGenIntegration.generate_signals(self.config, output_dir)
        if not success:
            self.progress_bar.setVisible(False)
            self.generate_button.setEnabled(True)
            self.status_label.setText("Ready")

    def on_generation_progress(self, progress):
        """Handle signal generation progress updates."""
        self.progress_bar.setValue(progress)

    def on_generation_status(self, status):
        """Handle signal generation status updates."""
        self.status_label.setText(status)

    def on_generation_finished(self, success, message):
        """Handle signal generation completion."""
        self.progress_bar.setVisible(False)
        self.generate_button.setEnabled(True)

        if success:
            self.status_label.setText("Signal generation completed")
            QMessageBox.information(
                self,
                "Generation Complete",
                "Signal generation completed successfully!\n\n" + message,
            )
            info("Signal generation completed successfully")
        else:
            self.status_label.setText("Signal generation failed")
            QMessageBox.warning(
                self, "Generation Failed", "Signal generation failed:\n\n" + message
            )
            error(f"Signal generation failed: {message}")

        # Disconnect signals to prevent memory leaks
        try:
            IFDataGenIntegration.progress_updated.disconnect(
                self.on_generation_progress
            )
            IFDataGenIntegration.status_updated.disconnect(self.on_generation_status)
            IFDataGenIntegration.generation_finished.disconnect(
                self.on_generation_finished
            )
        except:
            pass  # Ignore disconnect errors

    def refresh_tabs(self):
        """Refresh all tabs with current configuration."""
        debug("Refreshing all tabs with current configuration")
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, "refresh_from_config"):
                tab_name = self.tab_widget.tabText(i)
                debug(f"Refreshing tab: {tab_name}")
                tab.refresh_from_config()

    def check_save_changes(self) -> bool:
        """Check if changes need to be saved. Returns True if it's safe to continue."""
        if not self.is_modified:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_config()
            return not self.is_modified  # Return True if save was successful
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def show_preferences(self):
        """Show preferences dialog."""
        log_button_click("Show Preferences")
        
        dialog = PreferencesDialog(self)
        dialog.preferences_changed.connect(self.on_preferences_changed)
        
        if dialog.exec() == PreferencesDialog.DialogCode.Accepted:
            info("Preferences dialog accepted")
            self.status_label.setText("Preferences updated")
        else:
            info("Preferences dialog cancelled")

    def show_about(self):
        """Show about dialog."""
        log_button_click("Show About")
        
        dialog = AboutDialog(self)
        dialog.exec()
        
        info("About dialog shown")

    def apply_settings(self):
        """Apply current settings to the application."""
        # Apply auto-save settings
        auto_save_enabled = self.settings_manager.get("general", "auto_save_enabled", True)
        if auto_save_enabled:
            auto_save_interval = self.settings_manager.get("general", "auto_save_interval", 5) * 60 * 1000
            self.auto_save_timer.start(auto_save_interval)
        else:
            self.auto_save_timer.stop()
        
        # Apply appearance settings
        font_family = self.settings_manager.get("appearance", "font_family", "System Default")
        font_size = self.settings_manager.get("appearance", "font_size", 10)
        
        if font_family != "System Default":
            font = QFont(font_family, font_size)
            self.setFont(font)
        
        # Apply logging settings
        self.apply_logging_settings()
        
        info("Application settings applied")
    
    def apply_logging_settings(self):
        """Apply logging settings to the logger."""
        configure_logging_from_settings(self.settings_manager)

    def on_preferences_changed(self):
        """Handle preferences changes."""
        info("Preferences have been changed")
        
        # Reapply all settings
        self.apply_settings()
        
        self.status_label.setText("Preferences applied")

    def save_config_with_logging(self):
        """Save config with logging."""
        log_button_click(
            "Save Config", additional_info=f"Current file: {self.current_file}"
        )
        self.save_config()

    def load_config_with_logging(self):
        """Load config with logging."""
        log_button_click("Load Config")
        self.load_config()

    def generate_signals_with_logging(self):
        """Generate signals with logging."""
        log_button_click(
            "Generate Signals", additional_info=f"Config file: {self.current_file}"
        )
        self.generate_signals()

    def load_template(self):
        """Load a configuration template."""
        log_button_click("Load Template")

        dialog = TemplateDialog(self, self.config)
        dialog.template_selected.connect(self.apply_template)
        dialog.exec()

    def save_as_template(self):
        """Save current configuration as a template."""
        log_button_click("Save as Template")

        dialog = TemplateDialog(self, self.config)
        dialog.exec()

    def manage_templates(self):
        """Open template management dialog."""
        log_button_click("Manage Templates")

        dialog = TemplateDialog(self, self.config)
        dialog.exec()

    def apply_template(self, template_config):
        """Apply a template configuration."""
        if self.check_save_changes():
            self.config = template_config
            self.current_file = None
            self.is_modified = True

            # Refresh all tabs
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, "refresh_from_config"):
                    tab.refresh_from_config()

            self.update_window_title()
            self.update_preview()
            self.file_label.setText("Template loaded")

            info("Template applied successfully")
            QMessageBox.information(
                self,
                "Template Loaded",
                "Template configuration has been applied successfully.",
            )

    def closeEvent(self, event):
        """Handle application close event."""
        info("Application closing")
        if self.check_save_changes():
            info("Application closed successfully")
            event.accept()
        else:
            info("Application close cancelled by user")
            event.ignore()

    # Validation methods for each workflow step
    def validate_basic_info(self):
        """Validate basic information step."""
        try:
            # Basic info is always valid if we have a config
            if self.config:
                self.workflow_manager.update_step_status(
                    WorkflowStep.BASIC_INFO,
                    ValidationStatus.VALID,
                    "Basic information configured",
                    completion_percentage=100
                )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.BASIC_INFO,
                    ValidationStatus.INVALID,
                    "No configuration available"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.BASIC_INFO,
                ValidationStatus.ERROR,
                f"Error validating basic info: {str(e)}"
            )

    def validate_ephemeris_loading(self):
        """Validate ephemeris loading step."""
        try:
            if self.config.ephemeris and len(self.config.ephemeris) > 0:
                # Check if files exist and are valid
                valid_files = 0
                total_files = len(self.config.ephemeris)
                
                for eph_config in self.config.ephemeris:
                    if os.path.exists(eph_config.name):
                        valid_files += 1
                
                if valid_files > 0:
                    completion = int((valid_files / total_files) * 100)
                    self.workflow_manager.update_step_status(
                        WorkflowStep.EPHEMERIS_LOADING,
                        ValidationStatus.VALID,
                        f"{valid_files}/{total_files} ephemeris files loaded",
                        completion_percentage=completion
                    )
                else:
                    self.workflow_manager.update_step_status(
                        WorkflowStep.EPHEMERIS_LOADING,
                        ValidationStatus.INVALID,
                        "No valid ephemeris files found"
                    )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.EPHEMERIS_LOADING,
                    ValidationStatus.INVALID,
                    "No ephemeris files loaded"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.EPHEMERIS_LOADING,
                ValidationStatus.ERROR,
                f"Error validating ephemeris: {str(e)}"
            )

    def validate_time_configuration(self):
        """Validate time configuration step."""
        try:
            # Delegate to ephemeris_time_tab for detailed validation
            if hasattr(self.ephemeris_time_tab, 'ephemeris_file_ranges') and self.ephemeris_time_tab.ephemeris_file_ranges:
                # Check if current time is within validity range
                self.ephemeris_time_tab.validate_current_time()
                
                # Check the validation result from the tab
                status_text = self.ephemeris_time_tab.time_status_label.text()
                if "VALID" in status_text:
                    self.workflow_manager.update_step_status(
                        WorkflowStep.TIME_VALIDATION,
                        ValidationStatus.VALID,
                        "Time is within ephemeris validity range",
                        completion_percentage=100
                    )
                else:
                    self.workflow_manager.update_step_status(
                        WorkflowStep.TIME_VALIDATION,
                        ValidationStatus.INVALID,
                        "Time is outside ephemeris validity range"
                    )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.TIME_VALIDATION,
                    ValidationStatus.INVALID,
                    "No ephemeris validity range available"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.TIME_VALIDATION,
                ValidationStatus.ERROR,
                f"Error validating time: {str(e)}"
            )

    def validate_trajectory_configuration(self):
        """Validate trajectory configuration step."""
        try:
            # Check if trajectory is configured
            if hasattr(self.config.trajectory, 'trajectory_list') and self.config.trajectory.trajectory_list:
                self.workflow_manager.update_step_status(
                    WorkflowStep.TRAJECTORY_CONFIG,
                    ValidationStatus.VALID,
                    f"{len(self.config.trajectory.trajectory_list)} trajectory segments configured",
                    completion_percentage=100
                )
            else:
                # Static trajectory is also valid
                self.workflow_manager.update_step_status(
                    WorkflowStep.TRAJECTORY_CONFIG,
                    ValidationStatus.VALID,
                    "Static trajectory configured",
                    completion_percentage=100
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.TRAJECTORY_CONFIG,
                ValidationStatus.ERROR,
                f"Error validating trajectory: {str(e)}"
            )

    def validate_signal_selection(self):
        """Validate signal selection step."""
        try:
            if self.config.output.system_select:
                enabled_signals = [s for s in self.config.output.system_select if s.enable]
                if enabled_signals:
                    self.workflow_manager.update_step_status(
                        WorkflowStep.SIGNAL_SELECTION,
                        ValidationStatus.VALID,
                        f"{len(enabled_signals)} signals selected",
                        completion_percentage=100
                    )
                else:
                    self.workflow_manager.update_step_status(
                        WorkflowStep.SIGNAL_SELECTION,
                        ValidationStatus.INVALID,
                        "No signals selected"
                    )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.SIGNAL_SELECTION,
                    ValidationStatus.INVALID,
                    "Signal selection not configured"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.SIGNAL_SELECTION,
                ValidationStatus.ERROR,
                f"Error validating signal selection: {str(e)}"
            )

    def validate_power_configuration(self):
        """Validate power configuration step."""
        try:
            if self.config.power:
                self.workflow_manager.update_step_status(
                    WorkflowStep.POWER_CONFIG,
                    ValidationStatus.VALID,
                    "Power configuration set",
                    completion_percentage=100
                )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.POWER_CONFIG,
                    ValidationStatus.INVALID,
                    "Power configuration missing"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.POWER_CONFIG,
                ValidationStatus.ERROR,
                f"Error validating power config: {str(e)}"
            )

    def validate_output_settings(self):
        """Validate output settings step."""
        try:
            if self.config.output and self.config.output.name:
                self.workflow_manager.update_step_status(
                    WorkflowStep.OUTPUT_SETTINGS,
                    ValidationStatus.VALID,
                    "Output settings configured",
                    completion_percentage=100
                )
            else:
                self.workflow_manager.update_step_status(
                    WorkflowStep.OUTPUT_SETTINGS,
                    ValidationStatus.INVALID,
                    "Output file not specified"
                )
        except Exception as e:
            self.workflow_manager.update_step_status(
                WorkflowStep.OUTPUT_SETTINGS,
                ValidationStatus.ERROR,
                f"Error validating output settings: {str(e)}"
            )

    # Smart validation methods for better user guidance
    def smart_validate_basic_info(self):
        """Smart validation for basic information step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if self.config:
                # Check if basic info is filled
                has_description = bool(self.config.description and self.config.description.strip())
                has_version = bool(self.config.version)
                
                if has_description and has_version:
                    update_step_feedback(
                        WorkflowStep.BASIC_INFO,
                        ValidationLevel.SUCCESS,
                        "Basic Information Complete",
                        f"Project configured: {self.config.description or 'Unnamed project'}",
                        completion_percentage=100
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.BASIC_INFO,
                        ValidationLevel.INFO,
                        "Basic Information",
                        "Project metadata can be configured in the Basic tab",
                        "Add a description and version for better organization",
                        completion_percentage=50
                    )
            else:
                update_step_feedback(
                    WorkflowStep.BASIC_INFO,
                    ValidationLevel.ERROR,
                    "Configuration Missing",
                    "No configuration available",
                    "Please restart the application if this error persists"
                )
        except Exception as e:
            debug(f"Error in smart basic info validation: {e}")

    def smart_validate_ephemeris_loading(self):
        """Smart validation for ephemeris loading step."""
        try:
            from core.workflow.smart_workflow import update_step_feedback
            
            if self.config.ephemeris and len(self.config.ephemeris) > 0:
                valid_files = 0
                total_files = len(self.config.ephemeris)
                
                for eph_config in self.config.ephemeris:
                    if os.path.exists(eph_config.name):
                        valid_files += 1
                
                if valid_files == total_files:
                    update_step_feedback(
                        WorkflowStep.EPHEMERIS_LOADING,
                        ValidationLevel.SUCCESS,
                        "Ephemeris Files Loaded",
                        f"All {total_files} ephemeris file(s) are accessible",
                        "Ready for time validation",
                        completion_percentage=100
                    )
                elif valid_files > 0:
                    update_step_feedback(
                        WorkflowStep.EPHEMERIS_LOADING,
                        ValidationLevel.WARNING,
                        "Some Ephemeris Files Missing",
                        f"{valid_files}/{total_files} ephemeris files found",
                        "Check file paths in the Ephemeris & Time tab",
                        completion_percentage=int((valid_files / total_files) * 100)
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.EPHEMERIS_LOADING,
                        ValidationLevel.ERROR,
                        "Ephemeris Files Not Found",
                        "None of the specified ephemeris files could be found",
                        "Check file paths and ensure files exist",
                        completion_percentage=20
                    )
            else:
                update_step_feedback(
                    WorkflowStep.EPHEMERIS_LOADING,
                    ValidationLevel.INCOMPLETE,
                    "No Ephemeris Files",
                    "Load RINEX ephemeris files to begin simulation",
                    "Go to Ephemeris & Time tab and add ephemeris files",
                    completion_percentage=0
                )
        except Exception as e:
            debug(f"Error in smart ephemeris validation: {e}")

    def smart_validate_time_configuration(self):
        """Smart validation for time configuration step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if hasattr(self.ephemeris_time_tab, 'ephemeris_file_ranges') and self.ephemeris_time_tab.ephemeris_file_ranges:
                # Trigger time validation in the tab
                self.ephemeris_time_tab.validate_current_time()
                
                # Check the validation result
                status_text = self.ephemeris_time_tab.time_status_label.text()
                if "VALID" in status_text:
                    update_step_feedback(
                        WorkflowStep.TIME_VALIDATION,
                        ValidationLevel.SUCCESS,
                        "Time Configuration Valid",
                        "Simulation time is within ephemeris validity range",
                        "Ready to configure trajectory",
                        completion_percentage=100
                    )
                elif "INVALID" in status_text:
                    update_step_feedback(
                        WorkflowStep.TIME_VALIDATION,
                        ValidationLevel.ERROR,
                        "Time Outside Valid Range",
                        "Simulation time is outside ephemeris validity range",
                        "Adjust time in Ephemeris & Time tab or load different ephemeris",
                        completion_percentage=50
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.TIME_VALIDATION,
                        ValidationLevel.WARNING,
                        "Time Validation Pending",
                        "Time validation in progress",
                        "Check the Ephemeris & Time tab for details",
                        completion_percentage=25
                    )
            else:
                update_step_feedback(
                    WorkflowStep.TIME_VALIDATION,
                    ValidationLevel.INCOMPLETE,
                    "Ephemeris Required",
                    "Load ephemeris files before configuring time",
                    "Complete ephemeris loading first",
                    completion_percentage=0
                )
        except Exception as e:
            debug(f"Error in smart time validation: {e}")

    def smart_validate_trajectory_configuration(self):
        """Smart validation for trajectory configuration step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if hasattr(self.config.trajectory, 'trajectory_list') and self.config.trajectory.trajectory_list:
                segment_count = len(self.config.trajectory.trajectory_list)
                update_step_feedback(
                    WorkflowStep.TRAJECTORY_CONFIG,
                    ValidationLevel.SUCCESS,
                    "Dynamic Trajectory Configured",
                    f"Trajectory with {segment_count} segment(s) defined",
                    "Ready for signal selection",
                    completion_percentage=100
                )
            else:
                # Check if we have initial position configured
                if (hasattr(self.config.trajectory, 'init_position') and 
                    self.config.trajectory.init_position):
                    update_step_feedback(
                        WorkflowStep.TRAJECTORY_CONFIG,
                        ValidationLevel.SUCCESS,
                        "Static Trajectory Configured",
                        "Receiver position is set for static simulation",
                        "Add trajectory segments for dynamic simulation if needed",
                        completion_percentage=100
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.TRAJECTORY_CONFIG,
                        ValidationLevel.INFO,
                        "Default Trajectory",
                        "Using default trajectory configuration",
                        "Configure custom trajectory in the Trajectory tab if needed",
                        completion_percentage=80
                    )
        except Exception as e:
            debug(f"Error in smart trajectory validation: {e}")

    def smart_validate_signal_selection(self):
        """Smart validation for signal selection step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if self.config.output.system_select:
                enabled_signals = [s for s in self.config.output.system_select if s.enable]
                total_signals = len(self.config.output.system_select)
                
                if enabled_signals:
                    # Group by constellation
                    constellations = set(s.system for s in enabled_signals)
                    constellation_names = [c.value for c in constellations]
                    
                    update_step_feedback(
                        WorkflowStep.SIGNAL_SELECTION,
                        ValidationLevel.SUCCESS,
                        "Signals Selected",
                        f"{len(enabled_signals)} signals from {', '.join(constellation_names)}",
                        "Ready for power configuration",
                        completion_percentage=100
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.SIGNAL_SELECTION,
                        ValidationLevel.WARNING,
                        "No Signals Selected",
                        f"0/{total_signals} available signals enabled",
                        "Select signals in the Signal Selection tab",
                        completion_percentage=20
                    )
            else:
                update_step_feedback(
                    WorkflowStep.SIGNAL_SELECTION,
                    ValidationLevel.INCOMPLETE,
                    "Signal Selection Not Configured",
                    "No signal selection configuration found",
                    "Configure signals in the Signal Selection tab",
                    completion_percentage=0
                )
        except Exception as e:
            debug(f"Error in smart signal selection validation: {e}")

    def smart_validate_power_configuration(self):
        """Smart validation for power configuration step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if self.config.power:
                has_noise_floor = hasattr(self.config.power, 'noise_floor') and self.config.power.noise_floor is not None
                has_init_power = hasattr(self.config.power, 'init_power') and self.config.power.init_power is not None
                
                if has_noise_floor and has_init_power:
                    update_step_feedback(
                        WorkflowStep.POWER_CONFIG,
                        ValidationLevel.SUCCESS,
                        "Power Configuration Complete",
                        f"Noise floor: {self.config.power.noise_floor} dBm/Hz",
                        "Ready for output configuration",
                        completion_percentage=100
                    )
                else:
                    update_step_feedback(
                        WorkflowStep.POWER_CONFIG,
                        ValidationLevel.INFO,
                        "Basic Power Configuration",
                        "Using default power settings",
                        "Customize power settings in the Signal Power tab if needed",
                        completion_percentage=80
                    )
            else:
                update_step_feedback(
                    WorkflowStep.POWER_CONFIG,
                    ValidationLevel.INFO,
                    "Default Power Settings",
                    "Using default power configuration",
                    "Configure custom power settings in the Signal Power tab if needed",
                    completion_percentage=70
                )
        except Exception as e:
            debug(f"Error in smart power validation: {e}")

    def smart_validate_output_settings(self):
        """Smart validation for output settings step."""
        try:
            from ..core.workflow.smart_workflow import update_step_feedback
            
            if self.config.output and self.config.output.name:
                output_name = self.config.output.name
                output_type = getattr(self.config.output, 'type', 'Unknown')
                
                update_step_feedback(
                    WorkflowStep.OUTPUT_SETTINGS,
                    ValidationLevel.SUCCESS,
                    "Output Configuration Complete",
                    f"Output: {os.path.basename(output_name)} ({output_type})",
                    "Configuration is ready for signal generation!",
                    completion_percentage=100
                )
            else:
                update_step_feedback(
                    WorkflowStep.OUTPUT_SETTINGS,
                    ValidationLevel.INCOMPLETE,
                    "Output File Not Specified",
                    "No output file configured",
                    "Set output file in the Output Settings tab",
                    completion_percentage=0
                )
        except Exception as e:
            debug(f"Error in smart output validation: {e}")
