"""
Settings Manager for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

Handles loading and saving application preferences using TOML format.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

# Handle TOML imports for different Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python versions
    except ImportError:
        tomllib = None

try:
    import tomli_w as tomli_w
except ImportError:
    tomli_w = None

from .logger import debug, info, error


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SettingsManager:
    """Manages application settings with TOML persistence."""
    
    def __init__(self):
        """Initialize settings manager."""
        self.settings_dir = self._get_settings_directory()
        self.settings_file = self.settings_dir / "preferences.toml"
        self._settings = self._get_default_settings()
        
        # Ensure settings directory exists
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing settings
        self.load_settings()
    
    def _get_settings_directory(self) -> Path:
        """Get the appropriate settings directory for the current platform."""
        app_name = "GNSSSignalSimGUI"
        
        if sys.platform == "win32":
            # Windows: Use %APPDATA%
            appdata = os.environ.get("APPDATA")
            if appdata:
                return Path(appdata) / app_name
            else:
                # Fallback to user home directory
                return Path.home() / f".{app_name.lower()}"
        
        elif sys.platform == "darwin":
            # macOS: Use ~/Library/Application Support
            return Path.home() / "Library" / "Application Support" / app_name
        
        else:
            # Linux/Unix: Use ~/.config
            config_home = os.environ.get("XDG_CONFIG_HOME")
            if config_home:
                return Path(config_home) / app_name
            else:
                return Path.home() / ".config" / app_name
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default application settings."""
        return {
            "general": {
                "auto_save_enabled": True,
                "auto_save_interval": 5,  # minutes
                "real_time_validation": True,
                "validation_level": "Standard"
            },
            "appearance": {
                "theme": "System",
                "font_family": "System Default",
                "font_size": 10
            },
            "paths": {
                "default_config_path": "",
                "default_ephemeris_path": "",
                "default_output_path": ""
            },
            "logging": {
                "file_log_level": "INFO",
                "console_log_level": "WARNING",
                "enable_file_logging": True,
                "enable_console_logging": True
            }
        }
    
    def load_settings(self) -> bool:
        """Load settings from TOML file."""
        if not tomllib:
            error("TOML library not available. Cannot load settings.")
            return False
        
        if not self.settings_file.exists():
            info("Settings file not found. Using default settings.")
            self.save_settings()  # Create default settings file
            return True
        
        try:
            with open(self.settings_file, 'rb') as f:
                loaded_settings = tomllib.load(f)
            
            # Merge loaded settings with defaults (in case new settings were added)
            self._merge_settings(loaded_settings)
            info(f"Settings loaded from {self.settings_file}")
            return True
            
        except Exception as e:
            error(f"Failed to load settings from {self.settings_file}: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save current settings to TOML file."""
        if not tomli_w:
            error("TOML writer library not available. Cannot save settings.")
            return False
        
        try:
            with open(self.settings_file, 'wb') as f:
                tomli_w.dump(self._settings, f)
            
            debug(f"Settings saved to {self.settings_file}")
            return True
            
        except Exception as e:
            error(f"Failed to save settings to {self.settings_file}: {e}")
            return False
    
    def _merge_settings(self, loaded_settings: Dict[str, Any]):
        """Merge loaded settings with defaults, preserving new default keys."""
        for section, values in self._settings.items():
            if section in loaded_settings:
                if isinstance(values, dict):
                    for key, default_value in values.items():
                        if key in loaded_settings[section]:
                            self._settings[section][key] = loaded_settings[section][key]
                        # Keep default value if key doesn't exist in loaded settings
                else:
                    self._settings[section] = loaded_settings[section]
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        try:
            return self._settings.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def set(self, section: str, key: str, value: Any):
        """Set a setting value."""
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all settings for a section."""
        return self._settings.get(section, {})
    
    def set_section(self, section: str, values: Dict[str, Any]):
        """Set all values for a section."""
        self._settings[section] = values
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._settings = self._get_default_settings()
        info("Settings reset to defaults")
    
    def get_log_levels(self) -> list:
        """Get available log levels."""
        return [level.value for level in LogLevel]


# Global settings manager instance
_settings_manager = None


def get_settings_manager() -> SettingsManager:
    """Get the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_setting(section: str, key: str, default: Any = None) -> Any:
    """Convenience function to get a setting."""
    return get_settings_manager().get(section, key, default)


def set_setting(section: str, key: str, value: Any):
    """Convenience function to set a setting."""
    get_settings_manager().set(section, key, value)


def save_settings() -> bool:
    """Convenience function to save settings."""
    return get_settings_manager().save_settings()


def get_default_path(path_type: str) -> str:
    """Get default path for file dialogs."""
    settings = get_settings_manager()
    path_key = f"default_{path_type}_path"
    default_path = settings.get("paths", path_key, "")
    
    # Return current directory if no default path is set
    if not default_path:
        return "."
    
    # Create directory if it doesn't exist
    try:
        Path(default_path).mkdir(parents=True, exist_ok=True)
        return default_path
    except Exception:
        # Return current directory if path creation fails
        return "."