"""
Generate Tab for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This tab handles signal generation with IFDataGen integration,
file management, and real-time output display.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QMessageBox, QFileDialog, QSplitter, QScrollArea,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from core.config.models import GNSSSignalSimConfig, OutputType
from core.utils.settings import (
    get_default_path, get_ifdatagen_executable_path, 
    get_generated_output_path, set_ifdatagen_executable_path
)
from core.utils.logger import info, debug, error
from core.integration.ifdatagen import ifdatagen_integration


class GenerateTab(QWidget):
    """Signal generation tab with IFDataGen integration."""

    config_changed = pyqtSignal()
    generation_started = pyqtSignal()
    generation_finished = pyqtSignal(bool, str)

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.current_output_path = ""
        self.generation_in_progress = False
        
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # File Configuration Group
        file_group = QGroupBox("Output File Configuration")
        file_group.setStyleSheet("""
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
            }
        """)
        file_layout = QFormLayout(file_group)

        # File name input
        file_name_layout = QHBoxLayout()
        self.file_name_edit = QLineEdit()
        self.file_name_edit.setPlaceholderText("simulation_output")
        file_name_layout.addWidget(self.file_name_edit)
        
        self.browse_file_button = QPushButton("Browse...")
        self.browse_file_button.clicked.connect(self.browse_output_file)
        self.browse_file_button.setMaximumWidth(100)
        file_name_layout.addWidget(self.browse_file_button)
        
        file_layout.addRow("File Name:", file_name_layout)

        # Full path display
        self.full_path_label = QLabel("Full path will be shown here")
        self.full_path_label.setWordWrap(True)
        self.full_path_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        file_layout.addRow("Full Path:", self.full_path_label)

        layout.addWidget(file_group)

        # IFDataGen Configuration Group
        ifdatagen_group = QGroupBox("IFDataGen Configuration")
        ifdatagen_group.setStyleSheet("""
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
            }
        """)
        ifdatagen_layout = QFormLayout(ifdatagen_group)

        # IFDataGen executable path
        executable_layout = QHBoxLayout()
        self.executable_path_label = QLabel("Executable path will be shown here")
        self.executable_path_label.setWordWrap(True)
        self.executable_path_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)
        executable_layout.addWidget(self.executable_path_label)
        
        self.browse_executable_button = QPushButton("Browse...")
        self.browse_executable_button.clicked.connect(self.browse_executable)
        self.browse_executable_button.setMaximumWidth(100)
        executable_layout.addWidget(self.browse_executable_button)
        
        ifdatagen_layout.addRow("Executable:", executable_layout)

        layout.addWidget(ifdatagen_group)

        # Generation Control Group
        control_group = QGroupBox("Generation Control")
        control_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        control_layout = QVBoxLayout(control_group)

        # Generate button
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate IF Data")
        self.generate_button.clicked.connect(self.generate_signals)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.generate_button)
        button_layout.addStretch()
        
        control_layout.addLayout(button_layout)

        layout.addWidget(control_group)

        # Output Display Group
        output_group = QGroupBox("Generation Output")
        output_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        output_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #6f42c1;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #6f42c1;
            }
        """)
        output_layout = QVBoxLayout(output_group)

        # Output text viewer with controls
        viewer_controls = QHBoxLayout()
        
        self.clear_output_button = QPushButton("Clear")
        self.clear_output_button.clicked.connect(self.clear_output)
        self.clear_output_button.setMaximumWidth(80)
        viewer_controls.addWidget(self.clear_output_button)
        
        self.save_output_button = QPushButton("Save Log")
        self.save_output_button.clicked.connect(self.save_output_log)
        self.save_output_button.setMaximumWidth(80)
        viewer_controls.addWidget(self.save_output_button)
        
        viewer_controls.addStretch()
        
        zoom_label = QLabel("Zoom:")
        viewer_controls.addWidget(zoom_label)
        
        self.zoom_out_button = QPushButton("-")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_out_button.setMaximumWidth(30)
        viewer_controls.addWidget(self.zoom_out_button)
        
        self.zoom_in_button = QPushButton("+")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_in_button.setMaximumWidth(30)
        viewer_controls.addWidget(self.zoom_in_button)
        
        output_layout.addLayout(viewer_controls)

        # Output text viewer
        self.output_viewer = QTextEdit()
        self.output_viewer.setReadOnly(True)
        self.output_viewer.setFont(QFont("Consolas", 9))
        self.output_viewer.setStyleSheet("""
            QTextEdit {
                background-color: #2d3748;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.output_viewer.setMinimumHeight(400)  # Increased minimum height
        self.output_viewer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        output_layout.addWidget(self.output_viewer)

        layout.addWidget(output_group)

        # Set stretch factors to give output group maximum space
        layout.setStretchFactor(file_group, 0)      # Fixed size
        layout.setStretchFactor(ifdatagen_group, 0) # Fixed size  
        layout.setStretchFactor(control_group, 0)   # Fixed size
        layout.setStretchFactor(output_group, 1)    # Takes all remaining space

        # Update initial display
        self.update_path_displays()

    def connect_signals(self):
        """Connect widget signals."""
        self.file_name_edit.textChanged.connect(self.on_file_name_changed)
        
        # Connect IFDataGen integration signals
        ifdatagen_integration.progress_updated.connect(self.on_generation_progress)
        ifdatagen_integration.status_updated.connect(self.on_generation_status)
        ifdatagen_integration.generation_finished.connect(self.on_generation_finished)
        ifdatagen_integration.output_received.connect(self.on_output_received)

    def on_file_name_changed(self):
        """Handle file name changes."""
        self.update_path_displays()
        self.update_generate_button()
        self.update_config()

    def update_path_displays(self):
        """Update the path display labels."""
        filename = self.file_name_edit.text().strip()
        
        if filename:
            # Get output type from config
            output_type = getattr(self.config.output, 'type', OutputType.IF_DATA)
            output_type_str = output_type.value if hasattr(output_type, 'value') else str(output_type)
            
            # Get the full output path (without creating directory)
            self.current_output_path = get_generated_output_path(output_type_str, filename, create_dir=False)
            
            # Add file extension if not present
            if not os.path.splitext(filename)[1]:
                if output_type == OutputType.IF_DATA:
                    filename += ".bin"
                elif output_type == OutputType.POSITION:
                    filename += ".kml"
                elif output_type == OutputType.OBSERVATION:
                    filename += ".obs"
            
            full_file_path = os.path.join(self.current_output_path, filename)
            # Use forward slashes for display
            full_file_path = full_file_path.replace('\\', '/')
            self.full_path_label.setText(full_file_path)
        else:
            self.full_path_label.setText("Enter a file name to see the full path")
            self.current_output_path = ""

        # Update IFDataGen executable path
        executable_path = get_ifdatagen_executable_path()
        if executable_path:
            # Use forward slashes for display
            executable_path = executable_path.replace('\\', '/')
            self.executable_path_label.setText(executable_path)
        else:
            default_path = os.path.join(get_default_path("ifdatagen"), "IFDataGen.exe")
            default_path = default_path.replace('\\', '/')
            self.executable_path_label.setText(f"Not found (expected: {default_path})")

    def update_generate_button(self):
        """Update the generate button text and state."""
        if self.generation_in_progress:
            self.generate_button.setText("Generating...")
            self.generate_button.setEnabled(False)
            return

        # Get output type from config
        output_type = getattr(self.config.output, 'type', OutputType.IF_DATA)
        
        if output_type == OutputType.IF_DATA:
            button_text = "Generate IF Data"
        elif output_type == OutputType.POSITION:
            button_text = "Generate Position"
        elif output_type == OutputType.OBSERVATION:
            button_text = "Generate Observation"
        else:
            button_text = "Generate Output"
        
        self.generate_button.setText(button_text)
        
        # Enable button only if we have a filename and executable
        filename = self.file_name_edit.text().strip()
        executable_available = get_ifdatagen_executable_path() is not None
        self.generate_button.setEnabled(bool(filename and executable_available))

    def browse_output_file(self):
        """Browse for output file location."""
        # Use the base generated path for browsing, not the specific output path
        base_path = get_default_path("generated")
        
        # Get file filter based on output type
        output_type = getattr(self.config.output, 'type', OutputType.IF_DATA)
        
        if output_type == OutputType.IF_DATA:
            file_filter = "Binary Signal Files (*.bin);;All Files (*)"
            default_name = "simulation_output.bin"
        elif output_type == OutputType.POSITION:
            file_filter = "Position Files (*.kml *.nmea);;All Files (*)"
            default_name = "position_output.kml"
        elif output_type == OutputType.OBSERVATION:
            file_filter = "RINEX Files (*.obs *.rnx);;All Files (*)"
            default_name = "observation_output.obs"
        else:
            file_filter = "All Files (*)"
            default_name = "output"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", 
            os.path.join(base_path, default_name), 
            file_filter
        )

        if file_path:
            filename = os.path.basename(file_path)
            # Remove extension for the filename field
            name_without_ext = os.path.splitext(filename)[0]
            self.file_name_edit.setText(name_without_ext)

    def browse_executable(self):
        """Browse for IFDataGen executable."""
        current_path = get_ifdatagen_executable_path() or get_default_path("ifdatagen")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select IFDataGen Executable", 
            current_path, 
            "Executable Files (*.exe);;All Files (*)"
        )

        if file_path:
            if set_ifdatagen_executable_path(file_path):
                self.update_path_displays()
                self.update_generate_button()
                info(f"IFDataGen executable path updated: {file_path}")
            else:
                QMessageBox.warning(
                    self, "Invalid Executable", 
                    "The selected file does not exist or is not accessible."
                )

    def generate_signals(self):
        """Start signal generation process."""
        if self.generation_in_progress:
            return

        filename = self.file_name_edit.text().strip()
        if not filename:
            QMessageBox.warning(self, "Missing Filename", "Please enter a filename for the output.")
            return

        executable_path = get_ifdatagen_executable_path()
        if not executable_path:
            QMessageBox.warning(
                self, "IFDataGen Not Found", 
                "IFDataGen executable not found. Please set the correct path in preferences or browse for it."
            )
            return

        # Now create the output directory (first time)
        output_type = getattr(self.config.output, 'type', OutputType.IF_DATA)
        output_type_str = output_type.value if hasattr(output_type, 'value') else str(output_type)
        self.current_output_path = get_generated_output_path(output_type_str, filename, create_dir=True)

        # Check if output directory already exists and warn user
        if os.path.exists(self.current_output_path) and os.listdir(self.current_output_path):
            reply = QMessageBox.question(
                self, "Directory Exists", 
                f"The output directory already exists and contains files:\n{self.current_output_path}\n\n"
                "Do you want to continue? Existing files may be overwritten.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Update config with current filename
        self.update_config()

        # Clear output viewer
        self.output_viewer.clear()
        self.append_output("Starting signal generation...\n")
        self.append_output(f"Output directory: {self.current_output_path}\n")

        # Set generation state
        self.generation_in_progress = True
        self.update_generate_button()
        self.generation_started.emit()

        # Start generation
        success = ifdatagen_integration.generate_signals(self.config, self.current_output_path)
        if not success:
            self.generation_in_progress = False
            self.update_generate_button()
            self.append_output("Failed to start signal generation.\n")

    def on_generation_progress(self, progress):
        """Handle generation progress updates."""
        self.append_output(f"Progress: {progress}%\n")

    def on_generation_status(self, status):
        """Handle generation status updates."""
        self.append_output(f"Status: {status}\n")

    def on_generation_finished(self, success, message):
        """Handle generation completion."""
        self.generation_in_progress = False
        self.update_generate_button()
        
        if success:
            self.append_output(f"\n✓ Generation completed successfully!\n{message}\n")
            info("Signal generation completed successfully")
        else:
            self.append_output(f"\n✗ Generation failed!\n{message}\n")
            error(f"Signal generation failed: {message}")
        
        self.generation_finished.emit(success, message)

    def on_output_received(self, output):
        """Handle real-time output from IFDataGen."""
        self.append_output(output)

    def append_output(self, text):
        """Append text to the output viewer."""
        self.output_viewer.append(text.rstrip())
        # Auto-scroll to bottom
        cursor = self.output_viewer.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_viewer.setTextCursor(cursor)

    def clear_output(self):
        """Clear the output viewer."""
        self.output_viewer.clear()

    def save_output_log(self):
        """Save the output log to a file."""
        if not self.output_viewer.toPlainText():
            QMessageBox.information(self, "No Output", "There is no output to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output Log", 
            os.path.join(get_default_path("generated"), "generation_log.txt"),
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.output_viewer.toPlainText())
                QMessageBox.information(self, "Log Saved", f"Output log saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save log:\n{str(e)}")

    def zoom_in(self):
        """Increase font size in output viewer."""
        font = self.output_viewer.font()
        size = font.pointSize()
        if size < 20:
            font.setPointSize(size + 1)
            self.output_viewer.setFont(font)

    def zoom_out(self):
        """Decrease font size in output viewer."""
        font = self.output_viewer.font()
        size = font.pointSize()
        if size > 6:
            font.setPointSize(size - 1)
            self.output_viewer.setFont(font)

    def update_config(self):
        """Update configuration from widget values."""
        filename = self.file_name_edit.text().strip()
        if filename:
            # Get output type and add appropriate extension
            output_type = getattr(self.config.output, 'type', OutputType.IF_DATA)
            
            if not os.path.splitext(filename)[1]:
                if output_type == OutputType.IF_DATA:
                    filename += ".bin"
                elif output_type == OutputType.POSITION:
                    filename += ".kml"
                elif output_type == OutputType.OBSERVATION:
                    filename += ".obs"
            
            # Set only the filename in config (not full path)
            self.config.output.name = filename
            
        self.config_changed.emit()

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals during refresh
        self.file_name_edit.blockSignals(True)
        
        try:
            # Extract filename from config
            if self.config.output.name:
                # Config should already contain just filename, but ensure we get basename
                filename = os.path.basename(self.config.output.name)
                # Remove extension for display
                name_without_ext = os.path.splitext(filename)[0]
                self.file_name_edit.setText(name_without_ext)
            
            # Update displays
            self.update_path_displays()
            self.update_generate_button()
            
        finally:
            # Re-enable signals
            self.file_name_edit.blockSignals(False)