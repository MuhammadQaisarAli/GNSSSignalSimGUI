"""
Masked Satellite Configuration Dialog

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This dialog allows users to configure which satellites should be masked out
from the simulation output according to the SignalSim JSON specification.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QLabel,
    QSpinBox,
    QCheckBox,
    QDialogButtonBox,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
from core.config.models import ConstellationType, SatelliteMask
from core.utils.logger import debug, info


class MaskedSatelliteDialog(QDialog):
    """Dialog for configuring masked satellites."""

    satellites_updated = pyqtSignal(list)  # Emit list of SatelliteMask objects

    def __init__(self, parent=None, current_masks=None):
        super().__init__(parent)
        self.current_masks = current_masks or []
        self.init_ui()
        self.populate_table()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Configure Masked Satellites")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title and description
        title_label = QLabel("Satellite Masking Configuration")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)

        desc_label = QLabel(
            "Configure which satellites should be excluded from the simulation output.\n"
            "Masked satellites will not appear in the generated signal data."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc_label)

        # Add new mask group
        add_group = QGroupBox("Add New Satellite Mask")
        add_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
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
        add_layout = QFormLayout(add_group)

        # Constellation selection
        self.constellation_combo = QComboBox()
        for constellation in ConstellationType:
            self.constellation_combo.addItem(constellation.value, constellation)
        add_layout.addRow("Constellation:", self.constellation_combo)

        # SVID input methods
        svid_method_layout = QHBoxLayout()
        
        # Single SVID
        self.single_svid_radio = QCheckBox("Single SVID:")
        self.single_svid_radio.setChecked(True)
        self.single_svid_radio.toggled.connect(self.on_svid_method_changed)
        svid_method_layout.addWidget(self.single_svid_radio)
        
        self.single_svid_spin = QSpinBox()
        self.single_svid_spin.setRange(1, 50)
        self.single_svid_spin.setValue(1)
        svid_method_layout.addWidget(self.single_svid_spin)
        
        svid_method_layout.addStretch()
        add_layout.addRow("", svid_method_layout)

        # Multiple SVIDs
        multi_svid_layout = QHBoxLayout()
        
        self.multi_svid_radio = QCheckBox("Multiple SVIDs:")
        self.multi_svid_radio.toggled.connect(self.on_svid_method_changed)
        multi_svid_layout.addWidget(self.multi_svid_radio)
        
        self.multi_svid_edit = QLineEdit()
        self.multi_svid_edit.setPlaceholderText("e.g., 1,2,5-10,15")
        self.multi_svid_edit.setEnabled(False)
        multi_svid_layout.addWidget(self.multi_svid_edit)
        
        add_layout.addRow("", multi_svid_layout)

        # Add button
        add_button_layout = QHBoxLayout()
        self.add_mask_button = QPushButton("Add Satellite Mask")
        self.add_mask_button.clicked.connect(self.add_satellite_mask)
        self.add_mask_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_button_layout.addWidget(self.add_mask_button)
        add_button_layout.addStretch()
        add_layout.addRow("", add_button_layout)

        layout.addWidget(add_group)

        # Current masks table
        table_group = QGroupBox("Current Satellite Masks")
        table_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
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
        table_layout = QVBoxLayout(table_group)

        self.masks_table = QTableWidget()
        self.masks_table.setColumnCount(4)
        self.masks_table.setHorizontalHeaderLabels([
            "Constellation", "SVID(s)", "Count", "Actions"
        ])
        
        # Set column widths
        header = self.masks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.masks_table.setAlternatingRowColors(True)
        self.masks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table_layout.addWidget(self.masks_table)

        # Table controls
        table_controls = QHBoxLayout()
        
        self.remove_selected_button = QPushButton("Remove Selected")
        self.remove_selected_button.clicked.connect(self.remove_selected_mask)
        self.remove_selected_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        table_controls.addWidget(self.remove_selected_button)
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self.clear_all_masks)
        table_controls.addWidget(self.clear_all_button)
        
        table_controls.addStretch()
        
        self.mask_count_label = QLabel("0 satellites masked")
        self.mask_count_label.setStyleSheet("color: #666; font-style: italic;")
        table_controls.addWidget(self.mask_count_label)
        
        table_layout.addLayout(table_controls)
        layout.addWidget(table_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def on_svid_method_changed(self):
        """Handle SVID input method change."""
        if self.single_svid_radio.isChecked():
            self.single_svid_spin.setEnabled(True)
            self.multi_svid_edit.setEnabled(False)
            self.multi_svid_radio.setChecked(False)
        else:
            self.single_svid_spin.setEnabled(False)
            self.multi_svid_edit.setEnabled(True)
            self.single_svid_radio.setChecked(False)

    def add_satellite_mask(self):
        """Add a new satellite mask."""
        constellation = self.constellation_combo.currentData()
        
        try:
            if self.single_svid_radio.isChecked():
                # Single SVID
                svid = self.single_svid_spin.value()
                svids = [svid]
            else:
                # Multiple SVIDs
                svid_text = self.multi_svid_edit.text().strip()
                if not svid_text:
                    QMessageBox.warning(self, "Input Error", "Please enter SVID(s).")
                    return
                
                svids = self.parse_svid_string(svid_text)
                if not svids:
                    return
            
            # Check for duplicates
            for existing_mask in self.current_masks:
                if existing_mask.system == constellation:
                    existing_svids = existing_mask.svid if isinstance(existing_mask.svid, list) else [existing_mask.svid]
                    overlap = set(svids) & set(existing_svids)
                    if overlap:
                        QMessageBox.warning(
                            self, 
                            "Duplicate SVIDs", 
                            f"SVID(s) {sorted(overlap)} are already masked for {constellation.value}."
                        )
                        return
            
            # Create new mask
            new_mask = SatelliteMask(system=constellation, svid=svids)
            self.current_masks.append(new_mask)
            
            # Refresh table
            self.populate_table()
            
            # Reset inputs
            self.single_svid_spin.setValue(1)
            self.multi_svid_edit.clear()
            
            info(f"Added satellite mask: {constellation.value} SVID(s) {svids}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add satellite mask: {str(e)}")

    def parse_svid_string(self, svid_text):
        """Parse SVID string like '1,2,5-10,15' into list of integers."""
        svids = []
        try:
            for part in svid_text.split(','):
                part = part.strip()
                if '-' in part:
                    # Range like "5-10"
                    start, end = map(int, part.split('-'))
                    if start > end:
                        raise ValueError(f"Invalid range: {part}")
                    svids.extend(range(start, end + 1))
                else:
                    # Single number
                    svids.append(int(part))
            
            # Remove duplicates and sort
            svids = sorted(list(set(svids)))
            
            # Validate range
            for svid in svids:
                if svid < 1 or svid > 50:  # Reasonable SVID range
                    raise ValueError(f"SVID {svid} is out of valid range (1-50)")
            
            return svids
            
        except ValueError as e:
            QMessageBox.warning(
                self, 
                "Invalid SVID Format", 
                f"Invalid SVID format: {str(e)}\n\n"
                "Please use format like: 1,2,5-10,15\n"
                "- Comma-separated numbers\n"
                "- Ranges with hyphen (e.g., 5-10)\n"
                "- SVIDs must be between 1 and 50"
            )
            return []

    def remove_selected_mask(self):
        """Remove selected satellite mask."""
        current_row = self.masks_table.currentRow()
        if current_row >= 0 and current_row < len(self.current_masks):
            mask = self.current_masks[current_row]
            constellation = mask.system.value
            svids = mask.svid if isinstance(mask.svid, list) else [mask.svid]
            
            reply = QMessageBox.question(
                self,
                "Confirm Removal",
                f"Remove satellite mask for {constellation} SVID(s) {svids}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                del self.current_masks[current_row]
                self.populate_table()
                info(f"Removed satellite mask: {constellation} SVID(s) {svids}")

    def clear_all_masks(self):
        """Clear all satellite masks."""
        if not self.current_masks:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Clear All",
            f"Remove all {len(self.current_masks)} satellite masks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_masks.clear()
            self.populate_table()
            info("Cleared all satellite masks")

    def populate_table(self):
        """Populate the masks table with current data."""
        self.masks_table.setRowCount(len(self.current_masks))
        
        total_satellites = 0
        
        for row, mask in enumerate(self.current_masks):
            # Constellation
            constellation_item = QTableWidgetItem(mask.system.value)
            constellation_item.setFlags(constellation_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.masks_table.setItem(row, 0, constellation_item)
            
            # SVID(s)
            svids = mask.svid if isinstance(mask.svid, list) else [mask.svid]
            svid_text = self.format_svid_list(svids)
            svid_item = QTableWidgetItem(svid_text)
            svid_item.setFlags(svid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.masks_table.setItem(row, 1, svid_item)
            
            # Count
            count_item = QTableWidgetItem(str(len(svids)))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.masks_table.setItem(row, 2, count_item)
            
            # Actions
            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda checked, r=row: self.remove_mask_by_index(r))
            remove_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            self.masks_table.setCellWidget(row, 3, remove_button)
            
            total_satellites += len(svids)
        
        # Update count label
        self.mask_count_label.setText(f"{total_satellites} satellites masked")

    def format_svid_list(self, svids):
        """Format SVID list for display, compacting consecutive ranges."""
        if not svids:
            return ""
        
        svids = sorted(svids)
        ranges = []
        start = svids[0]
        end = svids[0]
        
        for svid in svids[1:]:
            if svid == end + 1:
                end = svid
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = svid
        
        # Add the last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
        
        return ", ".join(ranges)

    def remove_mask_by_index(self, index):
        """Remove mask by table index."""
        if 0 <= index < len(self.current_masks):
            mask = self.current_masks[index]
            constellation = mask.system.value
            svids = mask.svid if isinstance(mask.svid, list) else [mask.svid]
            
            del self.current_masks[index]
            self.populate_table()
            info(f"Removed satellite mask: {constellation} SVID(s) {svids}")

    def accept(self):
        """Accept dialog and emit updated masks."""
        self.satellites_updated.emit(self.current_masks)
        super().accept()

    def get_masks(self):
        """Get current satellite masks."""
        return self.current_masks