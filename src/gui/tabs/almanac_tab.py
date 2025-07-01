"""
Almanac Tab for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QHeaderView,
)
from PyQt6.QtCore import pyqtSignal

from core.config.models import GNSSSignalSimConfig, AlmanacConfig, ConstellationType


class AlmanacTab(QWidget):
    """Almanac configuration tab."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.init_ui()

    def init_ui(self):
        """Initialize the UI for the almanac tab."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        almanac_group = QGroupBox("Almanac Settings")
        almanac_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #20c997;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #20c997;
            }
        """)
        layout.addWidget(almanac_group)

        grid = QGridLayout()
        almanac_group.setLayout(grid)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["System", "File Path", ""])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        grid.addWidget(self.table, 0, 0, 1, 4)

        self.add_button = QPushButton("Add Almanac")
        self.add_button.clicked.connect(self.add_almanac)
        grid.addWidget(self.add_button, 1, 0)

        self.refresh_from_config()

    def add_almanac(self):
        """Add a new almanac entry to the table."""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        system_combo = QComboBox()
        for const_type in ConstellationType:
            system_combo.addItem(const_type.value)
        self.table.setCellWidget(row_position, 0, system_combo)

        file_path_edit = QLineEdit()
        self.table.setCellWidget(row_position, 1, file_path_edit)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_almanac(row_position))
        self.table.setCellWidget(row_position, 2, remove_button)

    def remove_almanac(self, row):
        """Remove an almanac entry from the table."""
        self.table.removeRow(row)
        self.update_config()

    def refresh_from_config(self):
        """Refresh the UI from the config model."""
        self.table.setRowCount(0)
        for almanac_config in self.config.almanac:
            self.add_almanac_from_config(almanac_config)

    def add_almanac_from_config(self, almanac_config: AlmanacConfig):
        """Add a row to the table from an AlmanacConfig object."""
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        system_combo = QComboBox()
        for const_type in ConstellationType:
            system_combo.addItem(const_type.value)
        system_combo.setCurrentText(almanac_config.system.value)
        self.table.setCellWidget(row_position, 0, system_combo)

        file_path_edit = QLineEdit(almanac_config.name)
        self.table.setCellWidget(row_position, 1, file_path_edit)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(lambda: self.remove_almanac(row_position))
        self.table.setCellWidget(row_position, 2, remove_button)

    def update_config(self):
        """Update the config model from the UI."""
        almanac_list = []
        for row in range(self.table.rowCount()):
            system = ConstellationType(self.table.cellWidget(row, 0).currentText())
            name = self.table.cellWidget(row, 1).text()
            almanac_list.append(AlmanacConfig(system=system, name=name))
        self.config.almanac = almanac_list
        self.config_changed.emit()
