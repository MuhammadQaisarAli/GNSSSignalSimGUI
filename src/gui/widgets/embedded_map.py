"""
Embedded Map Widget for Coordinate Selection and Trajectory Visualization

This widget provides an always-visible map for coordinate selection and trajectory plotting.
"""

import os
import tempfile
import math
import folium
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QSizePolicy
from PyQt6.QtCore import pyqtSignal, QUrl, QTimer
from core.utils.logger import info, debug, error, log_button_click


class EmbeddedMapWidget(QWidget):
    """Embedded map widget for coordinate selection and trajectory visualization."""

    coordinates_changed = pyqtSignal(float, float)  # longitude, latitude

    def __init__(self, parent=None, initial_lat=37.352721, initial_lon=-121.915773):
        super().__init__(parent)
        self.current_lat = initial_lat
        self.current_lon = initial_lon
        self.temp_file = None
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.create_map)

        # Trajectory data
        self.trajectory_points = []  # List of (lat, lon, time, segment_type)
        self.initial_velocity = {"speed": 0, "course": 0}
        self.show_trajectory = True

        self.init_ui()
        self.create_map()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Simple coordinate display (read-only)
        coord_layout = QHBoxLayout()

        self.coord_label = QLabel(
            f"Center: {self.current_lat:.6f}, {self.current_lon:.6f}"
        )
        self.coord_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                color: #495057;
                padding: 2px 8px;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        self.coord_label.setMaximumHeight(25)  # Keep coordinate display compact
        coord_layout.addWidget(self.coord_label)

        coord_layout.addStretch()
        layout.addLayout(coord_layout)

        # Hidden spinboxes for programmatic access
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90.0, 90.0)
        self.lat_spin.setDecimals(6)
        self.lat_spin.setValue(self.current_lat)
        self.lat_spin.setVisible(False)

        self.lon_spin = QDoubleSpinBox()
        self.lon_spin.setRange(-180.0, 180.0)
        self.lon_spin.setDecimals(6)
        self.lon_spin.setValue(self.current_lon)
        self.lon_spin.setVisible(False)

        # Map view
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtWebEngineCore import QWebEngineSettings

            self.map_view = QWebEngineView()
            # Remove fixed minimum height - let it be fully dynamic
            self.map_view.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            # Configure web engine settings
            settings = self.map_view.settings()
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
            )
            settings.setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled, True
            )

            layout.addWidget(self.map_view)
            self.map_available = True
            info("QWebEngineView initialized successfully with trajectory support")

        except Exception as e:
            error(f"QWebEngineView not available: {str(e)}")
            # Fallback to coordinate picker widget
            try:
                from gui.widgets.coordinate_picker import CoordinatePickerWidget

                self.coordinate_picker = CoordinatePickerWidget(
                    self, self.current_lat, self.current_lon
                )
                self.coordinate_picker.coordinates_changed.connect(
                    self.on_fallback_coordinates_changed
                )
                layout.addWidget(self.coordinate_picker)
                info("Using coordinate picker fallback (map not available)")
            except Exception as fallback_error:
                error(f"Coordinate picker fallback failed: {str(fallback_error)}")
                # Final fallback to simple label
                fallback_label = QLabel(
                    "Interactive map not available.\n\n"
                    "To enable trajectory visualization:\n"
                    "1. Install: pip install PyQt6-WebEngine\n"
                    "2. Or use coordinate inputs above\n\n"
                    "Map service: OpenStreetMap (free, no API key needed)"
                )
                fallback_label.setStyleSheet("""
                    QLabel {
                        background-color: #f8f9fa;
                        color: #6c757d;
                        padding: 20px;
                        border: 2px dashed #dee2e6;
                        border-radius: 4px;
                        text-align: center;
                        font-style: italic;
                        font-family: 'Segoe UI', Arial, sans-serif;
                    }
                """)
                # Remove fixed height - let it be dynamic
                fallback_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                layout.addWidget(fallback_label)
            self.map_available = False

    def update_coordinate_display(self):
        """Update the coordinate display label."""
        self.coord_label.setText(
            f"Center: {self.current_lat:.6f}, {self.current_lon:.6f}"
        )

    def on_fallback_coordinates_changed(self, longitude, latitude):
        """Handle coordinate changes from fallback widget."""
        self.current_lat = latitude
        self.current_lon = longitude

        # Update main coordinate spinboxes
        self.lat_spin.blockSignals(True)
        self.lon_spin.blockSignals(True)
        self.lat_spin.setValue(latitude)
        self.lon_spin.setValue(longitude)
        self.lat_spin.blockSignals(False)
        self.lon_spin.blockSignals(False)

        # Emit signal
        self.coordinates_changed.emit(longitude, latitude)

    def set_coordinates(self, latitude, longitude):
        """Set coordinates programmatically."""
        self.current_lat = latitude
        self.current_lon = longitude

        # Update hidden spinboxes
        self.lat_spin.setValue(latitude)
        self.lon_spin.setValue(longitude)

        # Update coordinate display
        self.update_coordinate_display()

        # Update fallback widget if available
        if not self.map_available and hasattr(self, "coordinate_picker"):
            self.coordinate_picker.set_coordinates(latitude, longitude)

        if self.map_available:
            self.create_map()

    def set_trajectory_data(self, trajectory_segments, initial_velocity):
        """Set trajectory data for visualization."""
        self.initial_velocity = initial_velocity
        self.calculate_trajectory_points(trajectory_segments)
        if self.map_available:
            self.create_map()
        elif hasattr(self, "coordinate_picker"):
            # Update coordinate picker with trajectory info
            if hasattr(self.coordinate_picker, "update_trajectory_info"):
                self.coordinate_picker.update_trajectory_info(len(trajectory_segments))

    def calculate_trajectory_points(self, trajectory_segments):
        """Calculate trajectory points from segments."""
        self.trajectory_points = []

        if not trajectory_segments:
            return

        # Starting position and velocity
        current_lat = self.current_lat
        current_lon = self.current_lon
        current_speed = self.initial_velocity.get("speed", 0)  # m/s
        current_course = self.initial_velocity.get("course", 0)  # degrees

        # Add starting point
        self.trajectory_points.append((current_lat, current_lon, 0, "Start"))

        total_time = 0

        for segment in trajectory_segments:
            segment_time = segment.time
            segment_type = segment.type.value
            acceleration = (
                segment.acceleration if segment.acceleration is not None else 0
            )

            # Calculate points along this segment
            time_step = min(
                segment_time / 10, 1.0
            )  # 10 points per segment, max 1 second steps
            steps = max(int(segment_time / time_step), 1)

            for step in range(1, steps + 1):
                dt = step * time_step

                # Calculate new position based on segment type
                if segment_type == "Const":
                    # Constant velocity
                    distance = current_speed * dt
                elif segment_type == "ConstAcc":
                    # Constant acceleration
                    distance = current_speed * dt + 0.5 * acceleration * dt * dt
                elif segment_type == "Jerk":
                    # Simplified jerk (gradual acceleration change)
                    avg_acc = acceleration * dt / segment_time
                    distance = current_speed * dt + 0.5 * avg_acc * dt * dt
                else:
                    distance = current_speed * dt

                # Convert distance and course to lat/lon offset
                lat_offset, lon_offset = self.distance_to_coordinates(
                    distance, current_course, current_lat
                )

                new_lat = current_lat + lat_offset
                new_lon = current_lon + lon_offset

                self.trajectory_points.append(
                    (new_lat, new_lon, total_time + dt, segment_type)
                )

            # Update position and velocity for next segment
            if segment_type == "ConstAcc":
                current_speed += acceleration * segment_time
            elif segment_type == "Jerk":
                current_speed += acceleration * segment_time / 2  # Simplified

            # Update current position to end of segment
            if self.trajectory_points:
                current_lat, current_lon = self.trajectory_points[-1][:2]

            total_time += segment_time

        debug(f"Calculated {len(self.trajectory_points)} trajectory points")

    def distance_to_coordinates(self, distance_m, course_deg, lat):
        """Convert distance and course to lat/lon offsets."""
        # Earth radius in meters
        R = 6378137.0

        # Convert course to radians (0 deg = North, 90 deg = East)
        course_rad = math.radians(course_deg)

        # Calculate offsets
        lat_offset = (distance_m * math.cos(course_rad)) / R * 180 / math.pi
        lon_offset = (
            (distance_m * math.sin(course_rad))
            / (R * math.cos(math.radians(lat)))
            * 180
            / math.pi
        )

        return lat_offset, lon_offset


    def clear_trajectory(self):
        """Clear trajectory points."""
        log_button_click("Clear Trajectory", "Map Widget")
        self.trajectory_points = []
        if self.map_available:
            self.create_map()

    def create_map(self):
        """Create and display the map with trajectory."""
        if not self.map_available:
            return

        try:
            import folium

            debug(
                f"Creating map with trajectory at {self.current_lat}, {self.current_lon}"
            )

            # Create folium map
            m = folium.Map(
                location=[self.current_lat, self.current_lon],
                zoom_start=15,
                tiles="OpenStreetMap",
            )

            # Add alternative tile layers
            folium.TileLayer(
                tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                attr="OpenStreetMap",
                name="OpenStreetMap",
                overlay=False,
                control=True,
            ).add_to(m)

            # Add satellite view (if available)
            try:
                folium.TileLayer(
                    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    attr="Esri",
                    name="Satellite",
                    overlay=False,
                    control=True,
                ).add_to(m)
            except Exception as e:
                debug(f"Satellite tiles optional: {e}")
                pass  # Satellite tiles optional

            # Add layer control
            folium.LayerControl().add_to(m)

            # Add starting position marker
            folium.Marker(
                [self.current_lat, self.current_lon],
                popup=f"Start: {self.current_lat:.6f}, {self.current_lon:.6f}",
                tooltip="Starting Position",
                icon=folium.Icon(color="green", icon="play"),
            ).add_to(m)

            # Add trajectory if available and enabled
            if self.show_trajectory and self.trajectory_points:
                self.add_trajectory_to_map(m)

            # Save map to temporary file
            if self.temp_file and os.path.exists(self.temp_file):
                try:
                    os.unlink(self.temp_file)
                except:
                    pass

            temp_fd, self.temp_file = tempfile.mkstemp(suffix=".html")
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                f.write(m._repr_html_())

            # Load map in web view
            self.map_view.load(QUrl.fromLocalFile(self.temp_file))

        except Exception as e:
            error(f"Failed to create map with trajectory: {str(e)}")

    def add_trajectory_to_map(self, folium_map):
        """Add trajectory visualization to the map."""
        if not self.trajectory_points:
            return

        try:
            # Create trajectory line
            trajectory_coords = [
                (point[0], point[1]) for point in self.trajectory_points
            ]

            # Add trajectory polyline
            folium.PolyLine(
                trajectory_coords,
                color="blue",
                weight=3,
                opacity=0.8,
                popup="Trajectory Path",
            ).add_to(folium_map)

            # Add segment markers
            segment_colors = {
                "Start": "green",
                "Const": "blue",
                "ConstAcc": "orange",
                "Jerk": "red",
            }

            # Add markers for key points
            for i, (lat, lon, time, segment_type) in enumerate(self.trajectory_points):
                if i == 0:  # Start point
                    continue  # Already added above
                elif i == len(self.trajectory_points) - 1:  # End point
                    folium.Marker(
                        [lat, lon],
                        popup=f"End: {lat:.6f}, {lon:.6f}<br>Time: {time:.1f}s",
                        tooltip="End Position",
                        icon=folium.Icon(color="red", icon="stop"),
                    ).add_to(folium_map)
                elif i % 10 == 0:  # Every 10th point for segment markers
                    color = segment_colors.get(segment_type, "gray")
                    folium.CircleMarker(
                        [lat, lon],
                        radius=4,
                        popup=f"Time: {time:.1f}s<br>Type: {segment_type}",
                        color=color,
                        fill=True,
                        fillColor=color,
                    ).add_to(folium_map)

            # Add trajectory statistics
            if len(self.trajectory_points) > 1:
                total_distance = self.calculate_total_distance()
                total_time = self.trajectory_points[-1][2]

                # Add info box - compact version in bottom left
                info_html = f"""
                <div style="position: fixed; 
                           bottom: 10px; left: 10px; width: 150px; height: 60px; 
                           background-color: rgba(255, 255, 255, 0.9); border:1px solid #ccc; z-index:9999; 
                           font-size:11px; padding: 5px; border-radius: 3px; box-shadow: 0 2px 4px rgba(0,0,0,0.2)">
                <div style="font-weight: bold; margin-bottom: 2px;">Trajectory</div>
                <div>Distance: {total_distance:.0f}m</div>
                <div>Time: {total_time:.1f}s | Points: {len(self.trajectory_points)}</div>
                </div>
                """
                folium_map.get_root().html.add_child(folium.Element(info_html))

            info(f"Added trajectory with {len(self.trajectory_points)} points to map")

        except Exception as e:
            error(f"Failed to add trajectory to map: {str(e)}")

    def calculate_total_distance(self):
        """Calculate total trajectory distance."""
        if len(self.trajectory_points) < 2:
            return 0

        total_distance = 0
        for i in range(1, len(self.trajectory_points)):
            lat1, lon1 = self.trajectory_points[i - 1][:2]
            lat2, lon2 = self.trajectory_points[i][:2]

            # Haversine formula for distance
            R = 6378137  # Earth radius in meters
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
                math.radians(lat1)
            ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c
            total_distance += distance

        return total_distance

    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
                debug("Embedded map temporary file cleaned up")
            except Exception as e:
                debug(f"Temporary file cleanup failed: {e}")
                pass
