"""
Signal Power Dialog

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This dialog allows users to add and edit per-satellite power settings.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTableWidget,
    QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal
from core.config.models import SignalPower, SignalPowerValue, ConstellationType


class SignalPowerDialog(QDialog):
    """Dialog for adding/editing signal power rules."""

    signal_power_changed = pyqtSignal(object)  # SignalPower

    def __init__(self, parent=None, signal_power=None):
        super().__init__(parent)
        self.signal_power = signal_power or SignalPower(
            system=ConstellationType.GPS, svid=[]
        )
        self.init_ui()
        self.load_signal_power_data()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Signal Power Rule")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout(self)

        rule_group = QGroupBox("Rule Settings")
        rule_layout = QFormLayout(rule_group)

        self.system_combo = QComboBox()
        for const_type in ConstellationType:
            self.system_combo.addItem(const_type.value, const_type)
        rule_layout.addRow("System:", self.system_combo)

        self.svid_edit = QLineEdit()
        self.svid_edit.setPlaceholderText("e.g., 1, 2, 5-10")
        rule_layout.addRow("SVID(s):", self.svid_edit)

        layout.addWidget(rule_group)

        power_values_group = QGroupBox("Power Values")
        power_values_layout = QVBoxLayout(power_values_group)

        self.power_table = QTableWidget()
        self.power_table.setColumnCount(4)
        self.power_table.setHorizontalHeaderLabels(["Time (s)", "Unit", "Value", ""])
        power_values_layout.addWidget(self.power_table)

        self.add_power_value_button = QPushButton("Add Power Value")
        self.add_power_value_button.clicked.connect(self.add_power_value)
        power_values_layout.addWidget(self.add_power_value_button)

        layout.addWidget(power_values_group)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_changes)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def load_signal_power_data(self):
        for i in range(self.system_combo.count()):
            if self.system_combo.itemData(i) == self.signal_power.system:
                self.system_combo.setCurrentIndex(i)
                break

        svid_text = ", ".join(map(str, self.signal_power.svid))
        self.svid_edit.setText(svid_text)

        for power_value in self.signal_power.power_value:
            self.add_power_value_row(power_value)

    def add_power_value(self):
        self.add_power_value_row(SignalPowerValue(time=0.0, unit="dBHz", value=45.0))

    def add_power_value_row(self, power_value):
        row_position = self.power_table.rowCount()
        self.power_table.insertRow(row_position)

        time_spin = QDoubleSpinBox()
        time_spin.setRange(0, 86400)
        time_spin.setValue(power_value.time)
        self.power_table.setCellWidget(row_position, 0, time_spin)

        unit_combo = QComboBox()
        unit_combo.addItems(["dBHz", "dBm", "dBW"])
        unit_combo.setCurrentText(power_value.unit)
        self.power_table.setCellWidget(row_position, 1, unit_combo)

        value_spin = QDoubleSpinBox()
        value_spin.setRange(-200, 200)
        value_spin.setValue(power_value.value)
        self.power_table.setCellWidget(row_position, 2, value_spin)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.power_table.removeRow(row_position))
        self.power_table.setCellWidget(row_position, 3, remove_button)

    def accept_changes(self):
        system = self.system_combo.currentData()
        svid_text = self.svid_edit.text()
        svids = []
        for part in svid_text.split(","):
            part = part.strip()
            if "-" in part:
                start, end = part.split("-")
                svids.extend(range(int(start), int(end) + 1))
            else:
                svids.append(int(part))

        power_values = []
        for row in range(self.power_table.rowCount()):
            time = self.power_table.cellWidget(row, 0).value()
            unit = self.power_table.cellWidget(row, 1).currentText()
            value = self.power_table.cellWidget(row, 2).value()
            power_values.append(SignalPowerValue(time=time, unit=unit, value=value))

        self.signal_power.system = system
        self.signal_power.svid = svids
        self.signal_power.power_value = power_values

        self.signal_power_changed.emit(self.signal_power)
        self.accept()
