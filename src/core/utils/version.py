"""
Version utilities for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

Reads version information from pyproject.toml to ensure single source of truth.
"""

import sys
from pathlib import Path
from typing import Optional

# Handle TOML imports for different Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None


def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from this file and go up to find pyproject.toml
    current_path = Path(__file__).parent
    while current_path != current_path.parent:
        if (current_path / "pyproject.toml").exists():
            return current_path
        current_path = current_path.parent
    
    # Fallback to current working directory
    return Path.cwd()


def get_version() -> str:
    """Get version from pyproject.toml."""
    if not tomllib:
        return "Unknown (TOML not available)"
    
    try:
        project_root = get_project_root()
        pyproject_path = project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            return "Unknown (pyproject.toml not found)"
        
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        
        return data.get("project", {}).get("version", "Unknown")
    
    except Exception as e:
        return f"Unknown (Error: {e})"


def get_project_info() -> dict:
    """Get project information from pyproject.toml."""
    if not tomllib:
        return {
            "name": "GNSSSignalSim GUI",
            "version": "Unknown",
            "description": "GNSS Signal Simulation Configuration Tool"
        }
    
    try:
        project_root = get_project_root()
        pyproject_path = project_root / "pyproject.toml"
        
        if not pyproject_path.exists():
            return {
                "name": "GNSSSignalSim GUI",
                "version": "Unknown",
                "description": "GNSS Signal Simulation Configuration Tool"
            }
        
        with open(pyproject_path, 'rb') as f:
            data = tomllib.load(f)
        
        project_data = data.get("project", {})
        return {
            "name": project_data.get("name", "gnsssigsimgui"),
            "version": project_data.get("version", "Unknown"),
            "description": project_data.get("description", "GNSS Signal Simulation Configuration Tool"),
            "requires_python": project_data.get("requires-python", ">=3.8")
        }
    
    except Exception as e:
        return {
            "name": "GNSSSignalSim GUI",
            "version": f"Unknown (Error: {e})",
            "description": "GNSS Signal Simulation Configuration Tool"
        }


def get_app_name() -> str:
    """Get the application display name."""
    return "GNSSSignalSim GUI"


def get_app_title() -> str:
    """Get the application title with version."""
    version = get_version()
    return f"GNSSSignalSim GUI v{version}"


# Cache version info to avoid repeated file reads
_cached_version = None
_cached_project_info = None


def get_cached_version() -> str:
    """Get cached version (reads file only once)."""
    global _cached_version
    if _cached_version is None:
        _cached_version = get_version()
    return _cached_version


def get_cached_project_info() -> dict:
    """Get cached project info (reads file only once)."""
    global _cached_project_info
    if _cached_project_info is None:
        _cached_project_info = get_project_info()
    return _cached_project_info