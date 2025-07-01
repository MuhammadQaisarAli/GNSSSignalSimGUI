"""
RINEX File Parser for GNSSSignalSim

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides RINEX file parsing capabilities to extract ephemeris
validity ranges and satellite information for accurate time validation.

Based on GNSSSignalSim JSON format specification.md Section 4.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from core.utils.logger import debug, info, error


class RinexVersion(Enum):
    """RINEX file version types."""
    VERSION_2 = "2"
    VERSION_3 = "3"
    VERSION_4 = "4"


class SatelliteSystem(Enum):
    """Satellite system identifiers."""
    GPS = "G"
    GLONASS = "R"
    GALILEO = "E"
    BEIDOU = "C"
    QZSS = "J"
    IRNSS = "I"
    SBAS = "S"


@dataclass
class EphemerisRecord:
    """Single ephemeris record data."""
    satellite_system: SatelliteSystem
    satellite_number: int
    toc: datetime  # Time of Clock
    toe: datetime  # Time of Ephemeris
    validity_start: datetime
    validity_end: datetime
    health: int = 0


@dataclass
class RinexHeader:
    """RINEX file header information."""
    version: RinexVersion
    file_type: str
    satellite_system: SatelliteSystem
    program: str
    run_by: str
    date: str
    marker_name: str = ""
    observer: str = ""
    agency: str = ""
    receiver_number: str = ""
    receiver_type: str = ""
    receiver_version: str = ""
    antenna_number: str = ""
    antenna_type: str = ""
    approx_position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    antenna_delta: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    time_of_first_obs: Optional[datetime] = None
    time_of_last_obs: Optional[datetime] = None
    leap_seconds: int = 18


class RinexParseError(Exception):
    """Exception raised when RINEX parsing fails."""
    pass


class RinexParser:
    """RINEX file parser for ephemeris data extraction."""

    def __init__(self):
        self.header: Optional[RinexHeader] = None
        self.ephemeris_records: List[EphemerisRecord] = []
        self.validity_range: Optional[Tuple[datetime, datetime]] = None

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a RINEX file and extract ephemeris information.
        
        Args:
            file_path: Path to the RINEX file
            
        Returns:
            Dictionary containing parsed information
            
        Raises:
            RinexParseError: If parsing fails
        """
        if not os.path.exists(file_path):
            raise RinexParseError(f"File not found: {file_path}")

        info(f"Parsing RINEX file: {os.path.basename(file_path)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Parse header
            header_end = self._parse_header(lines)
            
            # Parse data records
            if self.header.file_type.startswith('N'):  # Navigation file
                self._parse_navigation_data(lines[header_end:])
            else:
                debug(f"File type {self.header.file_type} not supported for ephemeris parsing")
            
            # Calculate validity range
            self._calculate_validity_range()
            
            return self._create_result_dict()
            
        except Exception as e:
            error(f"Error parsing RINEX file {file_path}: {str(e)}")
            raise RinexParseError(f"Failed to parse RINEX file: {str(e)}")

    def _parse_header(self, lines: List[str]) -> int:
        """Parse RINEX header and return the line number where data starts."""
        header_data = {}
        line_idx = 0
        
        for i, line in enumerate(lines):
            if "END OF HEADER" in line:
                line_idx = i + 1
                break
                
            # Parse version and file type
            if "RINEX VERSION / TYPE" in line:
                version_str = line[:9].strip()
                file_type = line[20:21].strip()
                sat_system = line[40:41].strip()
                
                # Determine version
                if version_str.startswith('2'):
                    header_data['version'] = RinexVersion.VERSION_2
                elif version_str.startswith('3'):
                    header_data['version'] = RinexVersion.VERSION_3
                elif version_str.startswith('4'):
                    header_data['version'] = RinexVersion.VERSION_4
                else:
                    header_data['version'] = RinexVersion.VERSION_3  # Default
                
                header_data['file_type'] = file_type
                
                # Determine satellite system
                if sat_system in ['G', '']:
                    header_data['satellite_system'] = SatelliteSystem.GPS
                elif sat_system == 'R':
                    header_data['satellite_system'] = SatelliteSystem.GLONASS
                elif sat_system == 'E':
                    header_data['satellite_system'] = SatelliteSystem.GALILEO
                elif sat_system == 'C':
                    header_data['satellite_system'] = SatelliteSystem.BEIDOU
                else:
                    header_data['satellite_system'] = SatelliteSystem.GPS  # Default
            
            # Parse program info
            elif "PGM / RUN BY / DATE" in line:
                header_data['program'] = line[:20].strip()
                header_data['run_by'] = line[20:40].strip()
                header_data['date'] = line[40:60].strip()
            
            # Parse leap seconds
            elif "LEAP SECONDS" in line:
                try:
                    header_data['leap_seconds'] = int(line[:6].strip())
                except ValueError:
                    header_data['leap_seconds'] = 18  # Default
        
        # Create header object with defaults
        self.header = RinexHeader(
            version=header_data.get('version', RinexVersion.VERSION_3),
            file_type=header_data.get('file_type', 'N'),
            satellite_system=header_data.get('satellite_system', SatelliteSystem.GPS),
            program=header_data.get('program', 'Unknown'),
            run_by=header_data.get('run_by', 'Unknown'),
            date=header_data.get('date', 'Unknown'),
            leap_seconds=header_data.get('leap_seconds', 18)
        )
        
        debug(f"Parsed RINEX header: Version {self.header.version.value}, "
              f"System {self.header.satellite_system.value}, "
              f"Type {self.header.file_type}")
        
        return line_idx

    def _parse_navigation_data(self, data_lines: List[str]):
        """Parse navigation data records."""
        i = 0
        while i < len(data_lines):
            line = data_lines[i].strip()
            if not line:
                i += 1
                continue
            
            try:
                # Parse satellite identifier and time
                if self.header.version in [RinexVersion.VERSION_2]:
                    record = self._parse_v2_nav_record(data_lines[i:i+8])
                else:
                    record = self._parse_v3_nav_record(data_lines[i:i+8])
                
                if record:
                    self.ephemeris_records.append(record)
                    debug(f"Parsed ephemeris for {record.satellite_system.value}{record.satellite_number:02d}")
                
                # Move to next record (typically 8 lines per record)
                i += 8
                
            except Exception as e:
                debug(f"Error parsing navigation record at line {i}: {str(e)}")
                i += 1

    def _parse_v2_nav_record(self, record_lines: List[str]) -> Optional[EphemerisRecord]:
        """Parse RINEX v2 navigation record."""
        if len(record_lines) < 8:
            return None
            
        try:
            first_line = record_lines[0]
            
            # Extract satellite number
            sat_num = int(first_line[:2])
            
            # Extract time of clock (TOC)
            year = int(first_line[3:5])
            if year < 80:
                year += 2000
            else:
                year += 1900
                
            month = int(first_line[6:8])
            day = int(first_line[9:11])
            hour = int(first_line[12:14])
            minute = int(first_line[15:17])
            second = float(first_line[18:22])
            
            toc = datetime(year, month, day, hour, minute, int(second))
            
            # For navigation files, TOE is typically the same as TOC
            # In real implementation, this would be extracted from the data
            toe = toc
            
            # Calculate validity window (TOC ± 2-4 hours)
            validity_start = toc - timedelta(hours=2)
            validity_end = toc + timedelta(hours=4)
            
            return EphemerisRecord(
                satellite_system=self.header.satellite_system,
                satellite_number=sat_num,
                toc=toc,
                toe=toe,
                validity_start=validity_start,
                validity_end=validity_end
            )
            
        except Exception as e:
            debug(f"Error parsing v2 record: {str(e)}")
            return None

    def _parse_v3_nav_record(self, record_lines: List[str]) -> Optional[EphemerisRecord]:
        """Parse RINEX v3 navigation record."""
        if len(record_lines) < 8:
            return None
            
        try:
            first_line = record_lines[0]
            
            # Extract satellite system and number
            sat_id = first_line[:3].strip()
            if len(sat_id) >= 2:
                sys_char = sat_id[0]
                sat_num = int(sat_id[1:])
                
                # Map system character to enum
                sys_map = {
                    'G': SatelliteSystem.GPS,
                    'R': SatelliteSystem.GLONASS,
                    'E': SatelliteSystem.GALILEO,
                    'C': SatelliteSystem.BEIDOU,
                    'J': SatelliteSystem.QZSS,
                    'I': SatelliteSystem.IRNSS,
                    'S': SatelliteSystem.SBAS
                }
                satellite_system = sys_map.get(sys_char, self.header.satellite_system)
            else:
                satellite_system = self.header.satellite_system
                sat_num = int(sat_id)
            
            # Extract time of clock (TOC)
            year = int(first_line[4:8])
            month = int(first_line[9:11])
            day = int(first_line[12:14])
            hour = int(first_line[15:17])
            minute = int(first_line[18:20])
            second = float(first_line[21:23])
            
            toc = datetime(year, month, day, hour, minute, int(second))
            
            # For navigation files, TOE is typically the same as TOC
            toe = toc
            
            # Calculate validity window (TOC ± 2-4 hours)
            validity_start = toc - timedelta(hours=2)
            validity_end = toc + timedelta(hours=4)
            
            return EphemerisRecord(
                satellite_system=satellite_system,
                satellite_number=sat_num,
                toc=toc,
                toe=toe,
                validity_start=validity_start,
                validity_end=validity_end
            )
            
        except Exception as e:
            debug(f"Error parsing v3 record: {str(e)}")
            return None

    def _calculate_validity_range(self):
        """Calculate overall validity range from all ephemeris records."""
        if not self.ephemeris_records:
            self.validity_range = None
            return
        
        min_time = min(record.validity_start for record in self.ephemeris_records)
        max_time = max(record.validity_end for record in self.ephemeris_records)
        
        self.validity_range = (min_time, max_time)
        
        info(f"Calculated ephemeris validity range: {min_time} to {max_time}")
        info(f"Total duration: {(max_time - min_time).total_seconds() / 3600:.1f} hours")
        info(f"Number of satellites: {len(set((r.satellite_system, r.satellite_number) for r in self.ephemeris_records))}")

    def _create_result_dict(self) -> Dict:
        """Create result dictionary with parsed information."""
        result = {
            'file_valid': True,
            'header': {
                'version': self.header.version.value,
                'file_type': self.header.file_type,
                'satellite_system': self.header.satellite_system.value,
                'program': self.header.program,
                'run_by': self.header.run_by,
                'date': self.header.date,
                'leap_seconds': self.header.leap_seconds
            },
            'ephemeris_count': len(self.ephemeris_records),
            'satellite_systems': list(set(record.satellite_system.value for record in self.ephemeris_records)),
            'satellite_count': len(set((r.satellite_system, r.satellite_number) for r in self.ephemeris_records)),
            'validity_range': self.validity_range,
            'records': []
        }
        
        # Add individual records
        for record in self.ephemeris_records:
            result['records'].append({
                'satellite_system': record.satellite_system.value,
                'satellite_number': record.satellite_number,
                'toc': record.toc,
                'toe': record.toe,
                'validity_start': record.validity_start,
                'validity_end': record.validity_end,
                'health': record.health
            })
        
        return result

    @staticmethod
    def quick_parse_validity(file_path: str) -> Optional[Tuple[datetime, datetime]]:
        """
        Quick parse to get just the validity range without full parsing.
        
        Args:
            file_path: Path to the RINEX file
            
        Returns:
            Tuple of (start_time, end_time) or None if parsing fails
        """
        try:
            parser = RinexParser()
            result = parser.parse_file(file_path)
            return result.get('validity_range')
        except Exception as e:
            debug(f"Quick parse failed for {file_path}: {str(e)}")
            return None

    @staticmethod
    def validate_rinex_file(file_path: str) -> bool:
        """
        Validate if a file is a valid RINEX file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if valid RINEX file, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to check for RINEX header
                for i, line in enumerate(f):
                    if i > 10:  # Don't read too many lines
                        break
                    if "RINEX VERSION / TYPE" in line:
                        return True
                    if "END OF HEADER" in line:
                        break
            return False
        except Exception:
            return False


def parse_rinex_file(file_path: str) -> Dict:
    """
    Convenience function to parse a RINEX file.
    
    Args:
        file_path: Path to the RINEX file
        
    Returns:
        Dictionary containing parsed information
        
    Raises:
        RinexParseError: If parsing fails
    """
    parser = RinexParser()
    return parser.parse_file(file_path)


def get_ephemeris_validity_range(file_path: str) -> Optional[Tuple[datetime, datetime]]:
    """
    Get the validity range from a RINEX ephemeris file.
    
    Args:
        file_path: Path to the RINEX file
        
    Returns:
        Tuple of (start_time, end_time) or None if parsing fails
    """
    return RinexParser.quick_parse_validity(file_path)


def is_valid_rinex_file(file_path: str) -> bool:
    """
    Check if a file is a valid RINEX file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if valid RINEX file, False otherwise
    """
    return RinexParser.validate_rinex_file(file_path)