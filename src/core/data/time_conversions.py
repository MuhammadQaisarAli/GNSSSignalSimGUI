"""
Time System Conversions for GNSSSignalSim

Author: Muhammad Qaisar Ali
GitHub: https://github.com/MuhammadQaisarAli

This module provides accurate time system conversions between different
GNSS time systems and UTC, following GNSSSignalSim JSON format specification.

Based on GNSSSignalSim JSON format specification.md Section 2.
"""

from datetime import datetime, timedelta
from typing import Tuple
from dataclasses import dataclass
from enum import Enum

from core.utils.logger import debug


class TimeSystem(Enum):
    """Time system identifiers."""
    UTC = "UTC"
    GPS = "GPS"
    GLONASS = "GLONASS"
    BDS = "BDS"
    GALILEO = "Galileo"


@dataclass
class TimeConversion:
    """Result of time conversion operation."""
    original_time: datetime
    converted_time: datetime
    original_system: TimeSystem
    target_system: TimeSystem
    leap_seconds_applied: int
    conversion_accuracy: str  # "exact", "approximate", "estimated"


class TimeConverter:
    """Time system converter with leap second handling."""
    
    # GPS epoch: January 6, 1980 00:00:00 UTC
    GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
    
    # BDS epoch: January 1, 2006 00:00:00 UTC
    BDS_EPOCH = datetime(2006, 1, 1, 0, 0, 0)
    
    # Galileo epoch: August 22, 1999 00:00:00 UTC
    GALILEO_EPOCH = datetime(1999, 8, 22, 0, 0, 0)
    
    # GLONASS uses Moscow time (UTC+3) but with different leap second handling
    GLONASS_UTC_OFFSET = timedelta(hours=3)
    
    # Leap seconds table (simplified - in production this should be updated regularly)
    # Format: (date, total_leap_seconds_since_1972)

    LEAP_SECONDS_TABLE = [
        (datetime(1972, 7, 1), 1),
        (datetime(1973, 1, 1), 2),
        (datetime(1974, 1, 1), 3),
        (datetime(1975, 1, 1), 4),
        (datetime(1976, 1, 1), 5),
        (datetime(1977, 1, 1), 6),
        (datetime(1978, 1, 1), 7),
        (datetime(1979, 1, 1), 8),
        (datetime(1980, 1, 1), 9),
        (datetime(1981, 7, 1), 10),
        (datetime(1982, 7, 1), 11),
        (datetime(1983, 7, 1), 12),
        (datetime(1985, 7, 1), 13),
        (datetime(1988, 1, 1), 14),
        (datetime(1990, 1, 1), 15),
        (datetime(1991, 1, 1), 16),
        (datetime(1992, 7, 1), 17),
        (datetime(1993, 7, 1), 18),
        (datetime(1994, 7, 1), 19),
        (datetime(1996, 1, 1), 20),
        (datetime(1997, 7, 1), 21),
        (datetime(1999, 1, 1), 22),
        (datetime(2006, 1, 1), 23),
        (datetime(2009, 1, 1), 24),
        (datetime(2012, 7, 1), 25),
        (datetime(2015, 7, 1), 26),
        (datetime(2017, 1, 1), 27),
        # As of the latest decisions by the General Conference on Weights and Measures,
        # no new leap seconds will be introduced until at least 2135.
    ]



    def __init__(self):
        """Initialize time converter."""
        self.current_leap_seconds = self._get_current_leap_seconds()
        debug(f"TimeConverter initialized with {self.current_leap_seconds} leap seconds")

    def _get_current_leap_seconds(self) -> int:
        """Get current leap seconds for the current date."""
        now = datetime.utcnow()
        leap_seconds = 0
        
        for date, ls in self.LEAP_SECONDS_TABLE:
            if now >= date:
                leap_seconds = ls
            else:
                break
        
        return leap_seconds

    def _get_leap_seconds_for_date(self, date: datetime) -> int:
        """Get leap seconds for a specific date."""
        leap_seconds = 0
        
        for ls_date, ls in self.LEAP_SECONDS_TABLE:
            if date >= ls_date:
                leap_seconds = ls
            else:
                break
        
        return leap_seconds

    def gps_to_utc(self, week: int, second: float) -> TimeConversion:
        """
        Convert GPS time to UTC.
        
        Args:
            week: GPS week number
            second: Seconds into the week
            
        Returns:
            TimeConversion object with conversion details
        """
        # Calculate GPS time
        gps_time = self.GPS_EPOCH + timedelta(weeks=week, seconds=second)
        
        # Apply leap seconds correction
        leap_seconds = self._get_leap_seconds_for_date(gps_time)
        utc_time = gps_time - timedelta(seconds=leap_seconds)
        
        debug(f"GPS to UTC: Week {week}, Second {second:.1f} -> {utc_time}")
        
        return TimeConversion(
            original_time=gps_time,
            converted_time=utc_time,
            original_system=TimeSystem.GPS,
            target_system=TimeSystem.UTC,
            leap_seconds_applied=leap_seconds,
            conversion_accuracy="exact"
        )

    def utc_to_gps(self, utc_time: datetime) -> Tuple[int, float]:
        """
        Convert UTC time to GPS week and second.
        
        Args:
            utc_time: UTC datetime
            
        Returns:
            Tuple of (week, second)
        """
        # Apply leap seconds correction
        leap_seconds = self._get_leap_seconds_for_date(utc_time)
        gps_time = utc_time + timedelta(seconds=leap_seconds)
        
        # Calculate time since GPS epoch
        time_diff = gps_time - self.GPS_EPOCH
        
        # Calculate week and second
        total_seconds = time_diff.total_seconds()
        week = int(total_seconds // (7 * 24 * 3600))
        second = total_seconds % (7 * 24 * 3600)
        
        debug(f"UTC to GPS: {utc_time} -> Week {week}, Second {second:.1f}")
        
        return week, second

    def bds_to_utc(self, week: int, second: float) -> TimeConversion:
        """
        Convert BDS time to UTC.
        
        Args:
            week: BDS week number
            second: Seconds into the week
            
        Returns:
            TimeConversion object with conversion details
        """
        # Calculate BDS time
        bds_time = self.BDS_EPOCH + timedelta(weeks=week, seconds=second)
        
        # BDS time is ahead of UTC by leap seconds at BDS epoch (14 seconds)
        # Plus any additional leap seconds since BDS epoch
        bds_epoch_leap_seconds = 14  # Leap seconds at BDS epoch (2006-01-01)
        current_leap_seconds = self._get_leap_seconds_for_date(bds_time)
        
        # BDS time doesn't include leap seconds, so UTC = BDS - leap_seconds
        utc_time = bds_time - timedelta(seconds=current_leap_seconds)
        
        debug(f"BDS to UTC: Week {week}, Second {second:.1f} -> {utc_time}")
        
        return TimeConversion(
            original_time=bds_time,
            converted_time=utc_time,
            original_system=TimeSystem.BDS,
            target_system=TimeSystem.UTC,
            leap_seconds_applied=current_leap_seconds,
            conversion_accuracy="exact"
        )

    def utc_to_bds(self, utc_time: datetime) -> Tuple[int, float]:
        """
        Convert UTC time to BDS week and second.
        
        Args:
            utc_time: UTC datetime
            
        Returns:
            Tuple of (week, second)
        """
        # Apply leap seconds correction
        leap_seconds = self._get_leap_seconds_for_date(utc_time)
        bds_time = utc_time + timedelta(seconds=leap_seconds)
        
        # Calculate time since BDS epoch
        time_diff = bds_time - self.BDS_EPOCH
        
        # Calculate week and second
        total_seconds = time_diff.total_seconds()
        week = int(total_seconds // (7 * 24 * 3600))
        second = total_seconds % (7 * 24 * 3600)
        
        debug(f"UTC to BDS: {utc_time} -> Week {week}, Second {second:.1f}")
        
        return week, second

    def galileo_to_utc(self, week: int, second: float) -> TimeConversion:
        """
        Convert Galileo System Time (GST) to UTC.
        
        Args:
            week: Galileo week number
            second: Seconds into the week
            
        Returns:
            TimeConversion object with conversion details
        """
        # Calculate Galileo time
        galileo_time = self.GALILEO_EPOCH + timedelta(weeks=week, seconds=second)
        
        # Galileo time is ahead of UTC by leap seconds at Galileo epoch (13 seconds)
        # Plus any additional leap seconds since Galileo epoch
        galileo_epoch_leap_seconds = 13  # Leap seconds at Galileo epoch (1999-08-22)
        current_leap_seconds = self._get_leap_seconds_for_date(galileo_time)
        
        # GST doesn't include leap seconds, so UTC = GST - leap_seconds
        utc_time = galileo_time - timedelta(seconds=current_leap_seconds)
        
        debug(f"Galileo to UTC: Week {week}, Second {second:.1f} -> {utc_time}")
        
        return TimeConversion(
            original_time=galileo_time,
            converted_time=utc_time,
            original_system=TimeSystem.GALILEO,
            target_system=TimeSystem.UTC,
            leap_seconds_applied=current_leap_seconds,
            conversion_accuracy="exact"
        )

    def utc_to_galileo(self, utc_time: datetime) -> Tuple[int, float]:
        """
        Convert UTC time to Galileo week and second.
        
        Args:
            utc_time: UTC datetime
            
        Returns:
            Tuple of (week, second)
        """
        # Apply leap seconds correction
        leap_seconds = self._get_leap_seconds_for_date(utc_time)
        galileo_time = utc_time + timedelta(seconds=leap_seconds)
        
        # Calculate time since Galileo epoch
        time_diff = galileo_time - self.GALILEO_EPOCH
        
        # Calculate week and second
        total_seconds = time_diff.total_seconds()
        week = int(total_seconds // (7 * 24 * 3600))
        second = total_seconds % (7 * 24 * 3600)
        
        debug(f"UTC to Galileo: {utc_time} -> Week {week}, Second {second:.1f}")
        
        return week, second

    def glonass_to_utc(self, leap_year: int, day: int, second: float) -> TimeConversion:
        """
        Convert GLONASS time to UTC.
        
        Args:
            leap_year: GLONASS leap year (years since 1996)
            day: Day of year
            second: Seconds into the day
            
        Returns:
            TimeConversion object with conversion details
        """
        # Convert GLONASS leap year to actual year
        # GLONASS leap year 0 = 1996
        actual_year = 1996 + leap_year
        
        # Create datetime for the specified day
        glonass_time = datetime(actual_year, 1, 1) + timedelta(days=day-1, seconds=second)
        
        # GLONASS time is Moscow time (UTC+3), but the system time is maintained
        # without leap seconds relative to UTC
        # Convert to UTC (no leap second adjustment needed for GLONASS)
        utc_time = glonass_time - self.GLONASS_UTC_OFFSET
        
        debug(f"GLONASS to UTC: Year {actual_year}, Day {day}, Second {second:.1f} -> {utc_time}")
        
        return TimeConversion(
            original_time=glonass_time,
            converted_time=utc_time,
            original_system=TimeSystem.GLONASS,
            target_system=TimeSystem.UTC,
            leap_seconds_applied=0,  # GLONASS doesn't use leap seconds
            conversion_accuracy="exact"
        )

    def utc_to_glonass(self, utc_time: datetime) -> Tuple[int, int, float]:
        """
        Convert UTC time to GLONASS leap year, day, and second.
        
        Args:
            utc_time: UTC datetime
            
        Returns:
            Tuple of (leap_year, day, second)
        """
        # Convert to Moscow time
        moscow_time = utc_time + self.GLONASS_UTC_OFFSET
        
        # Calculate leap year (years since 1996)
        leap_year = moscow_time.year - 1996
        
        # Calculate day of year
        day_of_year = moscow_time.timetuple().tm_yday
        
        # Calculate seconds into the day
        seconds_into_day = (moscow_time.hour * 3600 + 
                           moscow_time.minute * 60 + 
                           moscow_time.second + 
                           moscow_time.microsecond / 1000000.0)
        
        debug(f"UTC to GLONASS: {utc_time} -> Leap Year {leap_year}, Day {day_of_year}, Second {seconds_into_day:.1f}")
        
        return leap_year, day_of_year, seconds_into_day

    def convert_to_utc(self, time_system: TimeSystem, **kwargs) -> TimeConversion:
        """
        Convert any time system to UTC.
        
        Args:
            time_system: Source time system
            **kwargs: Time parameters specific to the system
            
        Returns:
            TimeConversion object
        """
        if time_system == TimeSystem.GPS:
            return self.gps_to_utc(kwargs['week'], kwargs['second'])
        elif time_system == TimeSystem.BDS:
            return self.bds_to_utc(kwargs['week'], kwargs['second'])
        elif time_system == TimeSystem.GALILEO:
            return self.galileo_to_utc(kwargs['week'], kwargs['second'])
        elif time_system == TimeSystem.GLONASS:
            return self.glonass_to_utc(kwargs['leap_year'], kwargs['day'], kwargs['second'])
        elif time_system == TimeSystem.UTC:
            # Already UTC
            utc_time = kwargs['datetime']
            return TimeConversion(
                original_time=utc_time,
                converted_time=utc_time,
                original_system=TimeSystem.UTC,
                target_system=TimeSystem.UTC,
                leap_seconds_applied=0,
                conversion_accuracy="exact"
            )
        else:
            raise ValueError(f"Unsupported time system: {time_system}")

    def convert_from_utc(self, utc_time: datetime, target_system: TimeSystem) -> dict:
        """
        Convert UTC to any time system.
        
        Args:
            utc_time: UTC datetime
            target_system: Target time system
            
        Returns:
            Dictionary with time parameters for the target system
        """
        if target_system == TimeSystem.GPS:
            week, second = self.utc_to_gps(utc_time)
            return {'week': week, 'second': second}
        elif target_system == TimeSystem.BDS:
            week, second = self.utc_to_bds(utc_time)
            return {'week': week, 'second': second}
        elif target_system == TimeSystem.GALILEO:
            week, second = self.utc_to_galileo(utc_time)
            return {'week': week, 'second': second}
        elif target_system == TimeSystem.GLONASS:
            leap_year, day, second = self.utc_to_glonass(utc_time)
            return {'leap_year': leap_year, 'day': day, 'second': second}
        elif target_system == TimeSystem.UTC:
            return {'datetime': utc_time}
        else:
            raise ValueError(f"Unsupported target system: {target_system}")

    def validate_time_parameters(self, time_system: TimeSystem, **kwargs) -> bool:
        """
        Validate time parameters for a given time system.
        
        Args:
            time_system: Time system to validate
            **kwargs: Time parameters
            
        Returns:
            True if parameters are valid, False otherwise
        """
        try:
            if time_system in [TimeSystem.GPS, TimeSystem.BDS, TimeSystem.GALILEO]:
                week = kwargs.get('week', 0)
                second = kwargs.get('second', 0.0)
                return (0 <= week <= 9999 and 0 <= second < 604800)
            
            elif time_system == TimeSystem.GLONASS:
                leap_year = kwargs.get('leap_year', 0)
                day = kwargs.get('day', 1)
                second = kwargs.get('second', 0.0)
                return (0 <= leap_year <= 100 and 1 <= day <= 366 and 0 <= second < 86400)
            
            elif time_system == TimeSystem.UTC:
                datetime_obj = kwargs.get('datetime')
                return isinstance(datetime_obj, datetime)
            
            return False
            
        except Exception:
            return False


# Convenience functions
_converter = TimeConverter()

def gps_to_utc(week: int, second: float) -> datetime:
    """Convert GPS time to UTC datetime."""
    return _converter.gps_to_utc(week, second).converted_time

def utc_to_gps(utc_time: datetime) -> Tuple[int, float]:
    """Convert UTC datetime to GPS week and second."""
    return _converter.utc_to_gps(utc_time)

def bds_to_utc(week: int, second: float) -> datetime:
    """Convert BDS time to UTC datetime."""
    return _converter.bds_to_utc(week, second).converted_time

def utc_to_bds(utc_time: datetime) -> Tuple[int, float]:
    """Convert UTC datetime to BDS week and second."""
    return _converter.utc_to_bds(utc_time)

def galileo_to_utc(week: int, second: float) -> datetime:
    """Convert Galileo time to UTC datetime."""
    return _converter.galileo_to_utc(week, second).converted_time

def utc_to_galileo(utc_time: datetime) -> Tuple[int, float]:
    """Convert UTC datetime to Galileo week and second."""
    return _converter.utc_to_galileo(utc_time)

def glonass_to_utc(leap_year: int, day: int, second: float) -> datetime:
    """Convert GLONASS time to UTC datetime."""
    return _converter.glonass_to_utc(leap_year, day, second).converted_time

def utc_to_glonass(utc_time: datetime) -> Tuple[int, int, float]:
    """Convert UTC datetime to GLONASS leap year, day, and second."""
    return _converter.utc_to_glonass(utc_time)

def convert_time_to_utc(time_system: str, **kwargs) -> datetime:
    """
    Convert any time system to UTC.
    
    Args:
        time_system: Time system name ("GPS", "BDS", "Galileo", "GLONASS", "UTC")
        **kwargs: Time parameters
        
    Returns:
        UTC datetime
    """
    system_enum = TimeSystem(time_system)
    return _converter.convert_to_utc(system_enum, **kwargs).converted_time

def get_current_leap_seconds() -> int:
    """Get current leap seconds."""
    return _converter.current_leap_seconds