"""
Ephemeris & Time Configuration Tab (Merged)

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This tab handles both ephemeris data source configuration and time system configuration
with validation that the simulation time falls within ephemeris validity range.
"""

import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QComboBox,
    QPushButton,
    QFileDialog,
    QLabel,
    QSizePolicy,
    QListWidget,
    QSpinBox,
    QDoubleSpinBox,
    QDateTimeEdit,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QAbstractItemView,
    QMessageBox,
    QStackedWidget,
)
from PyQt6.QtCore import pyqtSignal, QDateTime, Qt
from core.config.models import GNSSSignalSimConfig, EphemerisType, EphemerisConfig, TimeType
from core.utils.logger import debug, info
from core.utils.settings import get_default_path


class EphemerisTimeTab(QWidget):
    """Merged Ephemeris and Time configuration tab with validity checking."""

    config_changed = pyqtSignal()

    def __init__(self, config: GNSSSignalSimConfig):
        super().__init__()
        self.config = config
        self.ephemeris_file_ranges = []  # List of (file_info, start_time, end_time, constellations) tuples
        self.init_ui()
        self.connect_signals()
        self.refresh_from_config()

    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Step 1: Ephemeris Configuration Group
        ephemeris_group = QGroupBox("Load Ephemeris Files")
        ephemeris_group.setStyleSheet("""
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
        ephemeris_layout = QHBoxLayout(ephemeris_group) # Changed to QHBoxLayout for overall group

        # Left side: Ephemeris type selection and buttons (vertical group)
        left_controls_layout = QVBoxLayout()
        
        # Ephemeris type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Ephemeris Type:"))
        self.type_combo = QComboBox()
        for eph_type in EphemerisType:
            self.type_combo.addItem(eph_type.value, eph_type)
        self.type_combo.setMaximumWidth(150)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch() # Push combo to left
        left_controls_layout.addLayout(type_layout)

        # Buttons
        self.add_file_button = QPushButton("Add Ephemeris Files")
        self.add_file_button.clicked.connect(self.add_ephemeris_file)
        left_controls_layout.addWidget(self.add_file_button)

        self.remove_file_button = QPushButton("Remove Selected")
        self.remove_file_button.clicked.connect(self.remove_ephemeris_file)
        left_controls_layout.addWidget(self.remove_file_button)
        
        left_controls_layout.addStretch() # Push buttons to top
        ephemeris_layout.addLayout(left_controls_layout)
        
        # Right side: File list
        self.ephemeris_list_widget = QListWidget()
        
        self.ephemeris_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #343a40;
                color: #f8f9fa;
                border: 1px solid #495057;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078d4; /* Blue color for selected item */
                color: #ffffff;
            }
        """)
        self.ephemeris_list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        ephemeris_layout.addWidget(self.ephemeris_list_widget, 1) # Give it more space

        # Make the ephemeris group resizable
        ephemeris_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        layout.addWidget(ephemeris_group, 1) # Smaller stretch factor for top group

        # Step 2: Time Configuration and Ephemeris Validation
        config_group = QGroupBox("Time Configuration and Ephemeris Validation")
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 5px; /* Reduced margin */
                padding-top: 5px; /* Reduced padding */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(5) # Reduced spacing

        # Time configuration section
        time_config_layout = QHBoxLayout()
        
        # Time type selection
        time_config_layout.addWidget(QLabel("Time Type:"))
        self.time_type_combo = QComboBox()
        for time_type in TimeType:
            self.time_type_combo.addItem(time_type.value, time_type)
        self.time_type_combo.setMaximumWidth(150)
        time_config_layout.addWidget(self.time_type_combo)
        
        # Auto time select button
        self.auto_time_select_button = QPushButton("Auto Time Select")
        self.auto_time_select_button.setToolTip("Automatically set time based on selected ephemeris file in the table below")
        self.auto_time_select_button.setMaximumWidth(120)
        self.auto_time_select_button.clicked.connect(self.auto_select_time_from_table)
        time_config_layout.addWidget(self.auto_time_select_button)

        # Stacked widget for time input fields
        self.time_input_stack = QStackedWidget()

        # UTC Time settings widget
        self.utc_widget = QWidget()
        utc_widget_layout = QHBoxLayout(self.utc_widget)
        utc_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.datetime_edit.setMaximumWidth(200)
        utc_widget_layout.addWidget(self.datetime_edit)
        utc_widget_layout.addStretch()
        self.time_input_stack.addWidget(self.utc_widget)

        # Satellite Time settings widget
        self.sat_widget = QWidget()
        sat_widget_layout = QHBoxLayout(self.sat_widget)
        sat_widget_layout.setContentsMargins(0, 0, 0, 0)
        sat_widget_layout.addWidget(QLabel("Week:"))
        self.week_spin = QSpinBox()
        self.week_spin.setRange(0, 9999)
        self.week_spin.setValue(2250)
        self.week_spin.setMaximumWidth(80)
        sat_widget_layout.addWidget(self.week_spin)
        sat_widget_layout.addWidget(QLabel("Second:"))
        self.second_spin = QDoubleSpinBox()
        self.second_spin.setRange(0, 604800)  # Seconds in a week
        self.second_spin.setDecimals(1)
        self.second_spin.setValue(345600.0)
        self.second_spin.setMaximumWidth(100)
        sat_widget_layout.addWidget(self.second_spin)
        # GLONASS specific fields
        sat_widget_layout.addWidget(QLabel("Leap Year:"))
        self.leap_year_spin = QSpinBox()
        self.leap_year_spin.setRange(1980, 2100)
        self.leap_year_spin.setValue(2024)
        self.leap_year_spin.setMaximumWidth(80)
        sat_widget_layout.addWidget(self.leap_year_spin)
        sat_widget_layout.addWidget(QLabel("Day:"))
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 366)  # Day of year
        self.day_spin.setValue(1)
        self.day_spin.setMaximumWidth(80)
        sat_widget_layout.addWidget(self.day_spin)
        sat_widget_layout.addStretch()
        self.time_input_stack.addWidget(self.sat_widget)

        time_config_layout.addWidget(self.time_input_stack)
        config_layout.addLayout(time_config_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        config_layout.addWidget(separator)

        # Ephemeris validation table
        table_label = QLabel("Ephemeris Files and Time Validation:")
        table_label.setStyleSheet("font-weight: bold; margin-top: 5px;") # Reduced margin
        config_layout.addWidget(table_label)
        
        self.ephemeris_table = QTableWidget()
        self.ephemeris_table.setColumnCount(6)
        self.ephemeris_table.setHorizontalHeaderLabels([
            "File Name", "Constellations", "Valid Time Range", "Duration", "Simulation \nStart Time Status", "Included"
        ])
        
        # Set column widths
        header = self.ephemeris_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # File Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Constellations
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Time Range
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Duration
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)           # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Include checkbox
        
        # Make table expand to fill available space
        self.ephemeris_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ephemeris_table.setAlternatingRowColors(True)
        self.ephemeris_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Make table non-editable
        self.ephemeris_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ephemeris_table.setStyleSheet("""
            QTableWidget {
                background-color: #343a40;
                alternate-background-color: #3E444A;
                gridline-color: #495057;
                color: #f8f9fa;
                font-family: 'Segoe UI', 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #495057;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #454a4f;
            }
            QHeaderView::section {
                background-color: #2c3136;
                color: #f8f9fa;
                padding: 8px;
                border: 1px solid #495057;
                font-weight: bold;
                font-size: 10px;
            }
            QHeaderView::section:horizontal:last-child {
                border-right: none;
            }
            QHeaderView::section:vertical:last-child {
                border-bottom: none;
            }
            QTableCornerButton::section {
                background-color: #2c3136;
                border: 1px solid #495057;
            }
        """)

        config_layout.addWidget(self.ephemeris_table)

        # Add include/exclude all checkbox in the header
        self.select_all_checkbox = QCheckBox("Include/Exclude All")
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        
        # Create a widget to hold the checkbox and add it to the table header
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.addWidget(self.select_all_checkbox)
        header_layout.addStretch()
        
        # Set the header widget for the Include column
        self.ephemeris_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.ephemeris_table.horizontalHeader().resizeSection(5, 80) # Make it smaller
        
        # Add warning label and select all checkbox
        controls_layout = QHBoxLayout()
        
        # Warning label for no files selected
        self.warning_label = QLabel("⚠️ Please select at least one ephemeris file")
        self.warning_label.setStyleSheet("""
            QLabel {
                color: #d63031;
                font-weight: bold;
                font-size: 12px;
                background-color: #ffe0e0;
                border: 2px solid #d63031;
                border-radius: 6px;
                padding: 8px 12px;
                margin: 2px;
            }
        """)
        self.warning_label.setVisible(False)
        controls_layout.addWidget(self.warning_label)
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.select_all_checkbox)
        config_layout.addLayout(controls_layout)

        layout.addWidget(config_group, 3) # Larger stretch factor for bottom group

        # Initially show appropriate time widgets and update label
        self.update_time_widgets()
        
        # Update initial warning state
        self.update_warning_visibility()

    def connect_signals(self):
        """Connect widget signals."""
        # Ephemeris signals
        self.type_combo.currentTextChanged.connect(self.update_config)
        self.ephemeris_list_widget.itemSelectionChanged.connect(self.update_ephemeris_info)

        # Time signals
        self.time_type_combo.currentTextChanged.connect(self.on_time_type_changed)
        self.datetime_edit.dateTimeChanged.connect(self.validate_time_and_update)
        self.week_spin.valueChanged.connect(self.validate_time_and_update)
        self.second_spin.valueChanged.connect(self.validate_time_and_update)
        self.leap_year_spin.valueChanged.connect(self.validate_time_and_update)
        self.day_spin.valueChanged.connect(self.validate_time_and_update)

    def add_ephemeris_file(self):
        """Add ephemeris files (supports multiple selection)."""
        eph_type = self.type_combo.currentData()

        if eph_type == EphemerisType.RINEX:
            file_filter = "RINEX Files (*.rnx *.nav *.21n *.22n *.23n *.24n);;All Files (*)"
        elif eph_type == EphemerisType.YUMA:
            file_filter = "YUMA Files (*.alm *.yuma);;All Files (*)"
        elif eph_type == EphemerisType.XML:
            file_filter = "XML Files (*.xml);;All Files (*)"
        else:
            file_filter = "All Files (*)"

        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Ephemeris Files", get_default_path("ephemeris"), file_filter
        )

        if file_paths:
            # Check for duplicates and only add new files
            existing_files = {eph.name for eph in self.config.ephemeris}
            added_count = 0
            
            for file_path in file_paths:
                if file_path not in existing_files:
                    new_eph_config = EphemerisConfig(type=eph_type, name=file_path)
                    self.config.ephemeris.append(new_eph_config)
                    existing_files.add(file_path)
                    added_count += 1
            
            if added_count > 0:
                self.refresh_ephemeris_list()
                self.analyze_ephemeris_validity()
                self.validate_current_time()
                self.update_config()
            
            if added_count < len(file_paths):
                skipped_count = len(file_paths) - added_count
                QMessageBox.warning(
                    self,
                    "Duplicate Files",
                    f"Skipped {skipped_count} duplicate file(s).\n\n"
                    f"Files that are already loaded will not be added again.",
                    QMessageBox.StandardButton.Ok
                )
                info(f"Skipped {skipped_count} duplicate file(s)")

    def remove_ephemeris_file(self):
        """Remove selected ephemeris file."""
        selected_items = self.ephemeris_list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            row = self.ephemeris_list_widget.row(item)
            if 0 <= row < len(self.config.ephemeris):
                del self.config.ephemeris[row]
        
        self.refresh_ephemeris_list()
        self.analyze_ephemeris_validity()
        self.validate_current_time()
        self.update_config()

    def refresh_ephemeris_list(self):
        """Refresh the ephemeris file list (simplified display)."""
        self.ephemeris_list_widget.clear()
        
        for eph_config in self.config.ephemeris:
            filename = os.path.basename(eph_config.name)
            display_text = f"{eph_config.type.value}: {filename}"
            self.ephemeris_list_widget.addItem(display_text)
        
        # Also update the table
        self.update_ephemeris_table()
        
        # Update select all checkbox and warning
        self.update_select_all_checkbox()
        self.update_warning_visibility()

    def update_ephemeris_table(self):
        """Update the ephemeris validation table with current file information and time validation."""
        # Set the number of rows to match the number of ephemeris files
        self.ephemeris_table.setRowCount(len(self.config.ephemeris))
        
        # Get current simulation time for validation
        sim_time = self.get_current_simulation_time()
        
        for i, eph_config in enumerate(self.config.ephemeris):
            filename = os.path.basename(eph_config.name)
            
            # File Name column
            file_item = QTableWidgetItem(filename)
            file_item.setToolTip(eph_config.name)  # Full path as tooltip
            self.ephemeris_table.setItem(i, 0, file_item)
            
            # Get file information
            if i < len(self.ephemeris_file_ranges):
                file_info, start_time, end_time, constellations = self.ephemeris_file_ranges[i]
                
                if start_time and end_time:
                    # Constellations column
                    const_str = ", ".join(sorted(constellations)) if constellations else "Unknown"
                    const_item = QTableWidgetItem(const_str)
                    self.ephemeris_table.setItem(i, 1, const_item)
                    
                    # Valid Time Range column
                    time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')} UTC"
                    range_item = QTableWidgetItem(time_range)
                    self.ephemeris_table.setItem(i, 2, range_item)
                    
                    # Duration column
                    duration = (end_time - start_time).total_seconds() / 3600
                    duration_item = QTableWidgetItem(f"{duration:.1f}h")
                    self.ephemeris_table.setItem(i, 3, duration_item)
                    
                    # Simulation Time Status column
                    if sim_time:
                        if start_time <= sim_time <= end_time:
                            # Time is valid for this file
                            hours_from_start = (sim_time - start_time).total_seconds() / 3600
                            hours_to_end = (end_time - sim_time).total_seconds() / 3600
                            status_text = f"✅ VALID ({hours_from_start:.1f}h from start, {hours_to_end:.1f}h to end)"
                            status_item = QTableWidgetItem(status_text)
                            status_item.setBackground(Qt.GlobalColor.green)
                            status_item.setForeground(Qt.GlobalColor.white)
                        else:
                            # Time is outside this file's range
                            if sim_time < start_time:
                                diff_hours = (start_time - sim_time).total_seconds() / 3600
                                status_text = f"❌ Too early ({diff_hours:.1f}h before start)"
                            else:
                                diff_hours = (sim_time - end_time).total_seconds() / 3600
                                status_text = f"❌ Too late ({diff_hours:.1f}h after end)"
                            status_item = QTableWidgetItem(status_text)
                            status_item.setBackground(Qt.GlobalColor.red)
                            status_item.setForeground(Qt.GlobalColor.white)
                    else:
                        status_item = QTableWidgetItem("⚠️ Set simulation time")
                        status_item.setBackground(Qt.GlobalColor.yellow)
                        status_item.setForeground(Qt.GlobalColor.black)
                    
                    self.ephemeris_table.setItem(i, 4, status_item)
                else:
                    # File couldn't be parsed
                    self.ephemeris_table.setItem(i, 1, QTableWidgetItem("Parse failed"))
                    self.ephemeris_table.setItem(i, 2, QTableWidgetItem("Unknown"))
                    self.ephemeris_table.setItem(i, 3, QTableWidgetItem("N/A"))
                    
                    status_item = QTableWidgetItem("❌ File parse error")
                    status_item.setBackground(Qt.GlobalColor.red)
                    status_item.setForeground(Qt.GlobalColor.white)
                    self.ephemeris_table.setItem(i, 4, status_item)
            else:
                # No file information available
                self.ephemeris_table.setItem(i, 1, QTableWidgetItem("Not analyzed"))
                self.ephemeris_table.setItem(i, 2, QTableWidgetItem("Unknown"))
                self.ephemeris_table.setItem(i, 3, QTableWidgetItem("N/A"))
                
                status_item = QTableWidgetItem("⚠️ Not analyzed")
                status_item.setBackground(Qt.GlobalColor.gray)
                status_item.setForeground(Qt.GlobalColor.white)
                self.ephemeris_table.setItem(i, 4, status_item)
            
            # Include checkbox column (rightmost)
            checkbox = QCheckBox()
            checkbox.setChecked(eph_config.include)
            checkbox.stateChanged.connect(lambda state, idx=i: self.on_include_changed(idx, state))
            self.ephemeris_table.setCellWidget(i, 5, checkbox)

    def get_current_simulation_time(self):
        """Get the current simulation time as a datetime object."""
        try:
            time_type = self.time_type_combo.currentData()
            
            if time_type == TimeType.UTC:
                qdt = self.datetime_edit.dateTime()
                return qdt.toPyDateTime()
            else:
                # Convert satellite time to UTC (simplified conversion)
                week = self.week_spin.value()
                second = self.second_spin.value()
                
                if time_type == TimeType.GPS:
                    # GPS epoch: January 6, 1980
                    gps_epoch = datetime(1980, 1, 6)
                    return gps_epoch + timedelta(weeks=week, seconds=second)
                elif time_type == TimeType.BDS:
                    # BDS epoch: January 1, 2006
                    bds_epoch = datetime(2006, 1, 1)
                    return bds_epoch + timedelta(weeks=week, seconds=second)
                elif time_type == TimeType.GALILEO:
                    # Galileo epoch: August 22, 1999
                    galileo_epoch = datetime(1999, 8, 22)
                    return galileo_epoch + timedelta(weeks=week, seconds=second)
                elif time_type == TimeType.GLONASS:
                    # GLONASS uses leap year, day, and second
                    leap_year = self.leap_year_spin.value()
                    day = self.day_spin.value()
                    second = self.second_spin.value()
                    return datetime(leap_year, 1, 1) + timedelta(days=day-1, seconds=second)
                else:
                    # Default to GPS time
                    gps_epoch = datetime(1980, 1, 6)
                    return gps_epoch + timedelta(weeks=week, seconds=second)
        except Exception as e:
            debug(f"Error getting simulation time: {e}")
            return None

    def analyze_ephemeris_validity(self):
        """Analyze ephemeris files to determine individual validity ranges and constellations."""
        # Clear previous file ranges
        self.ephemeris_file_ranges = []
        
        if not self.config.ephemeris:
            self.ephemeris_table.setRowCount(0)
            return

        try:
            # Try to use proper RINEX parser first
            try:
                from core.data.rinex_parser import parse_rinex_file, is_valid_rinex_file
                use_rinex_parser = True
            except ImportError:
                use_rinex_parser = False
                debug("RINEX parser not available, using fallback method")
            
            file_details = []
            parsed_files = 0
            
            for i, eph_config in enumerate(self.config.ephemeris):
                if eph_config.type == EphemerisType.RINEX:
                    file_path = eph_config.name
                    filename = os.path.basename(file_path)
                    
                    if use_rinex_parser and os.path.exists(file_path) and is_valid_rinex_file(file_path):
                        # Use proper RINEX parser
                        try:
                            parse_result = parse_rinex_file(file_path)
                            
                            if parse_result and parse_result.get('validity_range'):
                                file_start, file_end = parse_result['validity_range']
                                constellations = parse_result.get('satellite_systems', [])
                                satellite_count = parse_result.get('satellite_count', 0)
                                
                                # Store individual file information
                                self.ephemeris_file_ranges.append((eph_config, file_start, file_end, constellations))
                                
                                parsed_files += 1
                                file_details.append({
                                    'name': filename,
                                    'start': file_start,
                                    'end': file_end,
                                    'duration': (file_end - file_start).total_seconds() / 3600,
                                    'constellations': constellations,
                                    'satellite_count': satellite_count
                                })
                                
                                info(f"Parsed {filename}: {file_start} to {file_end}, Systems: {', '.join(constellations)}")
                            else:
                                # Add empty entry to maintain index alignment
                                self.ephemeris_file_ranges.append((eph_config, None, None, []))
                        except Exception as e:
                            debug(f"Error parsing {file_path}: {str(e)}")
                            self.ephemeris_file_ranges.append((eph_config, None, None, []))
                    else:
                        # Use fallback filename parsing
                        if len(filename) > 15:
                            try:
                                year_day = filename[12:19]  # e.g., "2021170"
                                if year_day.isdigit() and len(year_day) == 7:
                                    year = int(year_day[:4])
                                    day_of_year = int(year_day[4:])
                                    
                                    # Convert to datetime
                                    file_date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
                                    
                                    # Assume ephemeris is valid for ±2 hours around the file date
                                    file_start = file_date - timedelta(hours=2)
                                    file_end = file_date + timedelta(hours=26)  # +4 hours from end of day
                                    
                                    # Estimate constellation from filename
                                    constellations = ["GPS"]  # Default
                                    if "_MN" in filename or "BRDC" in filename:
                                        constellations = ["GPS", "GLO", "GAL", "BDS"]  # Multi-constellation
                                    
                                    # Store individual file information
                                    self.ephemeris_file_ranges.append((eph_config, file_start, file_end, constellations))
                                    
                                    parsed_files += 1
                                    file_details.append({
                                        'name': filename,
                                        'start': file_start,
                                        'end': file_end,
                                        'duration': (file_end - file_start).total_seconds() / 3600,
                                        'constellations': constellations,
                                        'satellite_count': 'estimated'
                                    })
                                else:
                                    self.ephemeris_file_ranges.append((eph_config, None, None, []))
                            except Exception as e:
                                debug(f"Error parsing filename for time range: {e}")
                                self.ephemeris_file_ranges.append((eph_config, None, None, []))
                        else:
                            self.ephemeris_file_ranges.append((eph_config, None, None, []))
                else:
                    # Non-RINEX files - add empty entry to maintain index alignment
                    self.ephemeris_file_ranges.append((eph_config, None, None, []))
            
            # Update the table with the analyzed files
            if parsed_files > 0:
                info(f"Successfully analyzed {parsed_files} ephemeris files individually")
            
            # Update the table display
            self.update_ephemeris_table()
            
            # Update warning visibility after analysis
            self.update_warning_visibility()
                
        except Exception as e:
            debug(f"Error analyzing ephemeris validity: {e}")
            # Still update the table to show error status
            self.update_ephemeris_table()
            # Update warning even on error
            self.update_warning_visibility()

    def on_time_type_changed(self):
        """Handle time type change."""
        self.update_time_widgets()
        self.validate_time_and_update()

    def update_time_widgets(self):
        """Update widget visibility based on time type and display selected type."""
        time_type = self.time_type_combo.currentData()

        if time_type == TimeType.UTC:
            self.time_input_stack.setCurrentWidget(self.utc_widget)
        else:
            self.time_input_stack.setCurrentWidget(self.sat_widget)
            
            # Show/hide GLONASS specific fields
            if time_type == TimeType.GLONASS:
                self.leap_year_spin.setVisible(True)
                self.day_spin.setVisible(True)
            else:
                self.leap_year_spin.setVisible(False)
                self.day_spin.setVisible(False)

    def validate_time_and_update(self):
        """Validate current time against ephemeris validity and update config."""
        self.validate_current_time()
        self.update_warning_visibility()
        self.update_config()

    def validate_current_time(self):
        """Validate that current simulation time is within individual ephemeris file validity ranges."""
        # Simply update the table - it will handle all the validation logic
        self.update_ephemeris_table()

    def on_include_changed(self, index: int, state: int):
        """Handle checkbox state change for including ephemeris files."""
        if 0 <= index < len(self.config.ephemeris):
            self.config.ephemeris[index].include = (state == Qt.CheckState.Checked.value)
            self.update_select_all_checkbox()
            self.update_warning_visibility()
            self.update_config()

    def on_select_all_changed(self, state: int):
        """Handle select/deselect all checkbox change."""
        checked = (state == Qt.CheckState.Checked.value)
        
        # Block signals to prevent recursive calls
        for i in range(len(self.config.ephemeris)):
            self.config.ephemeris[i].include = checked
        
        # Update the table checkboxes
        self.update_ephemeris_table()
        self.update_warning_visibility()
        self.update_config()

    def update_select_all_checkbox(self):
        """Update the select all checkbox based on individual checkbox states."""
        if not self.config.ephemeris:
            self.select_all_checkbox.setChecked(False)
            return
        
        all_checked = all(eph.include for eph in self.config.ephemeris)
        none_checked = not any(eph.include for eph in self.config.ephemeris)
        
        # Block signals to prevent recursive calls
        self.select_all_checkbox.blockSignals(True)
        
        if all_checked:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        elif none_checked:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        
        self.select_all_checkbox.blockSignals(False)

    def update_warning_visibility(self):
        """Update the visibility of the warning label based on selected valid files."""
        if not self.config.ephemeris:
            # No files loaded at all - critical warning
            self.warning_label.setText("⚠️ Please load ephemeris files")
            self._set_warning_style("critical")
            self.warning_label.setVisible(True)
            return
        
        # Check if any files are selected
        selected_files = [eph for eph in self.config.ephemeris if eph.include]
        if not selected_files:
            self.warning_label.setText("⚠️ Please select at least one ephemeris file")
            self._set_warning_style("error")
            self.warning_label.setVisible(True)
            return
        
        # Check if any selected files are valid for the current simulation time
        sim_time = self.get_current_simulation_time()
        if sim_time is None:
            # No simulation time set, can't validate
            self.warning_label.setVisible(False)
            return
        
        valid_selected_files = []
        for i, eph_config in enumerate(self.config.ephemeris):
            if not eph_config.include:
                continue
                
            # Check if this file has valid time range data
            if i < len(self.ephemeris_file_ranges):
                file_info, start_time, end_time, constellations = self.ephemeris_file_ranges[i]
                if start_time and end_time and start_time <= sim_time <= end_time:
                    valid_selected_files.append(eph_config)
        
        if not valid_selected_files:
            self.warning_label.setText("⚠️ Please select at least one valid ephemeris file for the current simulation time")
            self._set_warning_style("warning")
            self.warning_label.setVisible(True)
        else:
            self.warning_label.setVisible(False)

    def _set_warning_style(self, warning_type: str):
        """Set the warning label style based on warning type."""
        if warning_type == "critical":
            # Red for critical issues (no files loaded)
            style = """
                QLabel {
                    color: #d63031;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #ffe0e0;
                    border: 2px solid #d63031;
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 2px;
                }
            """
        elif warning_type == "error":
            # Orange-red for errors (no files selected)
            style = """
                QLabel {
                    color: #e17055;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #ffeaa7;
                    border: 2px solid #e17055;
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 2px;
                }
            """
        elif warning_type == "warning":
            # Yellow-orange for warnings (no valid files for time)
            style = """
                QLabel {
                    color: #f39c12;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #fff3cd;
                    border: 2px solid #f39c12;
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 2px;
                }
            """
        else:
            # Default style
            style = """
                QLabel {
                    color: #d63031;
                    font-weight: bold;
                    font-size: 12px;
                    background-color: #ffe0e0;
                    border: 2px solid #d63031;
                    border-radius: 6px;
                    padding: 8px 12px;
                    margin: 2px;
                }
            """
        
        self.warning_label.setStyleSheet(style)

    def update_ephemeris_info(self):
        """Update ephemeris information display."""
        # This could show detailed info about selected ephemeris file
        # TODO: Implement me
        pass

    def auto_select_time_from_table(self):
        """Auto-select simulation time based on selected ephemeris file in the table."""
        selected_rows = self.ephemeris_table.selectionModel().selectedRows()
        if not selected_rows:
            # No row selected in table, show a message
            QMessageBox.information(
                self,
                "No Selection",
                "Please select an ephemeris file row in the table below to auto-select time.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Get the index of the first selected row
        selected_row = selected_rows[0].row()
        
        # Check if we have file range information for this file
        if selected_row < len(self.ephemeris_file_ranges):
            file_info, start_time, end_time, constellations = self.ephemeris_file_ranges[selected_row]
            
            if start_time and end_time:
                # Calculate a good simulation time (start time of the ephemeris file)
                sim_time = start_time
                
                # Update the time widgets based on current time type
                time_type = self.time_type_combo.currentData()
                
                # Block signals to prevent recursive updates
                self.datetime_edit.blockSignals(True)
                self.week_spin.blockSignals(True)
                self.second_spin.blockSignals(True)
                self.leap_year_spin.blockSignals(True)
                self.day_spin.blockSignals(True)
                
                try:
                    if time_type == TimeType.UTC:
                        # Set UTC time directly
                        from PyQt6.QtCore import QDateTime
                        qdt = QDateTime.fromSecsSinceEpoch(int(sim_time.timestamp()))
                        self.datetime_edit.setDateTime(qdt)
                    else:
                        # Convert to satellite time (simplified conversion)
                        if time_type == TimeType.GPS:
                            # GPS epoch: January 6, 1980
                            gps_epoch = datetime(1980, 1, 6)
                            delta = sim_time - gps_epoch
                            weeks = int(delta.days / 7)
                            seconds = (delta.days % 7) * 86400 + delta.seconds
                            self.week_spin.setValue(weeks)
                            self.second_spin.setValue(seconds)
                        elif time_type == TimeType.BDS:
                            # BDS epoch: January 1, 2006
                            bds_epoch = datetime(2006, 1, 1)
                            delta = sim_time - bds_epoch
                            weeks = int(delta.days / 7)
                            seconds = (delta.days % 7) * 86400 + delta.seconds
                            self.week_spin.setValue(weeks)
                            self.second_spin.setValue(seconds)
                        elif time_type == TimeType.GALILEO:
                            # Galileo epoch: August 22, 1999
                            galileo_epoch = datetime(1999, 8, 22)
                            delta = sim_time - galileo_epoch
                            weeks = int(delta.days / 7)
                            seconds = (delta.days % 7) * 86400 + delta.seconds
                            self.week_spin.setValue(weeks)
                            self.second_spin.setValue(seconds)
                        elif time_type == TimeType.GLONASS:
                            # GLONASS uses leap year, day, and second
                            self.leap_year_spin.setValue(sim_time.year)
                            day_of_year = sim_time.timetuple().tm_yday
                            self.day_spin.setValue(day_of_year)
                            seconds_in_day = sim_time.hour * 3600 + sim_time.minute * 60 + sim_time.second
                            self.second_spin.setValue(seconds_in_day)
                    
                    # Update the configuration and validation
                    self.update_config()
                    self.validate_current_time()
                    
                    # Get filename for the info message
                    filename = "Unknown"
                    if selected_row < len(self.config.ephemeris):
                        filename = os.path.basename(self.config.ephemeris[selected_row].name)
                    
                    info(f"Auto-selected start time from ephemeris file '{filename}': {sim_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    
                    # Show success message
                    QMessageBox.information(
                        self,
                        "Time Auto-Selected",
                        f"Time has been set to the start time of ephemeris file:\n'{filename}'\n\n"
                        f"Selected time: {sim_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                        QMessageBox.StandardButton.Ok
                    )
                    
                finally:
                    # Re-enable signals
                    self.datetime_edit.blockSignals(False)
                    self.week_spin.blockSignals(False)
                    self.second_spin.blockSignals(False)
                    self.leap_year_spin.blockSignals(False)
                    self.day_spin.blockSignals(False)
            else:
                # File couldn't be parsed or no time information available
                filename = "Unknown"
                if selected_row < len(self.config.ephemeris):
                    filename = os.path.basename(self.config.ephemeris[selected_row].name)
                
                QMessageBox.warning(
                    self,
                    "No Time Information",
                    f"Cannot auto-select time for file '{filename}'.\n\n"
                    f"The ephemeris file could not be parsed or does not contain valid time information.",
                    QMessageBox.StandardButton.Ok
                )
        else:
            QMessageBox.warning(
                self,
                "File Not Analyzed",
                "The selected ephemeris file has not been analyzed yet.\n\n"
                "Please wait for the file analysis to complete.",
                QMessageBox.StandardButton.Ok
            )

    def update_config(self):
        """Update configuration from widget values."""
        # Update time configuration
        time_type = self.time_type_combo.currentData()
        self.config.time.type = time_type

        if time_type == TimeType.UTC:
            dt = self.datetime_edit.dateTime()
            self.config.time.year = dt.date().year()
            self.config.time.month = dt.date().month()
            self.config.time.day = dt.date().day()
            self.config.time.hour = dt.time().hour()
            self.config.time.minute = dt.time().minute()
            self.config.time.second = dt.time().second()

            # Clear satellite time fields
            self.config.time.week = None
            self.config.time.leap_year = None
        else:
            self.config.time.week = self.week_spin.value()
            self.config.time.second = self.second_spin.value()
            
            if time_type == TimeType.GLONASS:
                self.config.time.leap_year = self.leap_year_spin.value()
                self.config.time.day = self.day_spin.value()
            else:
                self.config.time.leap_year = None
                self.config.time.day = None

            # Clear UTC fields
            self.config.time.year = None
            self.config.time.month = None
            self.config.time.hour = None
            self.config.time.minute = None

        self.config_changed.emit()

    def refresh_from_config(self):
        """Refresh widget values from configuration."""
        # Block signals
        self.type_combo.blockSignals(True)
        self.time_type_combo.blockSignals(True)
        self.datetime_edit.blockSignals(True)
        self.week_spin.blockSignals(True)
        self.second_spin.blockSignals(True)
        self.leap_year_spin.blockSignals(True)
        self.day_spin.blockSignals(True)

        try:
            # Set ephemeris type
            if self.config.ephemeris:
                for i in range(self.type_combo.count()):
                    if self.type_combo.itemData(i) == self.config.ephemeris[0].type:
                        self.type_combo.setCurrentIndex(i)
                        break

            # Refresh ephemeris list
            self.refresh_ephemeris_list()
            self.analyze_ephemeris_validity()

            # Set time type
            for i in range(self.time_type_combo.count()):
                if self.time_type_combo.itemData(i) == self.config.time.type:
                    self.time_type_combo.setCurrentIndex(i)
                    break

            # Set time values
            if self.config.time.type == TimeType.UTC:
                if all(v is not None for v in [
                    self.config.time.year, self.config.time.month, self.config.time.day,
                    self.config.time.hour, self.config.time.minute, self.config.time.second
                ]):
                    dt = QDateTime(
                        self.config.time.year, self.config.time.month, self.config.time.day,
                        self.config.time.hour, self.config.time.minute, int(self.config.time.second)
                    )
                    self.datetime_edit.setDateTime(dt)
            else:
                if self.config.time.week is not None:
                    self.week_spin.setValue(self.config.time.week)
                if self.config.time.second is not None:
                    self.second_spin.setValue(self.config.time.second)
                if self.config.time.leap_year is not None:
                    self.leap_year_spin.setValue(self.config.time.leap_year)
                if self.config.time.day is not None:
                    self.day_spin.setValue(self.config.time.day)

            self.update_time_widgets()
            self.validate_current_time()

        finally:
            # Re-enable signals
            self.type_combo.blockSignals(False)
            self.time_type_combo.blockSignals(False)
            self.datetime_edit.blockSignals(False)
            self.week_spin.blockSignals(False)
            self.second_spin.blockSignals(False)
            self.leap_year_spin.blockSignals(False)
            self.day_spin.blockSignals(False)