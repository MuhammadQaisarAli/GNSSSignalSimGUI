"""
Custom Widgets Package

This package contains custom reusable widgets for the GNSSSignalSim GUI.
"""

# Import all widget classes for easy access
from .coordinate_picker import CoordinatePickerWidget
from .embedded_map import EmbeddedMapWidget

__all__ = [
    'CoordinatePickerWidget',
    'EmbeddedMapWidget',
]
