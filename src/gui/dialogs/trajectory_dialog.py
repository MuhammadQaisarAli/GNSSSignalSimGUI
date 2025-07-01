"""
Trajectory Segment Dialog

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This dialog allows users to add and edit trajectory segments.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal
from core.config.models import TrajectorySegment, TrajectoryType
from core.utils.logger import info, log_button_click


class TrajectorySegmentDialog(QDialog):
    """Dialog for adding/editing trajectory segments."""

    segment_created = pyqtSignal(object)  # TrajectorySegment

    def __init__(self, parent=None, segment=None):
        super().__init__(parent)
        self.segment = segment or TrajectorySegment()
        self.init_ui()
        self.load_segment_data()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Trajectory Segment")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout(self)

        # Segment configuration group
        segment_group = QGroupBox("Segment Configuration")
        segment_layout = QFormLayout(segment_group)

        # Trajectory type
        self.type_combo = QComboBox()
        for traj_type in TrajectoryType:
            self.type_combo.addItem(traj_type.value, traj_type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        segment_layout.addRow("Type:", self.type_combo)

        self.rows = {}

        # Parameter selectors
        self.param_selectors = {
            "const_acc": QComboBox(),
            "jerk": QComboBox(),
            "horz_turn": QComboBox(),
        }

        self.param_selectors["const_acc"].addItems(
            ["Duration & Acceleration", "Duration & Speed", "Acceleration & Speed"]
        )
        self.rows["const_acc_selector"] = (
            QLabel("Parameters:"),
            self.param_selectors["const_acc"],
        )
        segment_layout.addRow(
            self.rows["const_acc_selector"][0], self.rows["const_acc_selector"][1]
        )
        self.param_selectors["const_acc"].currentIndexChanged.connect(
            self.on_param_selection_changed
        )

        self.param_selectors["jerk"].addItems(
            ["Duration & Rate", "Duration & Acceleration", "Rate & Acceleration"]
        )
        self.rows["jerk_selector"] = (QLabel("Parameters:"), self.param_selectors["jerk"])
        segment_layout.addRow(
            self.rows["jerk_selector"][0], self.rows["jerk_selector"][1]
        )
        self.param_selectors["jerk"].currentIndexChanged.connect(
            self.on_param_selection_changed
        )

        self.param_selectors["horz_turn"].addItems(
            [
                "Duration & Angle",
                "Duration & Acceleration",
                "Duration & Rate",
                "Duration & Radius",
                "Angle & Acceleration",
                "Angle & Rate",
                "Angle & Radius",
            ]
        )
        self.rows["horz_turn_selector"] = (
            QLabel("Parameters:"),
            self.param_selectors["horz_turn"],
        )
        segment_layout.addRow(
            self.rows["horz_turn_selector"][0], self.rows["horz_turn_selector"][1]
        )
        self.param_selectors["horz_turn"].currentIndexChanged.connect(
            self.on_param_selection_changed
        )

        # Spinboxes
        self.time_spin = self._create_spinbox(0.001, 3600.0, 3, " s")
        self.rows["time"] = (QLabel("Duration:"), self.time_spin)
        segment_layout.addRow(self.rows["time"][0], self.rows["time"][1])

        self.acceleration_spin = self._create_spinbox(-100.0, 100.0, 3, " m/s²")
        self.rows["acceleration"] = (QLabel("Acceleration:"), self.acceleration_spin)
        segment_layout.addRow(
            self.rows["acceleration"][0], self.rows["acceleration"][1]
        )

        self.speed_spin = self._create_spinbox(0, 1000.0, 3, " m/s")
        self.rows["speed"] = (QLabel("Speed:"), self.speed_spin)
        segment_layout.addRow(self.rows["speed"][0], self.rows["speed"][1])

        self.rate_spin = self._create_spinbox(-100.0, 100.0, 3, " m/s³")
        self.rows["rate"] = (QLabel("Rate:"), self.rate_spin)
        segment_layout.addRow(self.rows["rate"][0], self.rows["rate"][1])

        self.angle_spin = self._create_spinbox(-360.0, 360.0, 3, " °")
        self.rows["angle"] = (QLabel("Angle:"), self.angle_spin)
        segment_layout.addRow(self.rows["angle"][0], self.rows["angle"][1])

        self.radius_spin = self._create_spinbox(0, 10000.0, 3, " m")
        self.rows["radius"] = (QLabel("Radius:"), self.radius_spin)
        segment_layout.addRow(self.rows["radius"][0], self.rows["radius"][1])

        layout.addWidget(segment_group)

        # Description group
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)

        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #212529;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        desc_layout.addWidget(self.description_label)

        layout.addWidget(desc_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_segment)
        self.ok_button.setDefault(True)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)

        # Update description initially
        self.update_description()
        self.connect_value_signals()

    def _create_spinbox(self, min_val, max_val, decimals, suffix):
        """Helper to create and configure a QDoubleSpinBox."""
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setSuffix(suffix)
        return spin

    def set_row_visible(self, row_key, visible):
        """Show or hide a form row."""
        if row_key in self.rows:
            self.rows[row_key][0].setVisible(visible)
            self.rows[row_key][1].setVisible(visible)

    def load_segment_data(self):
        """Load segment data into the form."""
        if not self.segment:
            return

        # Set trajectory type
        type_index = self.type_combo.findData(self.segment.type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        # Set values, which will trigger UI updates
        self.time_spin.setValue(self.segment.time or 0)
        self.acceleration_spin.setValue(self.segment.acceleration or 0)
        self.speed_spin.setValue(self.segment.speed or 0)
        self.rate_spin.setValue(self.segment.rate or 0)
        self.angle_spin.setValue(self.segment.angle or 0)
        self.radius_spin.setValue(self.segment.radius or 0)

        # Set parameter selectors based on which values are present
        self.on_type_changed()

    def on_type_changed(self):
        """Handle trajectory type change."""
        traj_type = self.type_combo.currentData()

        # Hide all parameter selectors and rows initially
        for key in self.param_selectors:
            self.set_row_visible(f"{key}_selector", False)

        for key in ["time", "acceleration", "speed", "rate", "angle", "radius"]:
            self.set_row_visible(key, False)

        # Show relevant controls based on trajectory type
        if traj_type == TrajectoryType.CONST:
            self.set_row_visible("time", True)
        elif traj_type in [TrajectoryType.CONST_ACC, TrajectoryType.VERTICAL_ACC]:
            self.set_row_visible("const_acc_selector", True)
        elif traj_type == TrajectoryType.JERK:
            self.set_row_visible("jerk_selector", True)
        elif traj_type == TrajectoryType.HORIZONTAL_TURN:
            self.set_row_visible("horz_turn_selector", True)

        self.on_param_selection_changed()
        self.update_description()

    def on_param_selection_changed(self):
        """Handle change in parameter selection."""
        traj_type = self.type_combo.currentData()

        # Hide all spinboxes first
        for key in ["time", "acceleration", "speed", "rate", "angle", "radius"]:
            self.set_row_visible(key, False)

        # Show spinboxes based on selection
        if traj_type in [TrajectoryType.CONST_ACC, TrajectoryType.VERTICAL_ACC]:
            selection = self.param_selectors["const_acc"].currentText()
            if "Duration" in selection:
                self.set_row_visible("time", True)
            if "Acceleration" in selection:
                self.set_row_visible("acceleration", True)
            if "Speed" in selection:
                self.set_row_visible("speed", True)
        elif traj_type == TrajectoryType.JERK:
            selection = self.param_selectors["jerk"].currentText()
            if "Duration" in selection:
                self.set_row_visible("time", True)
            if "Rate" in selection:
                self.set_row_visible("rate", True)
            if "Acceleration" in selection:
                self.set_row_visible("acceleration", True)
        elif traj_type == TrajectoryType.HORIZONTAL_TURN:
            selection = self.param_selectors["horz_turn"].currentText()
            if "Duration" in selection:
                self.set_row_visible("time", True)
            if "Angle" in selection:
                self.set_row_visible("angle", True)
            if "Acceleration" in selection:
                self.set_row_visible("acceleration", True)
            if "Rate" in selection:
                self.set_row_visible("rate", True)
            if "Radius" in selection:
                self.set_row_visible("radius", True)
        elif traj_type == TrajectoryType.CONST:
            self.set_row_visible("time", True)

        self.update_description()

    def update_description(self):
        """Update the description based on current settings."""
        traj_type = self.type_combo.currentData()
        time_val = self.time_spin.value()
        acc_val = self.acceleration_spin.value()
        speed_val = self.speed_spin.value()
        rate_val = self.rate_spin.value()
        angle_val = self.angle_spin.value()
        radius_val = self.radius_spin.value()

        description = ""
        if traj_type == TrajectoryType.CONST:
            description = f"<b>Constant Velocity:</b><br>Move at a constant speed for {time_val:.3f} seconds."
        elif traj_type in [TrajectoryType.CONST_ACC, TrajectoryType.VERTICAL_ACC]:
            selection = self.param_selectors["const_acc"].currentText()
            if selection == "Duration & Acceleration":
                description = f"<b>Constant Acceleration:</b><br>Accelerate at {acc_val:.3f} m/s² for {time_val:.3f} seconds."
            elif selection == "Duration & Speed":
                description = f"<b>Constant Acceleration:</b><br>Accelerate to a final speed of {speed_val:.3f} m/s over {time_val:.3f} seconds."
            elif selection == "Acceleration & Speed":
                description = f"<b>Constant Acceleration:</b><br>Accelerate at {acc_val:.3f} m/s² until a final speed of {speed_val:.3f} m/s is reached."
        elif traj_type == TrajectoryType.JERK:
            selection = self.param_selectors["jerk"].currentText()
            if selection == "Duration & Rate":
                description = f"<b>Jerk:</b><br>Apply a jerk rate of {rate_val:.3f} m/s³ for {time_val:.3f} seconds."
            elif selection == "Duration & Acceleration":
                description = f"<b>Jerk:</b><br>Apply jerk to reach a final acceleration of {acc_val:.3f} m/s² over {time_val:.3f} seconds."
            elif selection == "Rate & Acceleration":
                description = f"<b>Jerk:</b><br>Apply a jerk rate of {rate_val:.3f} m/s³ until a final acceleration of {acc_val:.3f} m/s² is reached."
        elif traj_type == TrajectoryType.HORIZONTAL_TURN:
            selection = self.param_selectors["horz_turn"].currentText()
            base_desc = "<b>Horizontal Turn:</b><br>"
            if "Duration & Angle" in selection:
                description = base_desc + f"Turn by {angle_val:.3f}° over {time_val:.3f} seconds."
            elif "Duration & Acceleration" in selection:
                description = base_desc + f"Turn with a centripetal acceleration of {acc_val:.3f} m/s² for {time_val:.3f} seconds."
            elif "Duration & Rate" in selection:
                description = base_desc + f"Turn at a rate of {rate_val:.3f}°/s for {time_val:.3f} seconds."
            elif "Duration & Radius" in selection:
                description = base_desc + f"Turn with a radius of {radius_val:.3f} m for {time_val:.3f} seconds."
            elif "Angle & Acceleration" in selection:
                description = base_desc + f"Turn by {angle_val:.3f}° with a centripetal acceleration of {acc_val:.3f} m/s²."
            elif "Angle & Rate" in selection:
                description = base_desc + f"Turn by {angle_val:.3f}° at a rate of {rate_val:.3f}°/s."
            elif "Angle & Radius" in selection:
                description = base_desc + f"Turn by {angle_val:.3f}° with a radius of {radius_val:.3f} m."

        self.description_label.setText(description or "Select a trajectory type.")

    def connect_value_signals(self):
        """Connects spinbox value changes to update the description."""
        self.time_spin.valueChanged.connect(self.update_description)
        self.acceleration_spin.valueChanged.connect(self.update_description)
        self.speed_spin.valueChanged.connect(self.update_description)
        self.rate_spin.valueChanged.connect(self.update_description)
        self.angle_spin.valueChanged.connect(self.update_description)
        self.radius_spin.valueChanged.connect(self.update_description)

    def accept_segment(self):
        """Accept the segment and emit signal."""
        log_button_click("Accept Trajectory Segment", "Trajectory Dialog")

        traj_type = self.type_combo.currentData()
        time_val = self.time_spin.value()
        acc_val = (
            self.acceleration_spin.value()
            if self.acceleration_spin.isEnabled()
            else None
        )
        speed_val = self.speed_spin.value() if self.speed_spin.isEnabled() else None
        rate_val = self.rate_spin.value() if self.rate_spin.isEnabled() else None
        angle_val = self.angle_spin.value() if self.angle_spin.isEnabled() else None
        radius_val = self.radius_spin.value() if self.radius_spin.isEnabled() else None

        # Validate non-zero values for visible fields
        validation_errors = []
        if self.rows["time"][0].isVisible() and self.time_spin.value() == 0.0:
            validation_errors.append("Duration cannot be zero.")
        if self.rows["acceleration"][0].isVisible() and self.acceleration_spin.value() == 0.0:
            validation_errors.append("Acceleration cannot be zero.")
        if self.rows["speed"][0].isVisible() and self.speed_spin.value() == 0.0:
            validation_errors.append("Speed cannot be zero.")
        if self.rows["rate"][0].isVisible() and self.rate_spin.value() == 0.0:
            validation_errors.append("Rate cannot be zero.")
        if self.rows["angle"][0].isVisible() and self.angle_spin.value() == 0.0:
            validation_errors.append("Angle cannot be zero.")
        if self.rows["radius"][0].isVisible() and self.radius_spin.value() == 0.0:
            validation_errors.append("Radius cannot be zero.")

        if validation_errors:
            QMessageBox.warning(
                self,
                "Input Error",
                "\n".join(validation_errors)
            )
            return

        # Create segment with only the visible parameters
        segment = TrajectorySegment(type=traj_type)

        if self.rows["time"][0].isVisible():
            segment.time = self.time_spin.value()
        if self.rows["acceleration"][0].isVisible():
            segment.acceleration = self.acceleration_spin.value()
        if self.rows["speed"][0].isVisible():
            segment.speed = self.speed_spin.value()
        if self.rows["rate"][0].isVisible():
            segment.rate = self.rate_spin.value()
        if self.rows["angle"][0].isVisible():
            segment.angle = self.angle_spin.value()
        if self.rows["radius"][0].isVisible():
            segment.radius = self.radius_spin.value()

        info(f"Trajectory segment created: {segment.type.value}, {segment.time}s, acc={segment.acceleration}")

        self.segment_created.emit(segment)
        self.accept()
