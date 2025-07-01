"""
Interactive Map Dialog for Coordinate Selection

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This dialog provides an interactive map for selecting coordinates
using Folium and QWebEngineView.
"""

import os
import tempfile
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
)
from PyQt6.QtCore import pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium
from core.utils.logger import info, debug, log_button_click, error


class MapDialog(QDialog):
    """Interactive map dialog for coordinate selection."""

    coordinates_selected = pyqtSignal(float, float)  # longitude, latitude

    def __init__(self, parent=None, initial_lat=37.352721, initial_lon=-121.915773):
        super().__init__(parent)
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.selected_lat = initial_lat
        self.selected_lon = initial_lon
        self.temp_file = None

        self.init_ui()
        self.create_map()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Select Coordinates on Map")
        self.setGeometry(100, 100, 1000, 700)

        layout = QVBoxLayout(self)

        # Coordinate display group
        coord_group = QGroupBox("Selected Coordinates")
        coord_layout = QFormLayout(coord_group)

        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90.0, 90.0)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setValue(self.initial_lat)
        self.lat_spin.valueChanged.connect(self.on_coordinate_changed)
        coord_layout.addRow("Latitude:", self.lat_spin)

        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180.0, 180.0)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setValue(self.initial_lon)
        self.lon_spin.valueChanged.connect(self.on_coordinate_changed)
        coord_layout.addRow("Longitude:", self.lon_spin)

        layout.addWidget(coord_group)

        # Map view
        self.map_view = QWebEngineView()
        layout.addWidget(self.map_view)

        # Instructions
        instructions = QLabel(
            "Click on the map to select coordinates, or enter them manually above. "
            "The map will update automatically."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(instructions)

        # Buttons
        button_layout = QHBoxLayout()

        self.reset_button = QPushButton("Reset to Initial")
        self.reset_button.clicked.connect(self.reset_coordinates)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_coordinates)
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

    def create_map(self):
        """Create and display the interactive map."""
        try:
            debug(f"Creating map centered at {self.selected_lat}, {self.selected_lon}")

            # Create folium map
            m = folium.Map(
                location=[self.selected_lat, self.selected_lon],
                zoom_start=15,
                tiles="OpenStreetMap",
            )

            # Add marker for selected location
            folium.Marker(
                [self.selected_lat, self.selected_lon],
                popup=f"Selected: {self.selected_lat:.6f}, {self.selected_lon:.6f}",
                tooltip="Selected Location",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)

            # Add click handler JavaScript
            click_js = """
            <script>
            function onMapClick(e) {
                var lat = e.latlng.lat;
                var lng = e.latlng.lng;
                
                // Update the marker
                if (window.currentMarker) {
                    map.removeLayer(window.currentMarker);
                }
                
                window.currentMarker = L.marker([lat, lng], {
                    icon: L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    })
                }).addTo(map);
                
                window.currentMarker.bindPopup('Selected: ' + lat.toFixed(6) + ', ' + lng.toFixed(6)).openPopup();
                
                // Send coordinates back to Python (this would need a bridge)
                console.log('Coordinates selected:', lat, lng);
            }
            
            map.on('click', onMapClick);
            </script>
            """

            # Save map to temporary file
            self.temp_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".html", delete=False
            )
            map_html = m._repr_html_()

            # Add the click handler to the HTML
            map_html = map_html.replace("</body>", click_js + "</body>")

            self.temp_file.write(map_html)
            self.temp_file.close()

            # Load map in web view
            self.map_view.load(QUrl.fromLocalFile(self.temp_file.name))

            info("Interactive map created successfully")

        except Exception as e:
            error(f"Failed to create map: {str(e)}")
            QMessageBox.warning(
                self, "Map Error", f"Failed to create interactive map: {str(e)}"
            )

    def on_coordinate_changed(self):
        """Handle coordinate changes from spin boxes."""
        self.selected_lat = self.lat_spin.value()
        self.selected_lon = self.lon_spin.value()
        debug(f"Coordinates changed to: {self.selected_lat}, {self.selected_lon}")
        self.create_map()  # Recreate map with new coordinates

    def reset_coordinates(self):
        """Reset coordinates to initial values."""
        log_button_click("Reset Coordinates", "Map Dialog")
        self.lat_spin.setValue(self.initial_lat)
        self.lon_spin.setValue(self.initial_lon)

    def accept_coordinates(self):
        """Accept selected coordinates and close dialog."""
        log_button_click(
            "Accept Coordinates",
            "Map Dialog",
            f"Selected: {self.selected_lat:.6f}, {self.selected_lon:.6f}",
        )
        self.coordinates_selected.emit(self.selected_lon, self.selected_lat)
        self.accept()

    def closeEvent(self, event):
        """Clean up temporary files when dialog closes."""
        if self.temp_file and os.path.exists(self.temp_file.name):
            try:
                os.unlink(self.temp_file.name)
                debug("Temporary map file cleaned up")
            except:
                pass
        event.accept()
