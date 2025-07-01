"""
GNSSSignalSim GUI - Main Application Entry Point

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

Main entry point for the GNSSSignalSim GUI application.
A comprehensive PyQt6-based GUI for generating GNSS signal simulation configuration files
with enhanced constellation support and interactive features.
https://github.com/MuhammadQaisarAli/SignalSim
"""

import sys
from pathlib import Path

# Add the src directory to Python path for imports FIRST
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Set Qt attributes before creating QApplication (IMPORTANT for QWebEngine)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

from gui.main_window import MainWindow
from core.utils.logger import info, error
from core.utils.version import get_cached_project_info


def setup_application():
    """Set up the QApplication with proper settings."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Get project info from pyproject.toml
    project_info = get_cached_project_info()
    
    app = QApplication(sys.argv)
    app.setApplicationName(project_info['name'])
    app.setApplicationVersion(project_info['version'])
    app.setOrganizationName("Muhammad Qaisar Ali")
    app.setOrganizationDomain("github.com/MuhammadQaisarAli")
    
    # Set application icon if available
    icon_paths = [
        Path(__file__).parent / "gui" / "resources" / "icons" / "gnsssignalsimgui.ico",
        Path(__file__).parent / "gui" / "resources" / "icons" / "app_icon.png",
        Path(__file__).parent / "gui" / "resources" / "icons" / "app_icon.ico"
    ]
    
    for icon_path in icon_paths:
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            info(f"Application icon set from {icon_path}")
            break
    else:
        info("No application icon found")
    
    return app


def main():
    """Main application entry point."""
    try:
        info("Starting GNSSSignalSim GUI application")
        
        app = setup_application()
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        info("GNSSSignalSim GUI application started successfully")
        
        # Run the application
        exit_code = app.exec()
        
        info(f"GNSSSignalSim GUI application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        error(f"Failed to start GNSSSignalSim GUI application: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())