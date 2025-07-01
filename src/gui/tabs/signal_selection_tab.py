"""
Signal Selection Tab

This tab handles constellation and signal selection configuration,
separated from output settings for better workflow organization.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QCheckBox,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QDoubleSpinBox,
    QFormLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.config.models import GNSSSignalSimConfig, SystemSelect, ConstellationType, OutputConfig
from core.utils.logger import debug


class SignalSelectionTab(QWidget):
    """Signal selection and constellation configuration tab."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.signal_definitions = self._get_signal_definitions()
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def _get_signal_definitions(self):
        """Define available signals for each constellation with bandwidth information."""
        return {
            ConstellationType.GPS: [
                ("L1CA", "1575.42 MHz", "2.046 MHz", "Coarse/Acquisition"),
                ("L1C", "1575.42 MHz", "4.092 MHz", "Civilian"),
                ("L2C", "1227.60 MHz", "2.046 MHz", "Civilian"),
                ("L2P", "1227.60 MHz", "20.46 MHz", "Precision"),
                ("L5", "1176.45 MHz", "24.552 MHz", "Safety of Life"),
            ],
            ConstellationType.BDS: [
                ("B1C", "1575.42 MHz", "32.736 MHz", "Civil Navigation"),
                ("B1I", "1561.098 MHz", "4.092 MHz", "Open Service"),
                ("B2I", "1207.14 MHz", "4.092 MHz", "Open Service"),
                ("B3I", "1268.52 MHz", "20.46 MHz", "Open Service"),
                ("B2a", "1176.45 MHz", "20.46 MHz", "Civil Navigation"),
                # B2b removed (not in SignalSim)
            ],
            ConstellationType.GALILEO: [
                ("E1", "1575.42 MHz", "24.552 MHz", "Open Service"),
                ("E5a", "1176.45 MHz", "20.46 MHz", "Open Service"),
                ("E5b", "1207.14 MHz", "20.46 MHz", "Open Service"),
                ("E5", "1191.795 MHz", "51.15 MHz", "AltBOC"),
                ("E6", "1278.75 MHz", "40.92 MHz", "Commercial Service"),
            ],
            ConstellationType.GLONASS: [
                ("G1", "1602.0 MHz", "4.092 MHz", "Standard Precision"),
                ("G2", "1246.0 MHz", "4.092 MHz", "Standard Precision"),
            ],
        }

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Constellation & Signal Selection Group
        selection_group = QGroupBox("Constellation & Signal Selection")
        selection_group.setStyleSheet("""
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
        selection_layout = QVBoxLayout(selection_group)

        # Signal selection table
        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(6)
        self.signal_table.setHorizontalHeaderLabels([
            "System", "Signal", "Frequency", "Bandwidth", "Description", "Enable"
        ])
        
        # Set column widths
        header = self.signal_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        self.signal_table.setColumnWidth(0, 80)   # System
        self.signal_table.setColumnWidth(1, 80)   # Signal
        self.signal_table.setColumnWidth(2, 100)  # Frequency
        self.signal_table.setColumnWidth(3, 100)  # Bandwidth
        self.signal_table.setColumnWidth(5, 70)   # Enable

        self.signal_table.setMinimumHeight(300)
        self.signal_table.setMaximumHeight(400)
        self.signal_table.setAlternatingRowColors(True)
        
        selection_layout.addWidget(self.signal_table)

        # Quick selection buttons
        button_layout = QHBoxLayout()
        
        self.toggle_selection_button = QPushButton("Select All")
        self.toggle_selection_button.clicked.connect(self.toggle_all_signals)
        button_layout.addWidget(self.toggle_selection_button)

        # Preset selection (REMOVED)

        button_layout.addStretch()
        selection_layout.addLayout(button_layout)

        layout.addWidget(selection_group)

        # Satellite Masking Group
        masking_group = QGroupBox("Satellite Masking Configuration")
        masking_group.setStyleSheet("""
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
        masking_layout = QFormLayout(masking_group)

        # Elevation mask
        elevation_layout = QHBoxLayout()
        self.elevation_spin = QDoubleSpinBox()
        self.elevation_spin.setRange(0.0, 90.0)
        self.elevation_spin.setValue(5.0)
        self.elevation_spin.setSuffix("°")
        self.elevation_spin.setMaximumWidth(100)
        elevation_layout.addWidget(self.elevation_spin)
        elevation_layout.addWidget(QLabel("(satellites below this elevation will be masked)"))
        elevation_layout.addStretch()
        masking_layout.addRow("Elevation Mask:", elevation_layout)

        # Masked satellites configuration
        masked_layout = QHBoxLayout()
        self.configure_masked_button = QPushButton("Configure Masked Satellites...")
        self.configure_masked_button.clicked.connect(self.configure_masked_satellites)
        masked_layout.addWidget(self.configure_masked_button)
        
        self.masked_count_label = QLabel("0 satellites manually masked")
        self.masked_count_label.setStyleSheet("color: #666;")
        masked_layout.addWidget(self.masked_count_label)
        masked_layout.addStretch()
        masking_layout.addRow("Manual Masking:", masked_layout)

        layout.addWidget(masking_group)

        # Selection Summary Group
        summary_group = QGroupBox("Selection Summary")
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

        self.summary_label = QLabel("No signals selected")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("""
            QLabel {
                background-color: #343a40;
                color: #f8f9fa;
                padding: 15px;
                border: 1px solid #f8f9fa;
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

        # Populate the signal table
        self.populate_signal_table()

    def populate_signal_table(self):
        """Populate the signal selection table with all available signals."""
        row = 0
        total_rows = sum(len(signals) for signals in self.signal_definitions.values())
        self.signal_table.setRowCount(total_rows)

        for constellation, signals in self.signal_definitions.items():
            for signal_name, frequency, bandwidth, description in signals:
                # System column
                system_item = QTableWidgetItem(constellation.value)
                system_item.setFlags(system_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signal_table.setItem(row, 0, system_item)

                # Signal column
                signal_item = QTableWidgetItem(signal_name)
                signal_item.setFlags(signal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signal_table.setItem(row, 1, signal_item)

                # Frequency column
                freq_item = QTableWidgetItem(frequency)
                freq_item.setFlags(freq_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signal_table.setItem(row, 2, freq_item)

                # Bandwidth column
                bandwidth_item = QTableWidgetItem(bandwidth)
                bandwidth_item.setFlags(bandwidth_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signal_table.setItem(row, 3, bandwidth_item)

                # Description column
                desc_item = QTableWidgetItem(description)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.signal_table.setItem(row, 4, desc_item)

                # Enable checkbox
                enable_checkbox = QCheckBox()
                enable_checkbox.setStyleSheet("""
                    QCheckBox::indicator:checked {
                        background-color: #6f42c1;
                        border: 1px solid #6f42c1;
                        border-radius: 4px;
                    }
                """)
                enable_checkbox.setChecked(False)
                enable_checkbox.stateChanged.connect(
                    lambda state, r=row: self.on_signal_toggled(r, state)
                )
                self.signal_table.setCellWidget(row, 5, enable_checkbox)

                row += 1

    def connect_signals(self):
        """Connect widget signals."""
        self.elevation_spin.valueChanged.connect(self.update_config)

    def toggle_all_signals(self):
        """Toggle selecting or deselecting all signals."""
        # Determine if we are selecting or deselecting based on button text
        select = self.toggle_selection_button.text() == "Select All"

        for row in range(self.signal_table.rowCount()):
            checkbox = self.signal_table.cellWidget(row, 5)
            if checkbox:
                # Block signals to avoid triggering on_signal_selection_changed for each row
                checkbox.blockSignals(True)
                checkbox.setChecked(select)
                checkbox.blockSignals(False)
        
        # Manually trigger the update once after all changes are made
        self.on_signal_selection_changed()

    def on_signal_toggled(self, row, state):
        """Handle a single signal checkbox being toggled."""
        is_checked = (state == Qt.CheckState.Checked.value)
        system_text = self.signal_table.item(row, 0).text()
        signal_text = self.signal_table.item(row, 1).text()

        # Find the signal in the config list
        found_item = None
        for item in self.config.output.system_select:
            if item.system.value == system_text and item.signal == signal_text:
                found_item = item
                break
        
        if is_checked and not found_item:
            # Add to config
            try:
                system_enum = ConstellationType(system_text)
                new_selection = SystemSelect(
                    system=system_enum,
                    signal=signal_text,
                    enable=True
                )
                self.config.output.system_select.append(new_selection)
            except ValueError:
                debug(f"Unknown constellation type: {system_text}")
        elif not is_checked and found_item:
            # Remove from config
            self.config.output.system_select.remove(found_item)

        # Now run the updates. We no longer need to call update_config() here.
        self.update_selection_summary()
        self.update_toggle_button_state()
        self.config_changed.emit()

    def on_signal_selection_changed(self):
        """Handle signal selection changes."""
        # self.preset_combo.setCurrentText("Custom") # No longer exists
        self.update_selection_summary()
        self.update_config()
        self.update_toggle_button_state()

    def update_toggle_button_state(self):
        """Update the text of the toggle button based on selection state."""
        for row in range(self.signal_table.rowCount()):
            checkbox = self.signal_table.cellWidget(row, 5)
            if checkbox and not checkbox.isChecked():
                self.toggle_selection_button.setText("Select All")
                return
        self.toggle_selection_button.setText("Deselect All")

    def update_selection_summary(self):
        """Update the selection summary display."""
        selected_signals = []
        constellation_counts = {}

        for row in range(self.signal_table.rowCount()):
            checkbox = self.signal_table.cellWidget(row, 5)
            if checkbox and checkbox.isChecked():
                system = self.signal_table.item(row, 0).text()
                signal = self.signal_table.item(row, 1).text()
                frequency = self.signal_table.item(row, 2).text()
                bandwidth = self.signal_table.item(row, 3).text()
                
                selected_signals.append(f"{system} {signal} ({frequency}, BW: {bandwidth})")
                
                if system not in constellation_counts:
                    constellation_counts[system] = 0
                constellation_counts[system] += 1

        if not selected_signals:
            summary_text = "No signals selected"
        else:
            summary_text = f"Selected {len(selected_signals)} signal(s):\n\n"
            
            # Group by constellation
            for constellation, count in constellation_counts.items():
                summary_text += f"• {constellation}: {count} signal(s)\n"
            
            summary_text += f"\nElevation mask: {self.elevation_spin.value()}°"
            
            # Add masked satellites info if any
            masked_count = len(getattr(self.config.output.config, 'mask_out', []))
            if masked_count > 0:
                summary_text += f"\nManually masked satellites: {masked_count}"

        self.summary_label.setText(summary_text)

    def configure_masked_satellites(self):
        """Open dialog to configure manually masked satellites."""
        from gui.dialogs.masked_satellite_dialog import MaskedSatelliteDialog
        
        # Get current masks
        current_masks = getattr(self.config.output.config, 'mask_out', [])
        
        # Open dialog
        dialog = MaskedSatelliteDialog(self, current_masks)
        dialog.satellites_updated.connect(self.on_masked_satellites_updated)
        dialog.exec()

    def on_masked_satellites_updated(self, masks):
        """Handle updated masked satellites."""
        # Ensure config has mask_out attribute
        if not hasattr(self.config.output.config, 'mask_out'):
            self.config.output.config.mask_out = []
        
        # Update configuration
        self.config.output.config.mask_out = masks
        
        # Update display
        self.update_selection_summary()
        self.update_config()

    def update_config(self):
        """Update configuration from widget values."""
        # Update system select configuration
        system_select = []
        
        for row in range(self.signal_table.rowCount()):
            checkbox = self.signal_table.cellWidget(row, 5)
            if checkbox and checkbox.isChecked():
                system_text = self.signal_table.item(row, 0).text()
                signal_text = self.signal_table.item(row, 1).text()
                
                # Convert text to enum
                try:
                    system_enum = ConstellationType(system_text)
                    system_select.append(SystemSelect(
                        system=system_enum,
                        signal=signal_text,
                        enable=True
                    ))
                except ValueError:
                    debug(f"Unknown constellation type: {system_text}")

        self.config.output.system_select = system_select

        # Update elevation mask
        if not hasattr(self.config.output, 'config') or self.config.output.config is None:
            self.config.output.config = OutputConfig()
        
        self.config.output.config.elevation_mask = self.elevation_spin.value()

        # Update summary
        self.update_selection_summary()
        
        # Update masked satellites count
        masked_count = len(getattr(self.config.output.config, 'mask_out', []))
        self.masked_count_label.setText(f"{masked_count} satellites manually masked")

        self.config_changed.emit()

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals
        self.elevation_spin.blockSignals(True)

        try:
            # Set elevation mask
            if (hasattr(self.config.output, 'config') and 
                self.config.output.config and 
                hasattr(self.config.output.config, 'elevation_mask')):
                self.elevation_spin.setValue(self.config.output.config.elevation_mask)

            # Set signal selections
            enabled_signals = set()
            for system_config in self.config.output.system_select:
                if system_config.enable:
                    enabled_signals.add((system_config.system.value, system_config.signal))

            # Update checkboxes
            for row in range(self.signal_table.rowCount()):
                system = self.signal_table.item(row, 0).text()
                signal = self.signal_table.item(row, 1).text()
                checkbox = self.signal_table.cellWidget(row, 5)
                
                if checkbox:
                    checkbox.blockSignals(True)
                    checkbox.setChecked((system, signal) in enabled_signals)
                    checkbox.blockSignals(False)

            # Update summary and masked count
            self.update_selection_summary()
            masked_count = len(getattr(self.config.output.config, 'mask_out', []))
            self.masked_count_label.setText(f"{masked_count} satellites manually masked")
            self.update_toggle_button_state()

        finally:
            # Re-enable signals
            self.elevation_spin.blockSignals(False)