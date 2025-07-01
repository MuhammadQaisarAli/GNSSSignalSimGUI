"""
Configuration Data Models for GNSSSignalSim

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module defines the data structures and models for GNSSSignalSim configuration.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class TimeType(Enum):
    """Time system types supported by GNSSSignalSim."""

    UTC = "UTC"
    GPS = "GPS"
    GLONASS = "GLONASS"
    BDS = "BDS"
    GALILEO = "Galileo"


class PositionType(Enum):
    """Position coordinate types."""

    LLA = "LLA"
    ECEF = "ECEF"


class VelocityType(Enum):
    """Velocity types."""

    SCU = "SCU"  # Speed, Course, Up
    ENU = "ENU"
    ECEF = "ECEF"


class TrajectoryType(Enum):
    """Trajectory segment types."""

    CONST = "Const"
    CONST_ACC = "ConstAcc"
    VERTICAL_ACC = "VerticalAcc"
    JERK = "Jerk"
    HORIZONTAL_TURN = "HorizontalTurn"


class EphemerisType(Enum):
    """Ephemeris data types."""

    RINEX = "RINEX"
    YUMA = "YUMA"
    XML = "XML"


class OutputType(Enum):
    """Output data types."""

    IF_DATA = "IFdata"
    POSITION = "position"
    OBSERVATION = "observation"


class OutputFormat(Enum):
    """Output format types."""

    IQ8 = "IQ8"
    IQ4 = "IQ4"
    RINEX3 = "RINEX3"
    KML = "KML"
    NMEA0183 = "NMEA0183"
    ECEF = "ECEF"
    LLA = "LLA"


class ConstellationType(Enum):
    """GNSS constellation types."""

    GPS = "GPS"
    BDS = "BDS"
    GALILEO = "Galileo"
    GLONASS = "GLONASS"
    QZSS = "QZSS"
    IRNSS = "IRNSS"


# Signal definitions for each constellation
CONSTELLATION_SIGNALS = {
    ConstellationType.GPS: ["L1CA", "L1C", "L2C", "L2P", "L5"],
    ConstellationType.BDS: ["B1C", "B1I", "B2I", "B3I", "B2a", "B2b"],
    ConstellationType.GALILEO: ["E1", "E5a", "E5b", "E5", "E6"],
    ConstellationType.GLONASS: ["G1", "G2"],
    ConstellationType.QZSS: [],  # Reserved for future
    ConstellationType.IRNSS: [],  # Reserved for future
}


@dataclass
class TimeConfig:
    """Time configuration data."""

    type: TimeType = TimeType.UTC
    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None
    hour: Optional[int] = None
    minute: Optional[int] = None
    second: Optional[float] = None
    week: Optional[int] = None
    leap_year: Optional[int] = None


@dataclass
class PositionConfig:
    """Position configuration data."""

    type: PositionType = PositionType.LLA
    format: str = "d"
    longitude: float = 0.0
    latitude: float = 0.0
    altitude: float = 0.0
    x: Optional[float] = None  # For ECEF
    y: Optional[float] = None  # For ECEF
    z: Optional[float] = None  # For ECEF


@dataclass
class VelocityConfig:
    """Velocity configuration data."""

    type: VelocityType = VelocityType.SCU
    speed: float = 0.0
    course: float = 0.0
    up: float = 0.0
    east: Optional[float] = None
    north: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    speed_unit: str = "mps"  # Single unit for SCU (both horizontal and vertical speed)
    angle_unit: str = "degree"
    # ENU units
    east_unit: str = "mps"
    north_unit: str = "mps"
    up_unit: str = "mps"
    # ECEF units
    x_unit: str = "mps"
    y_unit: str = "mps"
    z_unit: str = "mps"


@dataclass
class TrajectorySegment:
    """Individual trajectory segment."""

    type: TrajectoryType = TrajectoryType.CONST
    time: float = 1.0
    acceleration: Optional[float] = None
    speed: Optional[float] = None
    rate: Optional[float] = None
    angle: Optional[float] = None
    radius: Optional[float] = None


@dataclass
class TrajectoryConfig:
    """Trajectory configuration data."""

    name: str = "Default Trajectory"
    init_position: PositionConfig = field(default_factory=PositionConfig)
    init_velocity: VelocityConfig = field(default_factory=VelocityConfig)
    trajectory_list: List[TrajectorySegment] = field(default_factory=list)


@dataclass
class EphemerisConfig:
    """Ephemeris configuration data."""

    type: EphemerisType = EphemerisType.RINEX
    name: str = ""
    include: bool = True  # Whether to include this file in configuration output


@dataclass
class SystemSelect:
    """System and signal selection."""

    system: ConstellationType
    signal: str
    enable: bool = True


@dataclass
class SatelliteMask:
    """Satellite mask configuration."""

    system: ConstellationType
    svid: Union[int, List[int]]


@dataclass
class OutputConfig:
    """Output configuration data."""

    elevation_mask: float = 5.0
    mask_out: List[SatelliteMask] = field(default_factory=list)


@dataclass
class PowerConfig:
    """Power configuration data."""

    unit: str = "dBHz"
    value: float = 45.0


@dataclass
class SignalPowerValue:
    """Signal power value at a specific time."""

    time: float
    unit: str
    value: float


@dataclass
class SignalPower:
    """Signal power configuration for a specific satellite."""

    system: ConstellationType
    svid: Union[int, List[int]]
    power_value: List[SignalPowerValue] = field(default_factory=list)


@dataclass
class SignalPowerConfig:
    """Signal power configuration."""

    noise_floor: float = -174.0
    init_power: PowerConfig = field(default_factory=PowerConfig)
    elevation_adjust: bool = False
    signal_power: List[SignalPower] = field(default_factory=list)


@dataclass
class AlmanacConfig:
    """Almanac configuration data."""

    system: ConstellationType
    name: str


@dataclass
class OutputSettings:
    """Output settings configuration."""

    type: OutputType = OutputType.IF_DATA
    format: OutputFormat = OutputFormat.IQ8
    sample_freq: float = 20.0
    center_freq: float = 1575.42
    interval: float = 1.0
    name: str = "output.bin"
    config: OutputConfig = field(default_factory=OutputConfig)
    system_select: List[SystemSelect] = field(default_factory=list)


@dataclass
class GNSSSignalSimConfig:
    """Complete GNSSSignalSim configuration."""

    version: float = 1.0
    description: str = "GNSSSignalSim Configuration"
    comment: str = ""
    time: TimeConfig = field(default_factory=TimeConfig)
    trajectory: TrajectoryConfig = field(default_factory=TrajectoryConfig)
    ephemeris: List[EphemerisConfig] = field(default_factory=list)
    output: OutputSettings = field(default_factory=OutputSettings)
    power: SignalPowerConfig = field(default_factory=SignalPowerConfig)
    almanac: List[AlmanacConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON export."""

        def to_camel_case(snake_str):
            components = snake_str.split("_")
            return components[0] + "".join(x.title() for x in components[1:])

        def convert_enum(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj

        def convert_dataclass(obj):
            if hasattr(obj, "__dataclass_fields__"):
                result = {}
                for field_name, field_def in obj.__dataclass_fields__.items():
                    value = getattr(obj, field_name)

                    # Special handling for SystemSelect to ensure signal field is always present
                    if obj.__class__.__name__ == "SystemSelect":
                        if field_name == "signal" and (value is None or value == ""):
                            # Use default signal for the system if signal is missing
                            system_value = getattr(obj, "system")
                            if system_value == ConstellationType.GPS:
                                value = "L1CA"
                            elif system_value == ConstellationType.BDS:
                                value = "B1C"
                            elif system_value == ConstellationType.GALILEO:
                                value = "E1"
                            elif system_value == ConstellationType.GLONASS:
                                value = "G1"
                            else:
                                value = "L1CA"  # Default fallback

                    # Special handling for ephemeris list to only include selected files
                    if obj.__class__.__name__ == "GNSSSignalSimConfig" and field_name == "ephemeris":
                        # Filter to only include ephemeris files marked as included
                        value = [eph for eph in value if getattr(eph, 'include', True)]

                    # Special handling for OutputSettings interval field
                    if obj.__class__.__name__ == "OutputSettings":
                        if field_name == "interval":
                            # Only include interval for position and observation outputs
                            output_type = getattr(obj, "type")
                            if output_type not in [
                                OutputType.POSITION,
                                OutputType.OBSERVATION,
                            ]:
                                continue
                        # Skip sample_freq and center_freq for non-IFdata outputs
                        elif field_name in ["sample_freq", "center_freq"]:
                            output_type = getattr(obj, "type")
                            if output_type != OutputType.IF_DATA:
                                continue

                    # Skip the include field for EphemerisConfig (UI-only field)
                    if obj.__class__.__name__ == "EphemerisConfig" and field_name == "include":
                        continue

                    # Special handling for VelocityConfig to only include relevant units and values
                    if obj.__class__.__name__ == "VelocityConfig":
                        velocity_type = getattr(obj, "type")
                        if velocity_type == VelocityType.SCU:
                            # For SCU, only include speed, course, up, speedUnit and angleUnit
                            if field_name in ["east", "north", "x", "y", "z", "east_unit", "north_unit", "up_unit", "x_unit", "y_unit", "z_unit"]:
                                continue
                        elif velocity_type == VelocityType.ENU:
                            # For ENU, only include east, north, up, eastUnit, northUnit, upUnit
                            if field_name in ["speed", "course", "x", "y", "z", "speed_unit", "angle_unit", "x_unit", "y_unit", "z_unit"]:
                                continue
                        elif velocity_type == VelocityType.ECEF:
                            # For ECEF, only include x, y, z, xUnit, yUnit, zUnit
                            if field_name in ["speed", "course", "up", "east", "north", "speed_unit", "angle_unit", "east_unit", "north_unit", "up_unit"]:
                                continue

                    # Special handling for PositionConfig to only include relevant fields
                    if obj.__class__.__name__ == "PositionConfig":
                        position_type = getattr(obj, "type")
                        if position_type == PositionType.LLA:
                            # For LLA, only include type, format, longitude, latitude, altitude
                            if field_name in ["x", "y", "z"]:
                                continue
                        elif position_type == PositionType.ECEF:
                            # For ECEF, only include type, x, y, z
                            if field_name in ["format", "longitude", "latitude", "altitude"]:
                                continue

                    # Skip None values except for SystemSelect signal field
                    if value is None and not (
                        obj.__class__.__name__ == "SystemSelect"
                        and field_name == "signal"
                    ):
                        continue

                    camel_case_name = to_camel_case(field_name)

                    if isinstance(value, list):
                        result[camel_case_name] = [
                            convert_dataclass(item) for item in value
                        ]
                    elif hasattr(value, "__dataclass_fields__"):
                        result[camel_case_name] = convert_dataclass(value)
                    else:
                        result[camel_case_name] = convert_enum(value)
                return result
            else:
                return convert_enum(obj)

        return convert_dataclass(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GNSSSignalSimConfig":
        """Create configuration from dictionary (JSON import)."""

        def to_snake_case(camel_str: str) -> str:
            if not camel_str:
                return camel_str
            res = [camel_str[0].lower()]
            for char in camel_str[1:]:
                if char.isupper():
                    res.append("_")
                    res.append(char.lower())
                else:
                    res.append(char)
            return "".join(res)

        def convert_to_dataclass(data_dict: Dict[str, Any], dataclass_type):
            if not hasattr(dataclass_type, "__dataclass_fields__"):
                return data_dict

            kwargs = {}
            field_types = {
                f.name: f.type for f in dataclass_type.__dataclass_fields__.values()
            }

            for key, value in data_dict.items():
                snake_key = to_snake_case(key)
                if snake_key in field_types:
                    field_type = field_types[snake_key]

                    # Handle lists
                    if isinstance(value, list) and hasattr(field_type, "__args__"):
                        list_item_type = field_type.__args__[0]
                        kwargs[snake_key] = [
                            convert_to_dataclass(item, list_item_type) for item in value
                        ]
                    # Handle nested dataclasses
                    elif isinstance(value, dict) and hasattr(
                        field_type, "__dataclass_fields__"
                    ):
                        kwargs[snake_key] = convert_to_dataclass(value, field_type)
                    # Handle Enums
                    elif hasattr(field_type, "__members__") and isinstance(value, str):
                        try:
                            kwargs[snake_key] = field_type(value)
                        except ValueError:
                            # Handle cases where the enum value might not match
                            kwargs[snake_key] = None
                    else:
                        # Handle legacy unit formats
                        if snake_key == "speed_unit" and value == "m/s":
                            kwargs[snake_key] = "mps"
                        elif snake_key == "speed_unit" and value == "km/h":
                            kwargs[snake_key] = "kph"
                        elif snake_key == "angle_unit" and value == "deg":
                            kwargs[snake_key] = "degree"
                        else:
                            kwargs[snake_key] = value

            return dataclass_type(**kwargs)

        return convert_to_dataclass(data, cls)


def get_default_system_select() -> List[SystemSelect]:
    """Get default system selection with GPS L1CA enabled."""
    return [
        SystemSelect(ConstellationType.GPS, "L1CA", True),
        SystemSelect(ConstellationType.GPS, "L1C", False),
        SystemSelect(ConstellationType.GPS, "L2C", False),
        SystemSelect(ConstellationType.GPS, "L2P", False),
        SystemSelect(ConstellationType.GPS, "L5", False),
        SystemSelect(ConstellationType.BDS, "B1C", False),
        SystemSelect(ConstellationType.BDS, "B1I", False),
        SystemSelect(ConstellationType.BDS, "B2I", False),
        SystemSelect(ConstellationType.BDS, "B3I", False),
        SystemSelect(ConstellationType.BDS, "B2a", False),
        SystemSelect(ConstellationType.BDS, "B2b", False),
        SystemSelect(ConstellationType.GALILEO, "E1", False),
        SystemSelect(ConstellationType.GALILEO, "E5a", False),
        SystemSelect(ConstellationType.GALILEO, "E5b", False),
        SystemSelect(ConstellationType.GALILEO, "E5", False),
        SystemSelect(ConstellationType.GALILEO, "E6", False),
        SystemSelect(ConstellationType.GLONASS, "G1", False),
        SystemSelect(ConstellationType.GLONASS, "G2", False),
    ]