"""
Power Configuration Tab

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This tab handles signal power configuration including noise floor,
initial power settings, and elevation adjustment.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QCheckBox,
    QLabel,
    QSpacerItem,
    QSizePolicy,
    QTableWidget,
    QHeaderView,
    QPushButton,
    QTableWidgetItem,
    QComboBox,
)
from PyQt6.QtCore import pyqtSignal
from core.config.models import GNSSSignalSimConfig
from gui.dialogs.signal_power_dialog import SignalPowerDialog


class PowerTab(QWidget):
    """Power configuration tab."""

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

        # Power Settings Group
        power_group = QGroupBox("Signal Power Configuration")
        power_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #dc3545;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #dc3545;
            }
        """)
        power_layout = QFormLayout(power_group)

        # Noise floor
        self.noise_floor_spin = QDoubleSpinBox()
        self.noise_floor_spin.setRange(-200.0, -100.0)
        self.noise_floor_spin.setDecimals(1)
        self.noise_floor_spin.setSuffix(" dBm/Hz")
        self.noise_floor_spin.setValue(-174.0)
        power_layout.addRow("Noise Floor:", self.noise_floor_spin)

        # Initial power value
        self.init_power_spin = QDoubleSpinBox()
        self.init_power_spin.setRange(20.0, 60.0)
        self.init_power_spin.setDecimals(1)
        self.init_power_spin.setSuffix(" ")  # Suffix will be set by unit combo
        self.init_power_spin.setValue(45.0)
        power_layout.addRow("Initial Power:", self.init_power_spin)

        self.init_power_unit_combo = QComboBox()
        self.init_power_unit_combo.addItems(["dBHz", "dBm", "dBW"])
        power_layout.addRow("Initial Power Unit:", self.init_power_unit_combo)
        
        # Set initial suffix
        self.init_power_spin.setSuffix(f" {self.init_power_unit_combo.currentText()}")

        # Elevation adjustment
        self.elevation_adjust_check = QCheckBox(
            "Enable elevation-based power adjustment"
        )
        power_layout.addRow("Elevation Adjustment:", self.elevation_adjust_check)

        layout.addWidget(power_group)

        signal_power_group = QGroupBox("Per-Satellite Power Settings")
        signal_power_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #fd7e14;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #fd7e14;
            }
        """)
        signal_power_layout = QVBoxLayout(signal_power_group)

        self.signal_power_table = QTableWidget()
        self.signal_power_table.setColumnCount(4)
        self.signal_power_table.setHorizontalHeaderLabels(
            ["System", "SVID(s)", "Power Values", ""]
        )
        self.signal_power_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.signal_power_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        signal_power_layout.addWidget(self.signal_power_table)

        self.add_signal_power_button = QPushButton("Add Satellite Power Rule")
        signal_power_layout.addWidget(self.add_signal_power_button)

        layout.addWidget(signal_power_group)

        # Information Group
        info_group = QGroupBox("Power Information")
        info_group.setStyleSheet("""
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
        info_layout = QVBoxLayout(info_group)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #343a40;
                color: #f8f9fa;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_group)

        # Update info initially
        self.update_power_info()

        # Add spacer
        spacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        layout.addItem(spacer)

    def connect_signals(self):
        """Connect widget signals."""
        self.noise_floor_spin.valueChanged.connect(self.update_config)
        self.init_power_spin.valueChanged.connect(self.update_config)
        self.init_power_unit_combo.currentTextChanged.connect(self.on_unit_changed)
        self.elevation_adjust_check.stateChanged.connect(self.update_config)
        self.add_signal_power_button.clicked.connect(self.add_signal_power_rule)

    def on_unit_changed(self):
        """Handle unit change and update suffix."""
        unit = self.init_power_unit_combo.currentText()
        self.init_power_spin.setSuffix(f" {unit}")
        self.update_config()

    def update_config(self):
        """Update configuration from widget values."""
        self.config.power.noise_floor = self.noise_floor_spin.value()
        self.config.power.init_power.value = self.init_power_spin.value()
        self.config.power.init_power.unit = self.init_power_unit_combo.currentText()
        self.config.power.elevation_adjust = self.elevation_adjust_check.isChecked()

        self.update_power_info()
        self.config_changed.emit()

    def update_power_info(self):
        """Update power information display."""
        noise_floor = self.noise_floor_spin.value()
        init_power = self.init_power_spin.value()
        power_unit = self.init_power_unit_combo.currentText()
        elevation_adjust = self.elevation_adjust_check.isChecked()

        # Calculate signal-to-noise ratio
        snr = init_power - noise_floor

        info_text = "Signal Power Configuration:\n\n"
        info_text += f"• Noise Floor: {noise_floor:.1f} dBm/Hz\n"
        info_text += f"• Initial Power: {init_power:.1f} {power_unit}\n"
        info_text += f"• Signal-to-Noise Ratio: {snr:.1f} dB\n"
        info_text += f"• Elevation Adjustment: {'Enabled' if elevation_adjust else 'Disabled'}\n\n"

        # Add power level interpretation
        if snr < 35:
            info_text += "⚠️ Low SNR - May result in poor signal quality"
        elif snr < 45:
            info_text += "✓ Moderate SNR - Good for most applications"
        else:
            info_text += "✓ High SNR - Excellent signal quality"

        if elevation_adjust:
            info_text += "\n\nElevation adjustment will modify signal power based on satellite elevation angle."

        self.info_label.setText(info_text)

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals
        self.noise_floor_spin.blockSignals(True)
        self.init_power_spin.blockSignals(True)
        self.init_power_unit_combo.blockSignals(True)
        self.elevation_adjust_check.blockSignals(True)

        try:
            self.noise_floor_spin.setValue(self.config.power.noise_floor)
            self.init_power_spin.setValue(self.config.power.init_power.value)
            self.init_power_unit_combo.setCurrentText(self.config.power.init_power.unit)
            self.init_power_spin.setSuffix(f" {self.config.power.init_power.unit}")
            self.elevation_adjust_check.setChecked(self.config.power.elevation_adjust)

            self.signal_power_table.setRowCount(0)
            for i, signal_power in enumerate(self.config.power.signal_power):
                self.signal_power_table.insertRow(i)
                self.signal_power_table.setItem(
                    i, 0, QTableWidgetItem(signal_power.system.value)
                )
                svid_text = ", ".join(map(str, signal_power.svid))
                self.signal_power_table.setItem(i, 1, QTableWidgetItem(svid_text))
                power_values_text = f"{len(signal_power.power_value)} value(s)"
                self.signal_power_table.setItem(
                    i, 2, QTableWidgetItem(power_values_text)
                )

                remove_button = QPushButton("Remove")
                remove_button.clicked.connect(
                    lambda _, row=i: self.remove_signal_power_rule(row)
                )
                self.signal_power_table.setCellWidget(i, 3, remove_button)

            self.update_power_info()

        finally:
            # Re-enable signals
            self.noise_floor_spin.blockSignals(False)
            self.init_power_spin.blockSignals(False)
            self.init_power_unit_combo.blockSignals(False)
            self.elevation_adjust_check.blockSignals(False)

    def on_signal_power_changed(self, signal_power):
        self.config.power.signal_power.append(signal_power)
        self.refresh_from_config()
        self.config_changed.emit()

    def remove_signal_power_rule(self, row):
        del self.config.power.signal_power[row]
        self.refresh_from_config()
        self.config_changed.emit()

    def add_signal_power_rule(self):
        dialog = SignalPowerDialog(self)
        dialog.signal_power_changed.connect(self.on_signal_power_changed)
        dialog.exec()
