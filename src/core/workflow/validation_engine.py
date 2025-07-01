"""
Advanced Validation Engine for GNSSSignalSim GUI

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides comprehensive validation with smart suggestions,
error recovery, and real-time feedback for enhanced user experience.

Based on "SignalSim JSON format specification.md" requirements.
"""

from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import os

from core.utils.logger import debug, info, error
from core.config.models import GNSSSignalSimConfig


class ValidationSeverity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationCategory(Enum):
    """Validation categories."""
    FILE_ACCESS = "file_access"
    DATA_FORMAT = "data_format"
    TIME_RANGE = "time_range"
    SIGNAL_COMPATIBILITY = "signal_compatibility"
    TRAJECTORY_PHYSICS = "trajectory_physics"
    OUTPUT_FORMAT = "output_format"
    CONFIGURATION_COMPLETENESS = "configuration_completeness"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    message: str
    suggestion: str = ""
    auto_fix_available: bool = False
    auto_fix_description: str = ""
    affected_fields: List[str] = None
    
    def __post_init__(self):
        if self.affected_fields is None:
            self.affected_fields = []


class AdvancedValidationEngine:
    """Advanced validation engine with smart suggestions and auto-fixes."""
    
    def __init__(self):
        self.validation_results: List[ValidationResult] = []
        self.auto_fixes: Dict[str, callable] = {}
        self._register_auto_fixes()
        
        info("AdvancedValidationEngine initialized")

    def _register_auto_fixes(self):
        """Register available auto-fix functions."""
        self.auto_fixes = {
            "set_default_output_name": self._auto_fix_output_name,
            "enable_gps_signals": self._auto_fix_enable_gps,
            "set_current_time": self._auto_fix_current_time,
            "create_output_directory": self._auto_fix_create_directory,
        }

    def validate_complete_configuration(self, config: GNSSSignalSimConfig) -> List[ValidationResult]:
        """Perform comprehensive validation of the entire configuration."""
        self.validation_results = []
        
        # Validate each component
        self._validate_basic_info(config)
        self._validate_ephemeris_configuration(config)
        self._validate_time_configuration(config)
        self._validate_trajectory_configuration(config)
        self._validate_signal_configuration(config)
        self._validate_power_configuration(config)
        self._validate_output_configuration(config)
        self._validate_cross_dependencies(config)
        
        # Sort by severity (critical first)
        severity_order = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 1,
            ValidationSeverity.WARNING: 2,
            ValidationSeverity.INFO: 3
        }
        
        self.validation_results.sort(key=lambda x: severity_order[x.severity])
        
        info(f"Validation complete: {len(self.validation_results)} issues found")
        return self.validation_results

    def _validate_basic_info(self, config: GNSSSignalSimConfig):
        """Validate basic configuration information."""
        if not config.description or not config.description.strip():
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.INFO,
                title="Missing Project Description",
                message="No project description provided",
                suggestion="Add a description to help identify this configuration",
                affected_fields=["description"]
            ))
        
        if not config.version:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.INFO,
                title="Missing Version Information",
                message="No version specified for this configuration",
                suggestion="Consider adding version information for tracking",
                affected_fields=["version"]
            ))

    def _validate_ephemeris_configuration(self, config: GNSSSignalSimConfig):
        """Validate ephemeris file configuration."""
        if not config.ephemeris or len(config.ephemeris) == 0:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.CRITICAL,
                title="No Ephemeris Files",
                message="No ephemeris files configured",
                suggestion="Add RINEX ephemeris files in the Ephemeris & Time tab",
                affected_fields=["ephemeris"]
            ))
            return
        
        missing_files = []
        invalid_files = []
        
        for i, eph_config in enumerate(config.ephemeris):
            file_path = eph_config.name
            
            if not os.path.exists(file_path):
                missing_files.append(os.path.basename(file_path))
            else:
                # Check if it's a valid RINEX file
                try:
                    from core.data.rinex_parser import is_valid_rinex_file
                    if not is_valid_rinex_file(file_path):
                        invalid_files.append(os.path.basename(file_path))
                except ImportError:
                    debug("RINEX parser not available for validation")
        
        if missing_files:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.FILE_ACCESS,
                severity=ValidationSeverity.ERROR,
                title="Ephemeris Files Not Found",
                message=f"{len(missing_files)} ephemeris file(s) not found: {', '.join(missing_files)}",
                suggestion="Check file paths and ensure files exist",
                affected_fields=["ephemeris"]
            ))
        
        if invalid_files:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.DATA_FORMAT,
                severity=ValidationSeverity.ERROR,
                title="Invalid RINEX Files",
                message=f"{len(invalid_files)} file(s) are not valid RINEX: {', '.join(invalid_files)}",
                suggestion="Ensure files are valid RINEX navigation files",
                affected_fields=["ephemeris"]
            ))

    def _validate_time_configuration(self, config: GNSSSignalSimConfig):
        """Validate time configuration."""
        if not config.time:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.ERROR,
                title="No Time Configuration",
                message="Simulation time not configured",
                suggestion="Configure simulation time in the Ephemeris & Time tab",
                auto_fix_available=True,
                auto_fix_description="Set to current time",
                affected_fields=["time"]
            ))
            return
        
        # Validate time is within ephemeris range (if ephemeris is available)
        if config.ephemeris:
            try:
                from core.data.rinex_parser import get_ephemeris_validity_range
                from core.data.time_conversions import convert_time_to_utc
                
                # Get ephemeris validity range
                validity_ranges = []
                for eph_config in config.ephemeris:
                    if os.path.exists(eph_config.name):
                        validity_range = get_ephemeris_validity_range(eph_config.name)
                        if validity_range:
                            validity_ranges.append(validity_range)
                
                if validity_ranges:
                    # Get overall validity range
                    min_time = min(vr[0] for vr in validity_ranges)
                    max_time = max(vr[1] for vr in validity_ranges)
                    
                    # Convert simulation time to UTC
                    try:
                        if config.time.type == "UTC":
                            sim_time = datetime.fromisoformat(config.time.datetime.replace('Z', '+00:00'))
                        else:
                            # Convert from satellite time
                            sim_time = convert_time_to_utc(
                                config.time.type,
                                week=getattr(config.time, 'week', 0),
                                second=getattr(config.time, 'second', 0.0),
                                leap_year=getattr(config.time, 'leapYear', 0),
                                day=getattr(config.time, 'day', 1)
                            )
                        
                        if sim_time < min_time or sim_time > max_time:
                            hours_diff = min(abs((sim_time - min_time).total_seconds() / 3600),
                                           abs((sim_time - max_time).total_seconds() / 3600))
                            
                            self.validation_results.append(ValidationResult(
                                category=ValidationCategory.TIME_RANGE,
                                severity=ValidationSeverity.ERROR,
                                title="Time Outside Ephemeris Range",
                                message=f"Simulation time is {hours_diff:.1f} hours outside ephemeris validity",
                                suggestion=f"Set time between {min_time.strftime('%Y-%m-%d %H:%M')} and {max_time.strftime('%Y-%m-%d %H:%M')}",
                                auto_fix_available=True,
                                auto_fix_description="Set to middle of ephemeris range",
                                affected_fields=["time"]
                            ))
                    
                    except Exception as e:
                        debug(f"Error validating time range: {e}")
                        
            except ImportError:
                debug("Time conversion modules not available for validation")

    def _validate_trajectory_configuration(self, config: GNSSSignalSimConfig):
        """Validate trajectory configuration."""
        if not config.trajectory:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.INFO,
                title="Default Trajectory",
                message="Using default trajectory configuration",
                suggestion="Configure custom trajectory in the Trajectory tab if needed",
                affected_fields=["trajectory"]
            ))
            return
        
        # Validate trajectory segments if present
        if hasattr(config.trajectory, 'trajectory_list') and config.trajectory.trajectory_list:
            for i, segment in enumerate(config.trajectory.trajectory_list):
                # Check for reasonable values
                if hasattr(segment, 'duration') and segment.duration <= 0:
                    self.validation_results.append(ValidationResult(
                        category=ValidationCategory.TRAJECTORY_PHYSICS,
                        severity=ValidationSeverity.ERROR,
                        title="Invalid Trajectory Duration",
                        message=f"Trajectory segment {i+1} has invalid duration: {segment.duration}",
                        suggestion="Set positive duration values for all trajectory segments",
                        affected_fields=["trajectory", "trajectory_list"]
                    ))
                
                # Check for reasonable velocities
                if hasattr(segment, 'velocity') and segment.velocity:
                    speed = (segment.velocity.x**2 + segment.velocity.y**2 + segment.velocity.z**2)**0.5
                    if speed > 1000:  # > 1000 m/s is very fast for most applications
                        self.validation_results.append(ValidationResult(
                            category=ValidationCategory.TRAJECTORY_PHYSICS,
                            severity=ValidationSeverity.WARNING,
                            title="High Velocity in Trajectory",
                            message=f"Trajectory segment {i+1} has very high velocity: {speed:.1f} m/s",
                            suggestion="Verify velocity values are correct (consider if units are appropriate)",
                            affected_fields=["trajectory", "trajectory_list"]
                        ))

    def _validate_signal_configuration(self, config: GNSSSignalSimConfig):
        """Validate signal selection configuration."""
        if not config.output or not config.output.system_select:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.ERROR,
                title="No Signal Configuration",
                message="No signal selection configured",
                suggestion="Configure signals in the Signal Selection tab",
                auto_fix_available=True,
                auto_fix_description="Enable default GPS signals",
                affected_fields=["output", "system_select"]
            ))
            return
        
        enabled_signals = [s for s in config.output.system_select if s.enable]
        
        if not enabled_signals:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.SIGNAL_COMPATIBILITY,
                severity=ValidationSeverity.ERROR,
                title="No Signals Enabled",
                message="No signals are currently enabled for simulation",
                suggestion="Enable at least one signal in the Signal Selection tab",
                auto_fix_available=True,
                auto_fix_description="Enable GPS L1 C/A signal",
                affected_fields=["output", "system_select"]
            ))
        else:
            # Check for signal compatibility
            constellations = set(s.system for s in enabled_signals)
            if len(constellations) > 4:
                self.validation_results.append(ValidationResult(
                    category=ValidationCategory.SIGNAL_COMPATIBILITY,
                    severity=ValidationSeverity.WARNING,
                    title="Many Constellations Selected",
                    message=f"{len(constellations)} different constellations enabled",
                    suggestion="Consider if all constellations are needed for your simulation",
                    affected_fields=["output", "system_select"]
                ))

    def _validate_power_configuration(self, config: GNSSSignalSimConfig):
        """Validate power configuration."""
        if not config.power:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.INFO,
                title="Default Power Settings",
                message="Using default power configuration",
                suggestion="Configure custom power settings in the Signal Power tab if needed",
                affected_fields=["power"]
            ))
            return
        
        # Validate noise floor
        if hasattr(config.power, 'noise_floor') and config.power.noise_floor is not None:
            if config.power.noise_floor > -100:  # Very high noise floor
                self.validation_results.append(ValidationResult(
                    category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    title="High Noise Floor",
                    message=f"Noise floor is quite high: {config.power.noise_floor} dBm/Hz",
                    suggestion="Verify noise floor value is appropriate for your simulation",
                    affected_fields=["power", "noise_floor"]
                ))

    def _validate_output_configuration(self, config: GNSSSignalSimConfig):
        """Validate output configuration."""
        if not config.output or not config.output.name:
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.CONFIGURATION_COMPLETENESS,
                severity=ValidationSeverity.ERROR,
                title="No Output File Specified",
                message="Output file path not configured",
                suggestion="Set output file in the Output Settings tab",
                auto_fix_available=True,
                auto_fix_description="Set default output filename",
                affected_fields=["output", "name"]
            ))
            return
        
        output_path = config.output.name
        output_dir = os.path.dirname(output_path)
        
        # Check if output directory exists
        if output_dir and not os.path.exists(output_dir):
            self.validation_results.append(ValidationResult(
                category=ValidationCategory.FILE_ACCESS,
                severity=ValidationSeverity.WARNING,
                title="Output Directory Missing",
                message=f"Output directory does not exist: {output_dir}",
                suggestion="Create the directory or choose an existing location",
                auto_fix_available=True,
                auto_fix_description="Create the output directory",
                affected_fields=["output", "name"]
            ))
        
        # Check file extension
        if output_path:
            _, ext = os.path.splitext(output_path)
            if not ext:
                self.validation_results.append(ValidationResult(
                    category=ValidationCategory.OUTPUT_FORMAT,
                    severity=ValidationSeverity.INFO,
                    title="No File Extension",
                    message="Output file has no extension",
                    suggestion="Consider adding appropriate file extension (.bin, .dat, etc.)",
                    affected_fields=["output", "name"]
                ))

    def _validate_cross_dependencies(self, config: GNSSSignalSimConfig):
        """Validate cross-dependencies between different configuration sections."""
        # Check if ephemeris supports selected signals
        if config.ephemeris and config.output and config.output.system_select:
            enabled_signals = [s for s in config.output.system_select if s.enable]
            enabled_systems = set(s.system for s in enabled_signals)
            
            # This would require parsing ephemeris to check available systems
            # For now, just provide a general check
            if len(enabled_systems) > 1:
                self.validation_results.append(ValidationResult(
                    category=ValidationCategory.SIGNAL_COMPATIBILITY,
                    severity=ValidationSeverity.INFO,
                    title="Multi-Constellation Setup",
                    message=f"Using {len(enabled_systems)} different satellite systems",
                    suggestion="Ensure ephemeris files contain data for all selected systems",
                    affected_fields=["ephemeris", "output"]
                ))

    # Auto-fix methods
    def _auto_fix_output_name(self, config: GNSSSignalSimConfig) -> bool:
        """Auto-fix: Set default output filename."""
        try:
            if not config.output:
                from core.config.models import OutputConfig
                config.output = OutputConfig()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config.output.name = f"signalsim_output_{timestamp}.bin"
            return True
        except Exception as e:
            debug(f"Auto-fix failed for output name: {e}")
            return False

    def _auto_fix_enable_gps(self, config: GNSSSignalSimConfig) -> bool:
        """Auto-fix: Enable GPS L1 C/A signal."""
        try:
            if config.output and config.output.system_select:
                for signal in config.output.system_select:
                    if signal.system.value == "GPS" and "L1" in signal.signal:
                        signal.enable = True
                        return True
            return False
        except Exception as e:
            debug(f"Auto-fix failed for GPS signals: {e}")
            return False

    def _auto_fix_current_time(self, config: GNSSSignalSimConfig) -> bool:
        """Auto-fix: Set simulation time to current time."""
        try:
            if not config.time:
                from core.config.models import TimeConfig
                config.time = TimeConfig()
            
            config.time.type = "UTC"
            config.time.datetime = datetime.utcnow().isoformat() + "Z"
            return True
        except Exception as e:
            debug(f"Auto-fix failed for current time: {e}")
            return False

    def _auto_fix_create_directory(self, config: GNSSSignalSimConfig) -> bool:
        """Auto-fix: Create output directory."""
        try:
            if config.output and config.output.name:
                output_dir = os.path.dirname(config.output.name)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                    return True
            return False
        except Exception as e:
            debug(f"Auto-fix failed for directory creation: {e}")
            return False

    def apply_auto_fix(self, fix_id: str, config: GNSSSignalSimConfig) -> bool:
        """Apply an auto-fix to the configuration."""
        if fix_id in self.auto_fixes:
            try:
                result = self.auto_fixes[fix_id](config)
                if result:
                    info(f"Auto-fix applied successfully: {fix_id}")
                return result
            except Exception as e:
                error(f"Auto-fix failed: {fix_id} - {e}")
                return False
        return False

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get a summary of validation results."""
        summary = {
            'total_issues': len(self.validation_results),
            'by_severity': {},
            'by_category': {},
            'auto_fixes_available': 0,
            'critical_issues': [],
            'recommendations': []
        }
        
        for result in self.validation_results:
            # Count by severity
            severity = result.severity.value
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Count by category
            category = result.category.value
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
            
            # Count auto-fixes
            if result.auto_fix_available:
                summary['auto_fixes_available'] += 1
            
            # Collect critical issues
            if result.severity == ValidationSeverity.CRITICAL:
                summary['critical_issues'].append(result.title)
            
            # Collect recommendations
            if result.suggestion:
                summary['recommendations'].append(result.suggestion)
        
        return summary


# Global validation engine instance
validation_engine = AdvancedValidationEngine()


def validate_configuration(config: GNSSSignalSimConfig) -> List[ValidationResult]:
    """Convenience function to validate configuration."""
    return validation_engine.validate_complete_configuration(config)


def get_validation_summary(config: GNSSSignalSimConfig) -> Dict[str, Any]:
    """Convenience function to get validation summary."""
    validation_engine.validate_complete_configuration(config)
    return validation_engine.get_validation_summary()


def apply_auto_fix(fix_id: str, config: GNSSSignalSimConfig) -> bool:
    """Convenience function to apply auto-fix."""
    return validation_engine.apply_auto_fix(fix_id, config)