"""
About Dialog for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides the about dialog for the application.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.utils.version import get_cached_project_info



class AboutDialog(QDialog):
    """About dialog for the application."""
    
    def __init__(self, parent=None):
        """Initialize the about dialog."""
        super().__init__(parent)
        
        # Get project info from pyproject.toml
        self.project_info = get_cached_project_info()
        
        self.setWindowTitle(f"About {self.project_info['name']}")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with logo and title
        header_layout = QHBoxLayout()
        
        # Logo (placeholder)
        logo_label = QLabel()
        logo_label.setFixedSize(64, 64)
        logo_label.setStyleSheet("background-color: #2196F3; border-radius: 8px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setText("GNSS")
        logo_label.setStyleSheet("""
            QLabel {
                background-color: #2196F3;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        header_layout.addWidget(logo_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        title_label = QLabel("GNSSSignalSim GUI")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {self.project_info['version']}")
        version_label.setStyleSheet("color: #666;")
        title_layout.addWidget(version_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tab widget for different information
        tab_widget = QTabWidget()
        
        # About tab
        about_tab = self.create_about_tab()
        tab_widget.addTab(about_tab, "About")
        
        # Credits tab
        credits_tab = self.create_credits_tab()
        tab_widget.addTab(credits_tab, "Credits")
        
        # License tab
        license_tab = self.create_license_tab()
        tab_widget.addTab(license_tab, "License")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
    
    def create_about_tab(self):
        """Create the about tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        description = QLabel(f"""
        <p><b>GNSSSignalSim GUI</b> is a comprehensive tool for configuring 
        GNSS signal simulation parameters.</p>
        
        <p>{self.project_info['description']}</p>
        
        <p>This application provides an intuitive interface for creating 
        and managing SignalSim JSON configuration files with support for 
        multiple GNSS constellations including GPS, GLONASS, Galileo, and BeiDou.</p>
        
        <p><b>Features:</b></p>
        <ul>
        <li>Interactive configuration of GNSS simulation parameters</li>
        <li>Support for multiple constellation systems</li>
        <li>Real-time validation and feedback</li>
        <li>Template management for common configurations</li>
        <li>Integrated map for trajectory planning</li>
        <li>Comprehensive ephemeris data support</li>
        </ul>
        """)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(description)
        
        return tab
    
    def create_credits_tab(self):
        """Create the credits tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        credits = QTextEdit()
        credits.setReadOnly(True)
        credits.setHtml("""
        <h3>Development Team</h3>
        <p><b>Muhammad Qaisar Ali</b><br>
        Lead Developer<br>
        GitHub: <a href="https://github.com/MuhammadQaisarAli">https://github.com/MuhammadQaisarAli</a></p>
        
        <h3>Third-Party Libraries</h3>
        <p><b>PyQt6</b> - Cross-platform GUI toolkit<br>
        <b>Folium</b> - Interactive maps<br>
        <b>PyQt6-WebEngine</b> - Web engine for PyQt6<br>
        <b>JsonSchema</b> - Json Handling</p>

        <h3>Special Thanks</h3>
        <p>Thanks to the open-source community for providing the tools and
        libraries that made this project possible. Special thanks to the author of
        SignalSim for providing the GNSS Signal Simulator core functionality.</p>
        """)
        layout.addWidget(credits)
        
        return tab
    
    def create_license_tab(self):
        """Create the license tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText("""
MIT License

Copyright (c) 2025 Muhammad Qaisar Ali

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
        """)
        layout.addWidget(license_text)
        
        return tab