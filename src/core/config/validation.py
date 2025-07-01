"""
Configuration Validation for GNSSSignalSim

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides configuration validation functionality for GNSSSignalSim.
"""

from typing import List, Tuple
from config.models import GNSSSignalSimConfig
from utils.logger import info, error


class ConfigValidator:
    """Configuration validator for SignalSim configurations."""
    
    def __init__(self):
        """Initialize the configuration validator."""
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_config(self, config: GNSSSignalSimConfig) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a complete GNSSSignalSim configuration.
        
        Args:
            config: The configuration to validate
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        try:
            # Validate basic configuration
            self._validate_basic_config(config)
            
            # Validate time configuration
            self._validate_time_config(config)
            
            # Validate trajectory configuration
            self._validate_trajectory_config(config)
            
            # Validate signal configuration
            self._validate_signal_config(config)
            
            # Validate output configuration
            self._validate_output_config(config)
            
            is_valid = len(self.validation_errors) == 0
            
            if is_valid:
                info("Configuration validation passed")
            else:
                error(f"Configuration validation failed with {len(self.validation_errors)} errors")
                
            return is_valid, self.validation_errors.copy(), self.validation_warnings.copy()
            
        except Exception as e:
            error(f"Configuration validation error: {e}")
            self.validation_errors.append(f"Validation error: {e}")
            return False, self.validation_errors.copy(), self.validation_warnings.copy()

    def _validate_basic_config(self, config: GNSSSignalSimConfig) -> None:
        """Validate basic configuration parameters."""
        if not config.scenario_name:
            self.validation_errors.append("Scenario name is required")
            
        if not config.description:
            self.validation_warnings.append("Description is recommended")
    
    def _validate_time_config(self, config: GNSSSignalSimConfig) -> None:
        """Validate time configuration parameters."""
        if not hasattr(config, 'time_config') or not config.time_config:
            self.validation_errors.append("Time configuration is required")
            return
            
        time_config = config.time_config
        if time_config.duration <= 0:
            self.validation_errors.append("Duration must be positive")
            
        if time_config.sample_rate <= 0:
            self.validation_errors.append("Sample rate must be positive")
    
    def _validate_trajectory_config(self, config: GNSSSignalSimConfig) -> None:
        """Validate trajectory configuration parameters."""
        if not hasattr(config, 'trajectory_config') or not config.trajectory_config:
            self.validation_errors.append("Trajectory configuration is required")
            return
            
        trajectory_config = config.trajectory_config
        if not trajectory_config.segments:
            self.validation_errors.append("At least one trajectory segment is required")
    
    def _validate_signal_config(self, config: GNSSSignalSimConfig) -> None:
        """Validate signal configuration parameters."""
        if not hasattr(config, 'system_select') or not config.system_select:
            self.validation_errors.append("Signal system selection is required")
            return
            
        system_select = config.system_select
        has_signals = (
            system_select.gps_enabled or 
            system_select.glonass_enabled or 
            system_select.galileo_enabled or 
            system_select.beidou_enabled
        )
        
        if not has_signals:
            self.validation_errors.append("At least one signal system must be enabled")
    
    def _validate_output_config(self, config: GNSSSignalSimConfig) -> None:
        """Validate output configuration parameters."""
        if not hasattr(config, 'output_config') or not config.output_config:
            self.validation_errors.append("Output configuration is required")
            return
            
        output_config = config.output_config
        if not output_config.output_path:
            self.validation_errors.append("Output path is required")


# Global validator instance
config_validator = ConfigValidator()