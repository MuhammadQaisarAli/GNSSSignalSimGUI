"""
Professional Logging System for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides comprehensive logging functionality with different levels
and formatters for debugging and monitoring application behavior.
"""

import logging
import logging.handlers

import sys
from datetime import datetime
from pathlib import Path


class GNSSSignalSimLogger:
    """Professional logging system for GNSSSignalSim GUI."""

    def __init__(self, name="GNSSSignalSimGUI", log_dir="logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Store handler references for dynamic reconfiguration
        self.console_handler = None
        self.file_handler = None
        self.error_handler = None

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Set up logging handlers for console and file output."""
        # Use default settings for initial setup
        self.configure_logging(
            enable_console=True,
            console_level="INFO",
            enable_file=True,
            file_level="DEBUG"
        )

    def configure_logging(self, enable_console=True, console_level="INFO", 
                         enable_file=True, file_level="DEBUG"):
        """Configure logging based on settings."""
        # Remove existing handlers
        if self.console_handler:
            self.logger.removeHandler(self.console_handler)
            self.console_handler = None
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
            self.file_handler = None
        if self.error_handler:
            self.logger.removeHandler(self.error_handler)
            self.error_handler = None

        # Console handler
        if enable_console:
            self.console_handler = logging.StreamHandler(sys.stdout)
            console_log_level = getattr(logging, console_level.upper(), logging.INFO)
            self.console_handler.setLevel(console_log_level)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
            )
            self.console_handler.setFormatter(console_formatter)
            self.logger.addHandler(self.console_handler)

        # File handler
        if enable_file:
            log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
            self.file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_log_level = getattr(logging, file_level.upper(), logging.DEBUG)
            self.file_handler.setLevel(file_log_level)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            self.file_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.file_handler)

            # Error file handler (always enabled if file logging is enabled)
            error_file = (
                self.log_dir / f"{self.name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
            )
            self.error_handler = logging.handlers.RotatingFileHandler(
                error_file, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            self.error_handler.setLevel(logging.ERROR)
            self.error_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.error_handler)

    def debug(self, message, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """Log critical message."""
        self.logger.critical(message, *args, **kwargs)

    def log_button_click(self, button_name, tab_name=None, additional_info=None):
        """Log button click events."""
        msg = f"Button clicked: '{button_name}'"
        if tab_name:
            msg += f" in tab '{tab_name}'"
        if additional_info:
            msg += f" - {additional_info}"
        self.info(msg)

    def log_config_change(self, field_name, old_value, new_value, tab_name=None):
        """Log configuration changes."""
        msg = f"Config changed: '{field_name}' from '{old_value}' to '{new_value}'"
        if tab_name:
            msg += f" in tab '{tab_name}'"
        self.debug(msg)

    def log_file_operation(self, operation, file_path, success=True, error_msg=None):
        """Log file operations."""
        msg = f"File {operation}: '{file_path}'"
        if success:
            self.info(f"{msg} - SUCCESS")
        else:
            self.error(f"{msg} - FAILED: {error_msg}")

    def log_validation_error(self, field_name, value, error_msg, tab_name=None):
        """Log validation errors."""
        msg = f"Validation error in field '{field_name}' with value '{value}': {error_msg}"
        if tab_name:
            msg += f" (tab: {tab_name})"
        self.warning(msg)


# Global logger instance
logger = GNSSSignalSimLogger()


# Convenience functions
def debug(message, *args, **kwargs):
    logger.debug(message, *args, **kwargs)


def info(message, *args, **kwargs):
    logger.info(message, *args, **kwargs)


def warning(message, *args, **kwargs):
    logger.warning(message, *args, **kwargs)


def error(message, *args, **kwargs):
    logger.error(message, *args, **kwargs)


def critical(message, *args, **kwargs):
    logger.critical(message, *args, **kwargs)


def log_button_click(button_name, tab_name=None, additional_info=None):
    logger.log_button_click(button_name, tab_name, additional_info)


def log_config_change(field_name, old_value, new_value, tab_name=None):
    logger.log_config_change(field_name, old_value, new_value, tab_name)


def log_file_operation(operation, file_path, success=True, error_msg=None):
    logger.log_file_operation(operation, file_path, success, error_msg)


def log_validation_error(field_name, value, error_msg, tab_name=None):
    logger.log_validation_error(field_name, value, error_msg, tab_name)


def configure_logging_from_settings(settings_manager):
    """Configure logging based on settings manager."""
    logging_settings = settings_manager.get_section("logging")
    
    enable_console = logging_settings.get("enable_console_logging", True)
    console_level = logging_settings.get("console_log_level", "WARNING")
    enable_file = logging_settings.get("enable_file_logging", True)
    file_level = logging_settings.get("file_log_level", "INFO")
    
    logger.configure_logging(
        enable_console=enable_console,
        console_level=console_level,
        enable_file=enable_file,
        file_level=file_level
    )
    
    info(f"Logging reconfigured: Console={console_level} (enabled={enable_console}), "
         f"File={file_level} (enabled={enable_file})")