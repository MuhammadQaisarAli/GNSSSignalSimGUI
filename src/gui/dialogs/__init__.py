"""
GUI Dialog Windows Module

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

Dialog windows for preferences, help, and specialized configuration tasks.
"""

# Import all dialog classes for easy access
from .about import AboutDialog
from .preferences import PreferencesDialog
from .map_dialog import MapDialog
from .masked_satellite_dialog import MaskedSatelliteDialog
from .signal_power_dialog import SignalPowerDialog
from .template_dialog import TemplateDialog
from .trajectory_dialog import TrajectorySegmentDialog

__all__ = [
    'AboutDialog',
    'PreferencesDialog', 
    'MapDialog',
    'MaskedSatelliteDialog',
    'SignalPowerDialog',
    'TemplateDialog',
    'TrajectorySegmentDialog',
]