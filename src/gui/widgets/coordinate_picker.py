"""
Simple Coordinate Picker Widget

A fallback widget for coordinate selection when maps are not available.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QDoubleSpinBox,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
)
from PyQt6.QtCore import pyqtSignal
from core.utils.logger import info, debug, log_button_click


class CoordinatePickerWidget(QWidget):
    """Simple coordinate picker with preset locations."""

    coordinates_changed = pyqtSignal(float, float)  # longitude, latitude

    def __init__(self, parent=None, initial_lat=37.352721, initial_lon=-121.915773):
        super().__init__(parent)
        self.current_lat = initial_lat
        self.current_lon = initial_lon

        self.init_ui()
        self.setup_presets()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Coordinate input group
        coord_group = QGroupBox("Coordinate Input")
        coord_layout = QFormLayout(coord_group)

        # Latitude
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90.0, 90.0)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setValue(self.current_lat)
        self.lat_spin.valueChanged.connect(self.on_coordinate_changed)
        coord_layout.addRow("Latitude:", self.lat_spin)

        # Longitude
        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180.0, 180.0)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setValue(self.current_lon)
        self.lon_spin.valueChanged.connect(self.on_coordinate_changed)
        coord_layout.addRow("Longitude:", self.lon_spin)

        layout.addWidget(coord_group)

        # Preset locations group
        preset_group = QGroupBox("Preset Locations")
        preset_layout = QVBoxLayout(preset_group)

        # Preset dropdown
        preset_select_layout = QHBoxLayout()
        preset_select_layout.addWidget(QLabel("Quick Select:"))

        self.preset_combo = QComboBox()
        self.preset_combo.currentTextChanged.connect(self.on_preset_selected)
        preset_select_layout.addWidget(self.preset_combo)

        preset_layout.addLayout(preset_select_layout)

        # Custom location input
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Or enter location:"))

        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("e.g., San Francisco, CA")
        custom_layout.addWidget(self.location_edit)

        self.geocode_button = QPushButton("Find")
        self.geocode_button.clicked.connect(self.geocode_location)
        custom_layout.addWidget(self.geocode_button)

        preset_layout.addLayout(custom_layout)

        layout.addWidget(preset_group)

        # Information display
        info_group = QGroupBox("Location Information")
        info_layout = QVBoxLayout(info_group)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #212529;
                padding: 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_group)

        self.update_info()

    def setup_presets(self):
        """Set up preset locations."""
        self.presets = {
            "Current Location": (self.current_lat, self.current_lon),
            "San Francisco, CA": (37.7749, -122.4194),
            "New York, NY": (40.7128, -74.0060),
            "London, UK": (51.5074, -0.1278),
            "Tokyo, Japan": (35.6762, 139.6503),
            "Sydney, Australia": (-33.8688, 151.2093),
            "Berlin, Germany": (52.5200, 13.4050),
            "Paris, France": (48.8566, 2.3522),
            "Beijing, China": (39.9042, 116.4074),
            "Moscow, Russia": (55.7558, 37.6176),
            "GPS Test Location": (37.352721, -121.915773),
        }

        self.preset_combo.addItem("-- Select Preset --")
        for name in self.presets.keys():
            self.preset_combo.addItem(name)

    def on_coordinate_changed(self):
        """Handle coordinate changes."""
        self.current_lat = self.lat_spin.value()
        self.current_lon = self.lon_spin.value()

        debug(f"Coordinates changed: {self.current_lat}, {self.current_lon}")
        self.coordinates_changed.emit(self.current_lon, self.current_lat)
        self.update_info()

    def on_preset_selected(self, preset_name):
        """Handle preset selection."""
        if preset_name in self.presets:
            log_button_click(
                "Preset Location Selected", "Coordinate Picker", preset_name
            )
            lat, lon = self.presets[preset_name]
            self.set_coordinates(lat, lon)

    def geocode_location(self):
        """Attempt to geocode the entered location."""
        location_text = self.location_edit.text().strip()
        if not location_text:
            return

        log_button_click("Geocode Location", "Coordinate Picker", location_text)

        # Simple geocoding simulation (in real implementation, you'd use a geocoding service)
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Geocoding",
            f"Geocoding for '{location_text}' would be implemented here.\n"
            "For now, please use preset locations or enter coordinates manually.",
        )

    def set_coordinates(self, latitude, longitude):
        """Set coordinates programmatically."""
        self.lat_spin.blockSignals(True)
        self.lon_spin.blockSignals(True)

        self.lat_spin.setValue(latitude)
        self.lon_spin.setValue(longitude)
        self.current_lat = latitude
        self.current_lon = longitude

        self.lat_spin.blockSignals(False)
        self.lon_spin.blockSignals(False)

        self.update_info()

    def update_info(self):
        """Update location information."""
        # Determine hemisphere and format
        lat_hem = "N" if self.current_lat >= 0 else "S"
        lon_hem = "E" if self.current_lon >= 0 else "W"

        info_text = "Current Coordinates:\n"
        info_text += f"Latitude: {abs(self.current_lat):.6f}° {lat_hem}\n"
        info_text += f"Longitude: {abs(self.current_lon):.6f}° {lon_hem}\n\n"

        # Add DMS format
        lat_dms = self.decimal_to_dms(self.current_lat, True)
        lon_dms = self.decimal_to_dms(self.current_lon, False)
        info_text += "DMS Format:\n"
        info_text += f"Lat: {lat_dms}\n"
        info_text += f"Lon: {lon_dms}\n\n"

        # Add trajectory info if available
        if hasattr(self, "trajectory_segments"):
            info_text += f"Trajectory Segments: {self.trajectory_segments}\n\n"

        # Add general location info
        if abs(self.current_lat) > 66.5:
            zone = "Arctic/Antarctic"
        elif abs(self.current_lat) > 23.5:
            zone = "Temperate"
        else:
            zone = "Tropical"

        info_text += f"Climate Zone: {zone}\n"
        info_text += f"Time Zone: Approximately UTC{self.estimate_timezone():+.0f}"

        self.info_label.setText(info_text)

    def update_trajectory_info(self, segment_count):
        """Update trajectory information."""
        self.trajectory_segments = segment_count
        self.update_info()

    def decimal_to_dms(self, decimal, is_latitude):
        """Convert decimal degrees to DMS format."""
        abs_decimal = abs(decimal)
        degrees = int(abs_decimal)
        minutes_float = (abs_decimal - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60

        if is_latitude:
            direction = "N" if decimal >= 0 else "S"
        else:
            direction = "E" if decimal >= 0 else "W"

        return f"{degrees}° {minutes}' {seconds:.2f}\" {direction}"

    def estimate_timezone(self):
        """Estimate timezone from longitude."""
        return round(self.current_lon / 15.0)
