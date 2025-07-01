"""
Trajectory Configuration Tab - Responsive Layout

This tab handles trajectory configuration with responsive, scrollable layout.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QGridLayout,
    QLineEdit,
    QDoubleSpinBox,
    QComboBox,
    QListWidget,
    QPushButton,
    QLabel,
    QSizePolicy,
    QScrollArea,
    QFrame,
    QSplitter,
)
from PyQt6.QtCore import pyqtSignal, Qt
from core.config.models import (
    GNSSSignalSimConfig,
    PositionType,
    VelocityType,
)
from core.utils.logger import info, debug, error, log_button_click
from gui.widgets.embedded_map import EmbeddedMapWidget
from gui.dialogs.trajectory_dialog import TrajectorySegmentDialog


class TrajectoryTab(QWidget):
    """Trajectory configuration tab with responsive layout."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        # Initialize unit tracking
        self._current_speed_unit = "mps"  # Single unit for SCU (both horizontal and vertical)
        self._current_angle_unit = "degree"
        # ENU unit tracking
        self._current_east_unit = "mps"
        self._current_north_unit = "mps"
        self._current_up_enu_unit = "mps"
        # ECEF unit tracking
        self._current_vx_unit = "mps"
        self._current_vy_unit = "mps"
        self._current_vz_unit = "mps"
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def init_ui(self):
        """Initialize the responsive, scrollable user interface."""
        # Main layout for the tab
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Create scroll area for the entire content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.Shape.NoFrame)

        # Content widget inside scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)

        # 1. Scenario Information
        self.setup_scenario_section(content_layout)

        # 2. Position and Velocity (side by side on wide screens)
        self.setup_position_velocity_section(content_layout)

        # 3. Map Integration is now integrated into the position/velocity section

        # Set the content widget to scroll area and add to main layout
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def setup_scenario_section(self, parent_layout):
        """Setup scenario information section - compact single line."""
        scenario_group = QGroupBox("Scenario")
        scenario_group.setMaximumHeight(60)  # Limit height to minimum needed
        scenario_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #6f42c1;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #6f42c1;
            }
        """)
        scenario_layout = QHBoxLayout(scenario_group)
        scenario_layout.setSpacing(5)
        scenario_layout.setContentsMargins(5, 5, 5, 5)  # Reduce margins

        scenario_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter scenario name...")
        self.name_edit.setMaximumWidth(250)  # Reasonable width, not too wide
        self.name_edit.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        scenario_layout.addWidget(self.name_edit)
        scenario_layout.addStretch()

        parent_layout.addWidget(scenario_group)

    def setup_position_velocity_section(self, parent_layout):
        """Setup position and velocity sections with responsive layout."""
        # Use splitter for resizable layout between left controls and map
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setChildrenCollapsible(False)  # Prevent collapsing sections

        # Left side: Position, Velocity, and Trajectory stacked vertically with splitters
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        left_splitter.setChildrenCollapsible(False)

        # Position Group
        position_group = QGroupBox("Initial Position")
        position_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #007acc;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #007acc;
            }
        """)
        position_layout = QVBoxLayout(position_group)
        position_layout.setSpacing(5)

        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.position_type_combo = QComboBox()
        self.position_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for pos_type in PositionType:
            self.position_type_combo.addItem(pos_type.value, pos_type)
        self.position_type_combo.currentTextChanged.connect(
            self.on_position_type_changed
        )
        type_layout.addWidget(self.position_type_combo)
        position_layout.addLayout(type_layout)

        # Format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.position_format_combo = QComboBox()
        self.position_format_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.position_format_combo.addItems(["d", "dm", "dms", "rad"])
        format_layout.addWidget(self.position_format_combo)
        self.format_layout = format_layout  # Store reference for visibility control
        position_layout.addLayout(format_layout)

        # Latitude
        lat_layout = QHBoxLayout()
        lat_layout.addWidget(QLabel("Lat (N):"))
        self.latitude_spin = QDoubleSpinBox()
        self.latitude_spin.setRange(-90.0, 90.0)
        self.latitude_spin.setDecimals(6)
        self.latitude_spin.setSuffix(" °")
        self.latitude_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lat_layout.addWidget(self.latitude_spin)
        self.lat_layout = lat_layout  # Store reference for visibility control
        position_layout.addLayout(lat_layout)

        # Longitude
        lon_layout = QHBoxLayout()
        lon_layout.addWidget(QLabel("Lon (E):"))
        self.longitude_spin = QDoubleSpinBox()
        self.longitude_spin.setRange(-180.0, 180.0)
        self.longitude_spin.setDecimals(6)
        self.longitude_spin.setSuffix(" °")
        self.longitude_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lon_layout.addWidget(self.longitude_spin)
        self.lon_layout = lon_layout  # Store reference for visibility control
        position_layout.addLayout(lon_layout)

        # Altitude
        alt_layout = QHBoxLayout()
        alt_layout.addWidget(QLabel("Alt  :"))
        self.altitude_spin = QDoubleSpinBox()
        self.altitude_spin.setRange(-1000.0, 50000.0)
        self.altitude_spin.setDecimals(1)
        self.altitude_spin.setSuffix(" m")
        self.altitude_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        alt_layout.addWidget(self.altitude_spin)
        self.alt_layout = alt_layout  # Store reference for visibility control
        position_layout.addLayout(alt_layout)

        # ECEF coordinates (hidden by default)
        # X
        x_layout = QHBoxLayout()
        self.x_label = QLabel("X:")
        x_layout.addWidget(self.x_label)
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-10000000.0, 10000000.0)
        self.x_spin.setDecimals(1)
        self.x_spin.setSuffix(" m")
        self.x_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        x_layout.addWidget(self.x_spin)
        self.x_layout = x_layout  # Store reference for visibility control
        position_layout.addLayout(x_layout)

        # Y
        y_layout = QHBoxLayout()
        self.y_label = QLabel("Y:")
        y_layout.addWidget(self.y_label)
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-10000000.0, 10000000.0)
        self.y_spin.setDecimals(1)
        self.y_spin.setSuffix(" m")
        self.y_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        y_layout.addWidget(self.y_spin)
        self.y_layout = y_layout  # Store reference for visibility control
        position_layout.addLayout(y_layout)

        # Z
        z_layout = QHBoxLayout()
        self.z_label = QLabel("Z:")
        z_layout.addWidget(self.z_label)
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setRange(-10000000.0, 10000000.0)
        self.z_spin.setDecimals(1)
        self.z_spin.setSuffix(" m")
        self.z_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        z_layout.addWidget(self.z_spin)
        self.z_layout = z_layout  # Store reference for visibility control
        position_layout.addLayout(z_layout)

        # Initially hide ECEF fields
        self.toggle_position_fields()

        # Add position group to left splitter
        left_splitter.addWidget(position_group)

        # Velocity Group
        velocity_group = QGroupBox("Initial Velocity")
        velocity_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #28a745;
            }
        """)
        velocity_layout = QVBoxLayout(velocity_group)
        velocity_layout.setSpacing(5)

        # Type
        vel_type_layout = QHBoxLayout()
        vel_type_layout.addWidget(QLabel("Type:"))
        self.velocity_type_combo = QComboBox()
        self.velocity_type_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        for vel_type in VelocityType:
            self.velocity_type_combo.addItem(vel_type.value, vel_type)
        self.velocity_type_combo.currentTextChanged.connect(
            self.on_velocity_type_changed
        )
        vel_type_layout.addWidget(self.velocity_type_combo)
        velocity_layout.addLayout(vel_type_layout)

        # Define velocity ranges first
        vel_min = -3000.0
        vel_max = 3000.0

        # Horizontal Speed with unit (SCU)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Hor. Speed:"))
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.0, vel_max)
        self.speed_spin.setDecimals(2)
        self.speed_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        speed_layout.addWidget(self.speed_spin)
        
        self.speed_unit_combo = QComboBox()
        self.speed_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.speed_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        speed_layout.addWidget(self.speed_unit_combo)
        self.speed_layout = speed_layout  # Store reference for visibility control
        velocity_layout.addLayout(speed_layout)

        # Vertical Speed (SCU) - uses same unit as horizontal speed
        up_layout = QHBoxLayout()
        up_layout.addWidget(QLabel("Ver. Speed:"))
        self.up_spin = QDoubleSpinBox()
        self.up_spin.setRange(vel_min, vel_max)
        self.up_spin.setDecimals(2)
        self.up_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        up_layout.addWidget(self.up_spin)
        self.up_layout = up_layout  # Store reference for visibility control
        velocity_layout.addLayout(up_layout)

        # Course with unit (SCU) - moved to bottom
        course_layout = QHBoxLayout()
        course_layout.addWidget(QLabel("Course:"))
        self.course_spin = QDoubleSpinBox()
        self.course_spin.setRange(0.0, 360.0)
        self.course_spin.setDecimals(2)
        self.course_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        course_layout.addWidget(self.course_spin)
        
        self.angle_unit_combo = QComboBox()
        self.angle_unit_combo.addItems(["degree", "rad"])
        self.angle_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        course_layout.addWidget(self.angle_unit_combo)
        self.course_layout = course_layout  # Store reference for visibility control
        velocity_layout.addLayout(course_layout)

        # ENU velocities (hidden by default)
        # East
        east_layout = QHBoxLayout()
        self.east_label = QLabel("East:")
        east_layout.addWidget(self.east_label)
        self.east_spin = QDoubleSpinBox()
        self.east_spin.setRange(vel_min, vel_max)
        self.east_spin.setDecimals(2)
        self.east_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        east_layout.addWidget(self.east_spin)
        
        self.east_unit_combo = QComboBox()
        self.east_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.east_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        east_layout.addWidget(self.east_unit_combo)
        self.east_layout = east_layout  # Store reference for visibility control
        velocity_layout.addLayout(east_layout)

        # North
        north_layout = QHBoxLayout()
        self.north_label = QLabel("North:")
        north_layout.addWidget(self.north_label)
        self.north_spin = QDoubleSpinBox()
        self.north_spin.setRange(vel_min, vel_max)
        self.north_spin.setDecimals(2)
        self.north_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        north_layout.addWidget(self.north_spin)
        
        self.north_unit_combo = QComboBox()
        self.north_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.north_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        north_layout.addWidget(self.north_unit_combo)
        self.north_layout = north_layout  # Store reference for visibility control
        velocity_layout.addLayout(north_layout)
        
        # Up for ENU
        up_enu_layout = QHBoxLayout()
        self.up_enu_label = QLabel("Up:")
        up_enu_layout.addWidget(self.up_enu_label)
        self.up_enu_spin = QDoubleSpinBox()
        self.up_enu_spin.setRange(vel_min, vel_max)
        self.up_enu_spin.setDecimals(2)
        self.up_enu_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        up_enu_layout.addWidget(self.up_enu_spin)
        
        self.up_enu_unit_combo = QComboBox()
        self.up_enu_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.up_enu_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        up_enu_layout.addWidget(self.up_enu_unit_combo)
        self.up_enu_layout = up_enu_layout  # Store reference for visibility control
        velocity_layout.addLayout(up_enu_layout)

        # ECEF velocities (hidden by default)
        # Vx
        vx_layout = QHBoxLayout()
        self.vx_label = QLabel("Vx:")
        vx_layout.addWidget(self.vx_label)
        self.vx_spin = QDoubleSpinBox()
        self.vx_spin.setRange(vel_min, vel_max)
        self.vx_spin.setDecimals(2)
        self.vx_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vx_layout.addWidget(self.vx_spin)
        
        self.vx_unit_combo = QComboBox()
        self.vx_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.vx_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        vx_layout.addWidget(self.vx_unit_combo)
        self.vx_layout = vx_layout  # Store reference for visibility control
        velocity_layout.addLayout(vx_layout)

        # Vy
        vy_layout = QHBoxLayout()
        self.vy_label = QLabel("Vy:")
        vy_layout.addWidget(self.vy_label)
        self.vy_spin = QDoubleSpinBox()
        self.vy_spin.setRange(vel_min, vel_max)
        self.vy_spin.setDecimals(2)
        self.vy_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vy_layout.addWidget(self.vy_spin)
        
        self.vy_unit_combo = QComboBox()
        self.vy_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.vy_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        vy_layout.addWidget(self.vy_unit_combo)
        self.vy_layout = vy_layout  # Store reference for visibility control
        velocity_layout.addLayout(vy_layout)

        # Vz
        vz_layout = QHBoxLayout()
        self.vz_label = QLabel("Vz:")
        vz_layout.addWidget(self.vz_label)
        self.vz_spin = QDoubleSpinBox()
        self.vz_spin.setRange(vel_min, vel_max)
        self.vz_spin.setDecimals(2)
        self.vz_spin.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        vz_layout.addWidget(self.vz_spin)
        
        self.vz_unit_combo = QComboBox()
        self.vz_unit_combo.addItems(["mps", "kph", "knot", "mph"])
        self.vz_unit_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        vz_layout.addWidget(self.vz_unit_combo)
        self.vz_layout = vz_layout  # Store reference for visibility control
        velocity_layout.addLayout(vz_layout)

        # Initially hide ENU and ECEF fields
        self.toggle_velocity_fields()

        # Add velocity group to left splitter
        left_splitter.addWidget(velocity_group)

        # Add trajectory section to left splitter
        self.setup_trajectory_section_left(left_splitter)

        # Add left splitter to main splitter
        main_splitter.addWidget(left_splitter)

        # Right side: Map (takes up most of the space)
        self.setup_map_section_right(main_splitter)

        # Set initial proportions: 1% for left controls, 99% for map
        main_splitter.setSizes([10, 990])  # Initial sizes (will be proportional)
        main_splitter.setStretchFactor(0, 0)  # Left side stretch factor
        main_splitter.setStretchFactor(1, 1)  # Right side (map) stretch factor

        parent_layout.addWidget(main_splitter)

    def setup_trajectory_section_left(self, parent_layout):
        """Setup trajectory segments section for left side."""
        trajectory_group = QGroupBox("Trajectory Segments")
        trajectory_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #ffc107;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #856404;
            }
        """)
        trajectory_layout = QVBoxLayout(trajectory_group)
        trajectory_layout.setSpacing(5)

        # Trajectory controls - compact horizontal layout
        traj_controls = QGridLayout()
        traj_controls.setSpacing(3)
        
        self.add_segment_button = QPushButton("Add")
        self.add_segment_button.clicked.connect(self.add_trajectory_segment)
        self.add_segment_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        traj_controls.addWidget(self.add_segment_button, 0, 0)

        self.edit_segment_button = QPushButton("Edit")
        self.edit_segment_button.clicked.connect(self.edit_trajectory_segment)
        self.edit_segment_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        traj_controls.addWidget(self.edit_segment_button, 0, 1)

        self.remove_segment_button = QPushButton("Remove")
        self.remove_segment_button.clicked.connect(self.remove_trajectory_segment)
        self.remove_segment_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        traj_controls.addWidget(self.remove_segment_button, 1, 0)

        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self.clear_all_segments)
        self.clear_all_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        traj_controls.addWidget(self.clear_all_button, 1, 1)
        
        trajectory_layout.addLayout(traj_controls)

        # Trajectory list - dynamic sizing
        self.trajectory_list = QListWidget()
        self.trajectory_list.setMinimumHeight(100)  # Small minimum, but no maximum
        self.trajectory_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        trajectory_layout.addWidget(self.trajectory_list)

        # Add to parent layout
        parent_layout.addWidget(trajectory_group)


    def setup_map_section_right(self, parent_layout):
        """Setup map section for right side with maximum space."""
        map_group = QGroupBox("Interactive Map & Trajectory Visualization")
        map_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                border: 2px solid #17a2b8;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #17a2b8;
            }
        """)
        map_layout = QVBoxLayout(map_group)
        map_layout.setSpacing(5)

        # Map controls - more compact (removed checkboxes as map and trajectory are always visible)
        map_controls = QHBoxLayout()
        map_controls.setSpacing(5)

        self.clear_trajectory_btn = QPushButton("Clear")
        map_controls.addWidget(self.clear_trajectory_btn)

        self.center_map_button = QPushButton("Center")
        self.center_map_button.clicked.connect(self.center_map_on_position)
        map_controls.addWidget(self.center_map_button)

        map_controls.addStretch()
        map_layout.addLayout(map_controls)

        # Location selection controls - more compact
        location_controls = QHBoxLayout()
        location_controls.setSpacing(5)
        
        location_controls.addWidget(QLabel("Quick:"))
        self.preset_location_combo = QComboBox()
        self.preset_location_combo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setup_preset_locations()
        self.preset_location_combo.currentTextChanged.connect(self.on_preset_location_selected)
        location_controls.addWidget(self.preset_location_combo)

        # Location search
        self.location_search_edit = QLineEdit()
        self.location_search_edit.setPlaceholderText("Search location...")
        self.location_search_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.location_search_edit.returnPressed.connect(self.search_location)
        location_controls.addWidget(self.location_search_edit)

        self.search_location_button = QPushButton("Go")
        self.search_location_button.clicked.connect(self.search_location)
        location_controls.addWidget(self.search_location_button)

        location_controls.addStretch()
        map_layout.addLayout(location_controls)

        # Map widget - takes maximum space
        try:
            self.map_widget = EmbeddedMapWidget(
                self,
                self.config.trajectory.init_position.latitude,
                self.config.trajectory.init_position.longitude,
            )
            self.map_widget.coordinates_changed.connect(self.on_map_coordinates_changed)
            
            # Make map widget fully expandable
            self.map_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            
            # Connect map controls
            self.clear_trajectory_btn.clicked.connect(self.map_widget.clear_trajectory)
            
            map_layout.addWidget(self.map_widget)
        except Exception as e:
            error(f"Failed to create map widget: {e}")
            map_placeholder = QLabel("Map not available - using coordinate input only")
            map_placeholder.setStyleSheet(
                "background-color: #f0f0f0; padding: 20px; text-align: center;"
            )
            # Let placeholder size dynamically too
            map_layout.addWidget(map_placeholder)

        # Add to parent splitter
        parent_layout.addWidget(map_group)



    def connect_signals(self):
        """Connect widget signals."""
        self.name_edit.textChanged.connect(self.update_config)
        self.position_type_combo.currentTextChanged.connect(self.update_config)
        self.position_format_combo.currentTextChanged.connect(self.update_config)
        self.latitude_spin.valueChanged.connect(self.update_config)
        self.longitude_spin.valueChanged.connect(self.update_config)
        self.altitude_spin.valueChanged.connect(self.update_config)
        self.x_spin.valueChanged.connect(self.update_config)
        self.y_spin.valueChanged.connect(self.update_config)
        self.z_spin.valueChanged.connect(self.update_config)

        self.velocity_type_combo.currentTextChanged.connect(self.update_config)
        self.speed_spin.valueChanged.connect(self.update_config)
        self.course_spin.valueChanged.connect(self.update_config)
        self.up_spin.valueChanged.connect(self.update_config)
        self.east_spin.valueChanged.connect(self.update_config)
        self.north_spin.valueChanged.connect(self.update_config)
        self.up_enu_spin.valueChanged.connect(self.update_config)
        self.vx_spin.valueChanged.connect(self.update_config)
        self.vy_spin.valueChanged.connect(self.update_config)
        self.vz_spin.valueChanged.connect(self.update_config)
        # SCU unit change signals
        self.speed_unit_combo.currentTextChanged.connect(self.on_speed_unit_changed)
        self.angle_unit_combo.currentTextChanged.connect(self.on_angle_unit_changed)
        
        # ENU unit change signals
        self.east_unit_combo.currentTextChanged.connect(self.on_east_unit_changed)
        self.north_unit_combo.currentTextChanged.connect(self.on_north_unit_changed)
        self.up_enu_unit_combo.currentTextChanged.connect(self.on_up_enu_unit_changed)
        
        # ECEF unit change signals
        self.vx_unit_combo.currentTextChanged.connect(self.on_vx_unit_changed)
        self.vy_unit_combo.currentTextChanged.connect(self.on_vy_unit_changed)
        self.vz_unit_combo.currentTextChanged.connect(self.on_vz_unit_changed)

        # Connect coordinate changes to map
        self.latitude_spin.valueChanged.connect(self.update_map_from_spinboxes)
        self.longitude_spin.valueChanged.connect(self.update_map_from_spinboxes)

    def on_position_type_changed(self):
        """Handle position type change."""
        self.toggle_position_fields()
        self.update_config()

    def on_velocity_type_changed(self):
        """Handle velocity type change."""
        self.toggle_velocity_fields()
        self.update_config()

    def toggle_position_fields(self):
        """Show/hide position fields based on type."""
        pos_type = self.position_type_combo.currentData()
        is_ecef = pos_type == PositionType.ECEF

        # LLA fields - show/hide widgets in their layouts
        self._set_layout_visible(self.format_layout, not is_ecef)
        self._set_layout_visible(self.lat_layout, not is_ecef)
        self._set_layout_visible(self.lon_layout, not is_ecef)
        self._set_layout_visible(self.alt_layout, not is_ecef)

        # ECEF fields - show/hide widgets in their layouts
        self._set_layout_visible(self.x_layout, is_ecef)
        self._set_layout_visible(self.y_layout, is_ecef)
        self._set_layout_visible(self.z_layout, is_ecef)

    def _set_layout_visible(self, layout, visible):
        """Helper method to show/hide all widgets in a layout."""
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(visible)

    def toggle_velocity_fields(self):
        """Show/hide velocity fields based on type."""
        vel_type = self.velocity_type_combo.currentData()

        # SCU fields
        is_scu = vel_type == VelocityType.SCU
        self._set_layout_visible(self.speed_layout, is_scu)
        self._set_layout_visible(self.course_layout, is_scu)
        self._set_layout_visible(self.up_layout, is_scu)

        # ENU fields
        is_enu = vel_type == VelocityType.ENU
        self._set_layout_visible(self.east_layout, is_enu)
        self._set_layout_visible(self.north_layout, is_enu)
        self._set_layout_visible(self.up_enu_layout, is_enu)

        # ECEF fields
        is_ecef = vel_type == VelocityType.ECEF
        self._set_layout_visible(self.vx_layout, is_ecef)
        self._set_layout_visible(self.vy_layout, is_ecef)
        self._set_layout_visible(self.vz_layout, is_ecef)

    def on_speed_unit_changed(self, new_unit):
        """Handle speed unit change with conversion for SCU type."""
        if not hasattr(self, '_current_speed_unit'):
            self._current_speed_unit = "mps"  # Default unit
        
        old_unit = self._current_speed_unit
        if old_unit == new_unit:
            return
            
        # Convert current horizontal speed value from old unit to new unit
        current_speed = self.speed_spin.value()
        converted_speed = self.convert_speed(current_speed, old_unit, new_unit)
        
        # Convert current vertical speed value (uses same unit as horizontal)
        current_up = self.up_spin.value()
        converted_up = self.convert_speed(current_up, old_unit, new_unit)
        
        # Update the spinboxes with converted values
        self.speed_spin.blockSignals(True)
        self.up_spin.blockSignals(True)
        
        self.speed_spin.setValue(converted_speed)
        self.up_spin.setValue(converted_up)
        
        self.speed_spin.blockSignals(False)
        self.up_spin.blockSignals(False)
        
        # Update the stored current unit
        self._current_speed_unit = new_unit
        
        # Update config and map
        self.update_config()
        info(f"Speed unit changed from {old_unit} to {new_unit}: Hor.Speed {current_speed:.2f} -> {converted_speed:.2f}, Ver.Speed {current_up:.2f} -> {converted_up:.2f}")

    def on_angle_unit_changed(self, new_unit):
        """Handle angle unit change with conversion."""
        if not hasattr(self, '_current_angle_unit'):
            self._current_angle_unit = "degree"  # Default unit
        
        old_unit = self._current_angle_unit
        if old_unit == new_unit:
            return
            
        # Convert current course value from old unit to new unit
        current_course = self.course_spin.value()
        converted_course = self.convert_angle(current_course, old_unit, new_unit)
        
        # Update the spinbox with converted value and range
        self.course_spin.blockSignals(True)
        if new_unit == "rad":
            self.course_spin.setRange(0.0, 2 * 3.14159)  # 0 to 2π
            self.course_spin.setDecimals(4)
        else:  # degree
            self.course_spin.setRange(0.0, 360.0)
            self.course_spin.setDecimals(2)
        
        self.course_spin.setValue(converted_course)
        self.course_spin.blockSignals(False)
        
        # Update the stored current unit
        self._current_angle_unit = new_unit
        
        # Update config and map
        self.update_config()
        info(f"Angle unit changed from {old_unit} to {new_unit}: {current_course:.4f} -> {converted_course:.4f}")

    # ENU unit change handlers
    def on_east_unit_changed(self, new_unit):
        """Handle east unit change with conversion."""
        if not hasattr(self, '_current_east_unit'):
            self._current_east_unit = "mps"
        
        old_unit = self._current_east_unit
        if old_unit == new_unit:
            return
        
        current_east = self.east_spin.value()
        converted_east = self.convert_speed(current_east, old_unit, new_unit)
        
        self.east_spin.blockSignals(True)
        self.east_spin.setValue(converted_east)
        self.east_spin.blockSignals(False)
        
        self._current_east_unit = new_unit
        self.update_config()
        info(f"East unit changed from {old_unit} to {new_unit}: {current_east:.2f} -> {converted_east:.2f}")

    def on_north_unit_changed(self, new_unit):
        """Handle north unit change with conversion."""
        if not hasattr(self, '_current_north_unit'):
            self._current_north_unit = "mps"
        
        old_unit = self._current_north_unit
        if old_unit == new_unit:
            return
        
        current_north = self.north_spin.value()
        converted_north = self.convert_speed(current_north, old_unit, new_unit)
        
        self.north_spin.blockSignals(True)
        self.north_spin.setValue(converted_north)
        self.north_spin.blockSignals(False)
        
        self._current_north_unit = new_unit
        self.update_config()
        info(f"North unit changed from {old_unit} to {new_unit}: {current_north:.2f} -> {converted_north:.2f}")

    def on_up_enu_unit_changed(self, new_unit):
        """Handle up (ENU) unit change with conversion."""
        if not hasattr(self, '_current_up_enu_unit'):
            self._current_up_enu_unit = "mps"
        
        old_unit = self._current_up_enu_unit
        if old_unit == new_unit:
            return
        
        current_up = self.up_enu_spin.value()
        converted_up = self.convert_speed(current_up, old_unit, new_unit)
        
        self.up_enu_spin.blockSignals(True)
        self.up_enu_spin.setValue(converted_up)
        self.up_enu_spin.blockSignals(False)
        
        self._current_up_enu_unit = new_unit
        self.update_config()
        info(f"Up (ENU) unit changed from {old_unit} to {new_unit}: {current_up:.2f} -> {converted_up:.2f}")

    # ECEF unit change handlers
    def on_vx_unit_changed(self, new_unit):
        """Handle Vx unit change with conversion."""
        if not hasattr(self, '_current_vx_unit'):
            self._current_vx_unit = "mps"
        
        old_unit = self._current_vx_unit
        if old_unit == new_unit:
            return
        
        current_vx = self.vx_spin.value()
        converted_vx = self.convert_speed(current_vx, old_unit, new_unit)
        
        self.vx_spin.blockSignals(True)
        self.vx_spin.setValue(converted_vx)
        self.vx_spin.blockSignals(False)
        
        self._current_vx_unit = new_unit
        self.update_config()
        info(f"Vx unit changed from {old_unit} to {new_unit}: {current_vx:.2f} -> {converted_vx:.2f}")

    def on_vy_unit_changed(self, new_unit):
        """Handle Vy unit change with conversion."""
        if not hasattr(self, '_current_vy_unit'):
            self._current_vy_unit = "mps"
        
        old_unit = self._current_vy_unit
        if old_unit == new_unit:
            return
        
        current_vy = self.vy_spin.value()
        converted_vy = self.convert_speed(current_vy, old_unit, new_unit)
        
        self.vy_spin.blockSignals(True)
        self.vy_spin.setValue(converted_vy)
        self.vy_spin.blockSignals(False)
        
        self._current_vy_unit = new_unit
        self.update_config()
        info(f"Vy unit changed from {old_unit} to {new_unit}: {current_vy:.2f} -> {converted_vy:.2f}")

    def on_vz_unit_changed(self, new_unit):
        """Handle Vz unit change with conversion."""
        if not hasattr(self, '_current_vz_unit'):
            self._current_vz_unit = "mps"
        
        old_unit = self._current_vz_unit
        if old_unit == new_unit:
            return
        
        current_vz = self.vz_spin.value()
        converted_vz = self.convert_speed(current_vz, old_unit, new_unit)
        
        self.vz_spin.blockSignals(True)
        self.vz_spin.setValue(converted_vz)
        self.vz_spin.blockSignals(False)
        
        self._current_vz_unit = new_unit
        self.update_config()
        info(f"Vz unit changed from {old_unit} to {new_unit}: {current_vz:.2f} -> {converted_vz:.2f}")

    def convert_speed(self, value, from_unit, to_unit):
        """Convert speed between different units."""
        # Convert to m/s first (base unit)
        if from_unit == "mps" or from_unit == "m/s":
            ms_value = value
        elif from_unit == "kph" or from_unit == "km/h":
            ms_value = value / 3.6
        elif from_unit == "knot":
            ms_value = value * 0.514444
        elif from_unit == "mph":
            ms_value = value * 0.44704
        else:
            ms_value = value  # Default to m/s
        
        # Convert from m/s to target unit
        if to_unit == "mps" or to_unit == "m/s":
            return ms_value
        elif to_unit == "kph" or to_unit == "km/h":
            return ms_value * 3.6
        elif to_unit == "knot":
            return ms_value / 0.514444
        elif to_unit == "mph":
            return ms_value / 0.44704
        else:
            return ms_value  # Default to m/s

    def convert_angle(self, value, from_unit, to_unit):
        """Convert angle between degrees and radians."""
        if from_unit == to_unit:
            return value
        
        if (from_unit == "degree" or from_unit == "deg") and to_unit == "rad":
            return value * 3.14159 / 180.0
        elif from_unit == "rad" and (to_unit == "degree" or to_unit == "deg"):
            return value * 180.0 / 3.14159
        else:
            return value  # No conversion needed

    def setup_preset_locations(self):
        """Set up preset location dropdown."""
        self.preset_locations = {
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
            "Cape Town, South Africa": (-33.9249, 18.4241),
            "Mumbai, India": (19.0760, 72.8777),
            "São Paulo, Brazil": (-23.5505, -46.6333),
            "Cairo, Egypt": (30.0444, 31.2357),
            "Mexico City, Mexico": (19.4326, -99.1332),
        }

        self.preset_location_combo.addItem("-- Select Location --")
        self.preset_location_combo.addItem("Current Location")
        for name in sorted(self.preset_locations.keys()):
            self.preset_location_combo.addItem(name)

    def on_preset_location_selected(self, location_name):
        """Handle preset location selection."""
        if location_name == "Current Location":
            self.get_current_location()
        elif location_name in self.preset_locations:
            log_button_click("Preset Location Selected", "Trajectory", location_name)
            lat, lon = self.preset_locations[location_name]
            self.latitude_spin.setValue(lat)
            self.longitude_spin.setValue(lon)
            info(f"Set location to {location_name}: {lat:.6f}, {lon:.6f}")

    def get_current_location(self):
        """Attempt to get current GPS location."""
        log_button_click("Get Current Location", "Trajectory")
        
        try:
            # Try to get location using various methods
            location = self.detect_current_location()
            if location:
                lat, lon = location
                self.latitude_spin.setValue(lat)
                self.longitude_spin.setValue(lon)
                info(f"Current location detected: {lat:.6f}, {lon:.6f}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Location Detection",
                    "Current location detection is not available.\n\n"
                    "To enable GPS location:\n"
                    "• Enable location services on your device\n"
                    "• Grant location permission to the application\n"
                    "• Ensure you have an internet connection\n\n"
                    "For now, please use preset locations or enter coordinates manually."
                )
        except Exception as e:
            error(f"Failed to get current location: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Location Error",
                f"Failed to detect current location: {str(e)}\n\n"
                "Please use preset locations or enter coordinates manually."
            )

    def detect_current_location(self):
        """Detect current location using available methods."""
        # Method 1: Try IP-based geolocation (requires internet)
        try:
            import requests
            response = requests.get('http://ipapi.co/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'latitude' in data and 'longitude' in data:
                    lat = float(data['latitude'])
                    lon = float(data['longitude'])
                    info(f"Location detected via IP: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}")
                    return (lat, lon)
        except Exception as e:
            debug(f"IP geolocation failed: {e}")

        # Method 2: Try other geolocation services
        try:
            import requests
            response = requests.get('http://ip-api.com/json/', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    lat = float(data['lat'])
                    lon = float(data['lon'])
                    info(f"Location detected via IP-API: {data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}")
                    return (lat, lon)
        except Exception as e:
            debug(f"IP-API geolocation failed: {e}")

        return None

    def search_location(self):
        """Search for a location by name."""
        location_text = self.location_search_edit.text().strip()
        if not location_text:
            return

        log_button_click("Search Location", "Trajectory", location_text)

        try:
            # Try to geocode the location
            coordinates = self.geocode_location(location_text)
            if coordinates:
                lat, lon = coordinates
                self.latitude_spin.setValue(lat)
                self.longitude_spin.setValue(lon)
                self.location_search_edit.clear()
                info(f"Location found: {location_text} -> {lat:.6f}, {lon:.6f}")
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    "Location Search",
                    f"Could not find location: '{location_text}'\n\n"
                    "Try using:\n"
                    "• City name (e.g., 'Paris')\n"
                    "• City, Country (e.g., 'Tokyo, Japan')\n"
                    "• Full address\n\n"
                    "Or select from preset locations above."
                )
        except Exception as e:
            error(f"Location search failed: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Search Error",
                f"Location search failed: {str(e)}\n\n"
                "Please check your internet connection or use preset locations."
            )

    def geocode_location(self, location_text):
        """Geocode a location name to coordinates."""
        try:
            # Method 1: Try Nominatim (OpenStreetMap) - free, no API key needed
            import requests
            import urllib.parse
            
            encoded_location = urllib.parse.quote(location_text)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
            
            headers = {
                'User-Agent': 'SignalSim-Trajectory-App/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    debug(f"Geocoded '{location_text}' to {lat}, {lon}")
                    return (lat, lon)
        except Exception as e:
            debug(f"Nominatim geocoding failed: {e}")

        # Method 2: Check if it matches any preset locations (fuzzy matching)
        location_lower = location_text.lower()
        for preset_name, coords in self.preset_locations.items():
            if location_lower in preset_name.lower() or preset_name.lower() in location_lower:
                debug(f"Matched '{location_text}' to preset '{preset_name}'")
                return coords

        return None

    def center_map_on_position(self):
        """Center map on current position."""
        if hasattr(self, "map_widget"):
            lat = self.latitude_spin.value()
            lon = self.longitude_spin.value()
            self.map_widget.set_coordinates(lat, lon)

    def on_map_coordinates_changed(self, lat, lon):
        """Handle coordinate changes from map."""
        info(f"Map coordinates changed: {lat:.6f}, {lon:.6f}")

        # Update spin boxes without triggering signals
        self.latitude_spin.blockSignals(True)
        self.longitude_spin.blockSignals(True)

        self.latitude_spin.setValue(lat)
        self.longitude_spin.setValue(lon)

        self.latitude_spin.blockSignals(False)
        self.longitude_spin.blockSignals(False)

        # Update config
        self.update_config()

    def add_trajectory_segment(self):
        """Add a new trajectory segment."""
        log_button_click("Add Trajectory Segment", "Trajectory")
        dialog = TrajectorySegmentDialog(self)
        dialog.segment_created.connect(self.on_segment_created)
        dialog.exec()

    def edit_trajectory_segment(self):
        """Edit selected trajectory segment."""
        current_row = self.trajectory_list.currentRow()
        if current_row >= 0 and current_row < len(
            self.config.trajectory.trajectory_list
        ):
            segment = self.config.trajectory.trajectory_list[current_row]
            dialog = TrajectorySegmentDialog(self, segment)
            dialog.segment_created.connect(
                lambda s: self.on_segment_edited(current_row, s)
            )
            dialog.exec()

    def remove_trajectory_segment(self):
        """Remove selected trajectory segment."""
        current_row = self.trajectory_list.currentRow()
        if current_row >= 0:
            del self.config.trajectory.trajectory_list[current_row]
            self.refresh_trajectory_list()
            self.update_config()

    def on_segment_created(self, segment):
        """Handle new segment creation."""
        info(f"New trajectory segment created: {segment.type.value}")
        
        # Add to configuration
        self.config.trajectory.trajectory_list.append(segment)
        
        # Refresh trajectory list display
        self.refresh_trajectory_list()
        
        # Update map with new trajectory
        self.update_map_trajectory()
        
        # Trigger config update
        self.update_config()

    def on_segment_edited(self, index, segment):
        """Handle segment editing."""
        self.config.trajectory.trajectory_list[index] = segment
        self.refresh_trajectory_list()
        self.update_config()

    def clear_all_segments(self):
        """Clear all trajectory segments."""
        log_button_click("Clear All Segments", "Trajectory")

        # Clear list widget
        self.trajectory_list.clear()

        # Clear config
        self.config.trajectory.trajectory_list.clear()
        info("Cleared all trajectory segments")

        # Update map
        self.update_map_trajectory()

        self.config_changed.emit()

    def update_map_from_spinboxes(self):
        """Update map when coordinates change in spinboxes."""
        if hasattr(self, "map_widget"):
            lat = self.latitude_spin.value()
            lon = self.longitude_spin.value()
            self.map_widget.set_coordinates(lat, lon)

    def update_map_trajectory(self):
        """Update map with current trajectory data."""
        try:
            if hasattr(self, "map_widget"):
                # Convert values to standard units for the map (m/s and degrees)
                speed_ms = self.convert_speed(
                    self.speed_spin.value(), 
                    self._current_speed_unit, 
                    "mps"
                )
                
                # Convert course to degrees for map if needed
                if self._current_angle_unit == "rad":
                    course_deg = self.convert_angle(
                        self.course_spin.value(), 
                        "rad", 
                        "degree"
                    )
                else:
                    course_deg = self.course_spin.value()  # Already in degrees
                
                initial_velocity = {
                    "speed": speed_ms,
                    "course": course_deg,
                }
                self.map_widget.set_trajectory_data(
                    self.config.trajectory.trajectory_list, initial_velocity
                )
                debug(
                    f"Updated map with {len(self.config.trajectory.trajectory_list)} trajectory segments"
                )
        except Exception as e:
            error(f"Failed to update map trajectory: {str(e)}")

    def refresh_trajectory_list(self):
        """Refresh the trajectory list display."""
        self.trajectory_list.clear()
        for i, segment in enumerate(self.config.trajectory.trajectory_list):
            parts = [f"{i + 1}. {segment.type.value}"]
            if segment.time is not None:
                parts.append(f"{segment.time:.3f}s")
            if segment.acceleration is not None:
                parts.append(f"acc: {segment.acceleration:.3f} m/s²")
            if segment.speed is not None:
                parts.append(f"speed: {segment.speed:.3f} m/s")
            if segment.rate is not None:
                parts.append(f"rate: {segment.rate:.3f} m/s³")
            if segment.angle is not None:
                parts.append(f"angle: {segment.angle:.3f}°")
            if segment.radius is not None:
                parts.append(f"radius: {segment.radius:.3f} m")
            item_text = " - ".join(parts)
            self.trajectory_list.addItem(item_text)

    def update_config(self):
        """Update configuration from widget values."""
        # Update trajectory name
        self.config.trajectory.name = self.name_edit.text()

        # Update position
        self.config.trajectory.init_position.type = (
            self.position_type_combo.currentData()
        )
        self.config.trajectory.init_position.format = (
            self.position_format_combo.currentText()
        )
        self.config.trajectory.init_position.latitude = self.latitude_spin.value()
        self.config.trajectory.init_position.longitude = self.longitude_spin.value()
        self.config.trajectory.init_position.altitude = self.altitude_spin.value()
        self.config.trajectory.init_position.x = self.x_spin.value()
        self.config.trajectory.init_position.y = self.y_spin.value()
        self.config.trajectory.init_position.z = self.z_spin.value()

        # Update velocity
        self.config.trajectory.init_velocity.type = (
            self.velocity_type_combo.currentData()
        )
        # Store the current display units in config based on velocity type
        vel_type = self.config.trajectory.init_velocity.type
        if vel_type == VelocityType.SCU:
            # For SCU, only store speedUnit and angleUnit
            self.config.trajectory.init_velocity.speed_unit = self._current_speed_unit
            self.config.trajectory.init_velocity.angle_unit = self._current_angle_unit
        elif vel_type == VelocityType.ENU:
            # For ENU, only store eastUnit, northUnit, upUnit
            self.config.trajectory.init_velocity.east_unit = self._current_east_unit
            self.config.trajectory.init_velocity.north_unit = self._current_north_unit
            self.config.trajectory.init_velocity.up_unit = self._current_up_enu_unit
        elif vel_type == VelocityType.ECEF:
            # For ECEF, only store xUnit, yUnit, zUnit
            self.config.trajectory.init_velocity.x_unit = self._current_vx_unit
            self.config.trajectory.init_velocity.y_unit = self._current_vy_unit
            self.config.trajectory.init_velocity.z_unit = self._current_vz_unit

        # Update velocity values based on type
        vel_type = self.config.trajectory.init_velocity.type
        if vel_type == VelocityType.SCU:
            # Store the actual display values (with their units stored separately)
            self.config.trajectory.init_velocity.speed = self.speed_spin.value()
            self.config.trajectory.init_velocity.course = self.course_spin.value()
            self.config.trajectory.init_velocity.up = self.up_spin.value()
        elif vel_type == VelocityType.ENU:
            self.config.trajectory.init_velocity.east = self.east_spin.value()
            self.config.trajectory.init_velocity.north = self.north_spin.value()
            self.config.trajectory.init_velocity.up = self.up_enu_spin.value()
        elif vel_type == VelocityType.ECEF:
            self.config.trajectory.init_velocity.x = self.vx_spin.value()
            self.config.trajectory.init_velocity.y = self.vy_spin.value()
            self.config.trajectory.init_velocity.z = self.vz_spin.value()

        # Update position values based on type
        pos_type = self.config.trajectory.init_position.type
        if pos_type == PositionType.LLA:
            self.config.trajectory.init_position.latitude = self.latitude_spin.value()
            self.config.trajectory.init_position.longitude = self.longitude_spin.value()
            self.config.trajectory.init_position.altitude = self.altitude_spin.value()
        elif pos_type == PositionType.ECEF:
            self.config.trajectory.init_position.x = self.x_spin.value()
            self.config.trajectory.init_position.y = self.y_spin.value()
            self.config.trajectory.init_position.z = self.z_spin.value()

        # Update map with trajectory data
        self.update_map_trajectory()

        self.config_changed.emit()

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals to prevent recursive updates
        self.blockSignals(True)

        try:
            # Set trajectory name
            self.name_edit.setText(self.config.trajectory.name)

            # Set position
            for i in range(self.position_type_combo.count()):
                if (
                    self.position_type_combo.itemData(i)
                    == self.config.trajectory.init_position.type
                ):
                    self.position_type_combo.setCurrentIndex(i)
                    break

            format_index = self.position_format_combo.findText(
                self.config.trajectory.init_position.format
            )
            if format_index >= 0:
                self.position_format_combo.setCurrentIndex(format_index)

            self.latitude_spin.setValue(self.config.trajectory.init_position.latitude)
            self.longitude_spin.setValue(self.config.trajectory.init_position.longitude)
            self.altitude_spin.setValue(self.config.trajectory.init_position.altitude)
            self.x_spin.setValue(self.config.trajectory.init_position.x or 0)
            self.y_spin.setValue(self.config.trajectory.init_position.y or 0)
            self.z_spin.setValue(self.config.trajectory.init_position.z or 0)

            # Set velocity
            for i in range(self.velocity_type_combo.count()):
                if (
                    self.velocity_type_combo.itemData(i)
                    == self.config.trajectory.init_velocity.type
                ):
                    self.velocity_type_combo.setCurrentIndex(i)
                    break

            # Set values directly from config (they are stored with their units)
            self.speed_spin.setValue(self.config.trajectory.init_velocity.speed or 0)
            self.course_spin.setValue(self.config.trajectory.init_velocity.course or 0)
            self.up_spin.setValue(self.config.trajectory.init_velocity.up or 0)
            self.east_spin.setValue(self.config.trajectory.init_velocity.east or 0)
            self.north_spin.setValue(self.config.trajectory.init_velocity.north or 0)
            self.up_enu_spin.setValue(self.config.trajectory.init_velocity.up or 0)
            self.vx_spin.setValue(self.config.trajectory.init_velocity.x or 0)
            self.vy_spin.setValue(self.config.trajectory.init_velocity.y or 0)
            self.vz_spin.setValue(self.config.trajectory.init_velocity.z or 0)

            # Set SCU units
            speed_unit = getattr(self.config.trajectory.init_velocity, 'speed_unit', 'mps')
            speed_unit_index = self.speed_unit_combo.findText(speed_unit)
            if speed_unit_index >= 0:
                self.speed_unit_combo.setCurrentIndex(speed_unit_index)
            self._current_speed_unit = speed_unit  # Update tracking

            angle_unit = getattr(self.config.trajectory.init_velocity, 'angle_unit', 'degree')
            angle_unit_index = self.angle_unit_combo.findText(angle_unit)
            if angle_unit_index >= 0:
                self.angle_unit_combo.setCurrentIndex(angle_unit_index)
            self._current_angle_unit = angle_unit  # Update tracking

            # Set ENU units
            east_unit = getattr(self.config.trajectory.init_velocity, 'east_unit', 'mps')
            east_unit_index = self.east_unit_combo.findText(east_unit)
            if east_unit_index >= 0:
                self.east_unit_combo.setCurrentIndex(east_unit_index)
            self._current_east_unit = east_unit

            north_unit = getattr(self.config.trajectory.init_velocity, 'north_unit', 'mps')
            north_unit_index = self.north_unit_combo.findText(north_unit)
            if north_unit_index >= 0:
                self.north_unit_combo.setCurrentIndex(north_unit_index)
            self._current_north_unit = north_unit

            up_enu_unit = getattr(self.config.trajectory.init_velocity, 'up_unit', 'mps')
            up_enu_unit_index = self.up_enu_unit_combo.findText(up_enu_unit)
            if up_enu_unit_index >= 0:
                self.up_enu_unit_combo.setCurrentIndex(up_enu_unit_index)
            self._current_up_enu_unit = up_enu_unit

            # Set ECEF units
            vx_unit = getattr(self.config.trajectory.init_velocity, 'x_unit', 'mps')
            vx_unit_index = self.vx_unit_combo.findText(vx_unit)
            if vx_unit_index >= 0:
                self.vx_unit_combo.setCurrentIndex(vx_unit_index)
            self._current_vx_unit = vx_unit

            vy_unit = getattr(self.config.trajectory.init_velocity, 'y_unit', 'mps')
            vy_unit_index = self.vy_unit_combo.findText(vy_unit)
            if vy_unit_index >= 0:
                self.vy_unit_combo.setCurrentIndex(vy_unit_index)
            self._current_vy_unit = vy_unit

            vz_unit = getattr(self.config.trajectory.init_velocity, 'z_unit', 'mps')
            vz_unit_index = self.vz_unit_combo.findText(vz_unit)
            if vz_unit_index >= 0:
                self.vz_unit_combo.setCurrentIndex(vz_unit_index)
            self._current_vz_unit = vz_unit

            # Update map with current coordinates
            if hasattr(self, "map_widget"):
                self.map_widget.set_coordinates(
                    self.config.trajectory.init_position.latitude,
                    self.config.trajectory.init_position.longitude,
                )

            # Update field visibility
            self.toggle_position_fields()
            self.toggle_velocity_fields()

            # Refresh trajectory list
            self.refresh_trajectory_list()

        finally:
            self.blockSignals(False)

    def closeEvent(self, event):
        """Clean up resources when tab is closed."""
        if hasattr(self, "map_widget"):
            self.map_widget.cleanup()
        event.accept()
