"""
Output Settings Tab

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This tab handles output file configuration settings,
with signal selection moved to its own dedicated tab.
"""

import os
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QDoubleSpinBox,
    QPushButton,
    QFileDialog,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QCheckBox,
)
from PyQt6.QtCore import pyqtSignal
from core.config.models import GNSSSignalSimConfig, OutputType, OutputFormat
from core.utils.settings import get_default_path


class OutputSettingsTab(QWidget):
    """Output file settings configuration tab."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Output File Configuration Group
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

        # Output type selection
        type_layout = QHBoxLayout()
        self.output_type_combo = QComboBox()
        for output_type in OutputType:
            self.output_type_combo.addItem(output_type.value, output_type)
        self.output_type_combo.setMaximumWidth(150)
        type_layout.addWidget(self.output_type_combo)
        type_layout.addStretch()
        file_layout.addRow("Output Type:", type_layout)


        layout.addWidget(file_group)

        # IF Data Settings Group
        self.ifdata_group = QGroupBox("IF Data Settings")
        self.ifdata_group.setStyleSheet("""
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
        ifdata_layout = QFormLayout(self.ifdata_group)

        # Format selection
        format_layout = QHBoxLayout()
        self.output_format_combo = QComboBox()
        for output_format in OutputFormat:
            self.output_format_combo.addItem(output_format.value, output_format)
        self.output_format_combo.setMaximumWidth(120)
        format_layout.addWidget(self.output_format_combo)
        format_layout.addStretch()
        ifdata_layout.addRow("Format:", format_layout)

        # Sample frequency
        sample_freq_layout = QHBoxLayout()
        self.sample_freq_spin = QDoubleSpinBox()
        self.sample_freq_spin.setRange(1.0, 100.0)
        self.sample_freq_spin.setDecimals(1)
        self.sample_freq_spin.setSuffix(" MHz")
        self.sample_freq_spin.setValue(20.0)
        self.sample_freq_spin.setMaximumWidth(120)
        sample_freq_layout.addWidget(self.sample_freq_spin)
        sample_freq_layout.addWidget(QLabel("(sampling frequency for IF data generation)"))
        sample_freq_layout.addStretch()
        ifdata_layout.addRow("Sample Frequency:", sample_freq_layout)

        # Center frequency
        center_freq_layout = QHBoxLayout()
        self.center_freq_spin = QDoubleSpinBox()
        self.center_freq_spin.setRange(1000.0, 2000.0)
        self.center_freq_spin.setDecimals(2)
        self.center_freq_spin.setSuffix(" MHz")
        self.center_freq_spin.setValue(1575.42)
        self.center_freq_spin.setMaximumWidth(120)
        center_freq_layout.addWidget(self.center_freq_spin)
        center_freq_layout.addWidget(QLabel("(center frequency for IF data generation)"))
        center_freq_layout.addStretch()
        ifdata_layout.addRow("Center Frequency:", center_freq_layout)

        layout.addWidget(self.ifdata_group)

        # Position/Observation Settings Group
        self.pos_obs_group = QGroupBox("Position/Observation Settings")
        self.pos_obs_group.setStyleSheet("""
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
        pos_obs_layout = QFormLayout(self.pos_obs_group)

        # Output interval
        interval_layout = QHBoxLayout()
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.001, 3600.0)
        self.interval_spin.setDecimals(3)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setValue(1.0)
        self.interval_spin.setMaximumWidth(120)
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addWidget(QLabel("(output interval for position/observation data)"))
        interval_layout.addStretch()
        pos_obs_layout.addRow("Interval:", interval_layout)

        layout.addWidget(self.pos_obs_group)

        # Additional Outputs Group
        additional_group = QGroupBox("Additional Outputs")
        additional_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #17a2b8;
            }
        """)
        additional_layout = QVBoxLayout(additional_group)

        self.position_output_check = QCheckBox("Position Output (NMEA/KML)")
        self.position_output_check.setToolTip("Generate position output in NMEA or KML format")
        additional_layout.addWidget(self.position_output_check)

        self.observation_output_check = QCheckBox("Observation Output (RINEX)")
        self.observation_output_check.setToolTip("Generate observation output in RINEX format")
        additional_layout.addWidget(self.observation_output_check)

        self.almanac_output_check = QCheckBox("Almanac Output")
        self.almanac_output_check.setToolTip("Generate almanac data output")
        additional_layout.addWidget(self.almanac_output_check)

        layout.addWidget(additional_group)

        # Output Summary Group
        summary_group = QGroupBox("Output Summary")
        summary_group.setStyleSheet("""
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
        summary_layout = QVBoxLayout(summary_group)

        self.summary_label = QLabel("Configure output settings above")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #343a40;
                color: #f8f9fa;
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        summary_layout.addWidget(self.summary_label)

        layout.addWidget(summary_group)

        # Add spacer
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        layout.addItem(spacer)

        # Initially update UI based on output type
        self.update_output_type_visibility()

    def connect_signals(self):
        """Connect widget signals."""
        self.output_type_combo.currentTextChanged.connect(self.on_output_type_changed)
        self.output_format_combo.currentTextChanged.connect(self.update_config)
        self.sample_freq_spin.valueChanged.connect(self.update_config)
        self.center_freq_spin.valueChanged.connect(self.update_config)
        self.interval_spin.valueChanged.connect(self.update_config)
        self.position_output_check.stateChanged.connect(self.update_config)
        self.observation_output_check.stateChanged.connect(self.update_config)
        self.almanac_output_check.stateChanged.connect(self.update_config)


    def on_output_type_changed(self):
        """Handle output type change."""
        self.update_output_type_visibility()
        self.update_format_options()
        self.update_config()

    def update_output_type_visibility(self):
        """Update widget visibility based on output type."""
        output_type = self.output_type_combo.currentData()

        if output_type == OutputType.IF_DATA:
            self.ifdata_group.setVisible(True)
            self.pos_obs_group.setVisible(False)
        elif output_type in [OutputType.POSITION, OutputType.OBSERVATION]:
            self.ifdata_group.setVisible(False)
            self.pos_obs_group.setVisible(True)
        else:
            self.ifdata_group.setVisible(False)
            self.pos_obs_group.setVisible(False)

    def update_format_options(self):
        """Update format options based on output type."""
        output_type = self.output_type_combo.currentData()
        
        # Block signals to prevent recursive updates
        self.output_format_combo.blockSignals(True)
        
        # Clear and repopulate format options
        self.output_format_combo.clear()
        
        if output_type == OutputType.IF_DATA:
            formats = [OutputFormat.IQ8, OutputFormat.IQ4]
        elif output_type == OutputType.POSITION:
            formats = [OutputFormat.KML, OutputFormat.NMEA0183]
        elif output_type == OutputType.OBSERVATION:
            formats = [OutputFormat.RINEX3]
        else:
            formats = list(OutputFormat)
        
        for fmt in formats:
            self.output_format_combo.addItem(fmt.value, fmt)
        
        # Select first option if available
        if self.output_format_combo.count() > 0:
            self.output_format_combo.setCurrentIndex(0)
        
        self.output_format_combo.blockSignals(False)

    def update_summary(self):
        """Update the output summary display."""
        output_type = self.output_type_combo.currentData()
        output_format = self.output_format_combo.currentData()
        
        summary_parts = []
        
        # Primary output configuration
        summary_parts.append(f"Output Type: {output_type.value if output_type else 'Not set'}")
        summary_parts.append(f"Format: {output_format.value if output_format else 'Not set'}")
        summary_parts.append("File location: Configured in Generate tab")
        
        # Type-specific settings
        if output_type == OutputType.IF_DATA:
            summary_parts.append(f"Sample Rate: {self.sample_freq_spin.value()} MHz")
            summary_parts.append(f"Center Freq: {self.center_freq_spin.value()} MHz")
        elif output_type in [OutputType.POSITION, OutputType.OBSERVATION]:
            summary_parts.append(f"Interval: {self.interval_spin.value()} seconds")
        
        # Additional outputs
        additional_outputs = []
        if self.position_output_check.isChecked():
            additional_outputs.append("Position (NMEA/KML)")
        if self.observation_output_check.isChecked():
            additional_outputs.append("Observation (RINEX)")
        if self.almanac_output_check.isChecked():
            additional_outputs.append("Almanac")
        
        if additional_outputs:
            summary_parts.append(f"Additional: {', '.join(additional_outputs)}")
        
        summary_text = "\n".join(summary_parts)
        self.summary_label.setText(summary_text)

    def update_config(self):
        """Update configuration from widget values."""
        # Update primary output settings
        self.config.output.type = self.output_type_combo.currentData()
        self.config.output.format = self.output_format_combo.currentData()
        
        # Note: output.name is now managed by the Generate tab
        
        # Update type-specific settings
        self.config.output.sample_freq = self.sample_freq_spin.value()
        self.config.output.center_freq = self.center_freq_spin.value()
        self.config.output.interval = self.interval_spin.value()

        # Update summary
        self.update_summary()
        
        self.config_changed.emit()

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals
        self.output_type_combo.blockSignals(True)
        self.output_format_combo.blockSignals(True)
        self.sample_freq_spin.blockSignals(True)
        self.center_freq_spin.blockSignals(True)
        self.interval_spin.blockSignals(True)
        self.position_output_check.blockSignals(True)
        self.observation_output_check.blockSignals(True)
        self.almanac_output_check.blockSignals(True)

        try:
            # Set output type
            for i in range(self.output_type_combo.count()):
                if self.output_type_combo.itemData(i) == self.config.output.type:
                    self.output_type_combo.setCurrentIndex(i)
                    break

            # Update format options and set format
            self.update_format_options()
            for i in range(self.output_format_combo.count()):
                if self.output_format_combo.itemData(i) == self.config.output.format:
                    self.output_format_combo.setCurrentIndex(i)
                    break

            # Note: File and directory are now managed by Generate tab

            # Set numeric values
            self.sample_freq_spin.setValue(self.config.output.sample_freq)
            self.center_freq_spin.setValue(self.config.output.center_freq)
            self.interval_spin.setValue(self.config.output.interval)

            # Update visibility and summary
            self.update_output_type_visibility()
            self.update_summary()

        finally:
            # Re-enable signals
            self.output_type_combo.blockSignals(False)
            self.output_format_combo.blockSignals(False)
            self.sample_freq_spin.blockSignals(False)
            self.center_freq_spin.blockSignals(False)
            self.interval_spin.blockSignals(False)
            self.position_output_check.blockSignals(False)
            self.observation_output_check.blockSignals(False)
            self.almanac_output_check.blockSignals(False)