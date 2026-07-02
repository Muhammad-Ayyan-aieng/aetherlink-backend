# ============================================================
# AETHER LINK - DATE UTILITIES
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import re

# ============================================================
# CONSTANTS
# ============================================================

# Default date formats
DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
ISO_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Time units in seconds
TIME_UNITS = {
    'year': 31536000,
    'month': 2592000,
    'week': 604800,
    'day': 86400,
    'hour': 3600,
    'minute': 60,
    'second': 1,
}


# ============================================================
# CURRENT TIME
# ============================================================

def now_utc() -> datetime:
    """
    Get current UTC datetime with timezone.
    
    Returns:
        Current UTC datetime
    
    Examples:
        >>> now_utc()
        datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    """
    return datetime.now(timezone.utc)


def now_utc_naive() -> datetime:
    """
    Get current UTC datetime without timezone (naive).
    
    Returns:
        Current UTC datetime (naive)
    
    Examples:
        >>> now_utc_naive()
        datetime.datetime(2024, 1, 1, 12, 0, 0)
    """
    return datetime.utcnow()


def today_utc() -> datetime:
    """
    Get today's date at midnight UTC.
    
    Returns:
        Today's date at 00:00:00 UTC
    
    Examples:
        >>> today_utc()
        datetime.datetime(2024, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    """
    now = now_utc()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


# ============================================================
# DATE FORMATTING
# ============================================================

def format_datetime(
    dt: Optional[datetime],
    format_str: str = DATETIME_FORMAT,
) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    
    Examples:
        >>> format_datetime(datetime(2024, 1, 1, 12, 0, 0))
        "2024-01-01 12:00:00"
        
        >>> format_datetime(None)
        ""
    """
    if dt is None:
        return ""
    
    # Ensure datetime has timezone for consistent formatting
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)


def format_date(
    dt: Optional[datetime],
    format_str: str = DATE_FORMAT,
) -> str:
    """
    Format date to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted date string
    
    Examples:
        >>> format_date(datetime(2024, 1, 1))
        "2024-01-01"
        
        >>> format_date(None)
        ""
    """
    if dt is None:
        return ""
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)


def format_time(
    dt: Optional[datetime],
    format_str: str = TIME_FORMAT,
) -> str:
    """
    Format time to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted time string
    
    Examples:
        >>> format_time(datetime(2024, 1, 1, 12, 30, 45))
        "12:30:45"
        
        >>> format_time(None)
        ""
    """
    if dt is None:
        return ""
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_str)


def to_iso_format(dt: Optional[datetime]) -> str:
    """
    Convert datetime to ISO 8601 format.
    
    Args:
        dt: Datetime object
    
    Returns:
        ISO 8601 formatted string
    
    Examples:
        >>> to_iso_format(datetime(2024, 1, 1, 12, 0, 0))
        "2024-01-01T12:00:00Z"
        
        >>> to_iso_format(None)
        ""
    """
    if dt is None:
        return ""
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(ISO_FORMAT)


# ============================================================
# DATE PARSING
# ============================================================

def parse_date(
    date_str: str,
    format_str: str = DATE_FORMAT,
) -> Optional[datetime]:
    """
    Parse date string to datetime.
    
    Args:
        date_str: Date string
        format_str: Format string
    
    Returns:
        Datetime object or None
    
    Examples:
        >>> parse_date("2024-01-01")
        datetime.datetime(2024, 1, 1, 0, 0, 0)
        
        >>> parse_date("invalid")
        None
    """
    if not date_str:
        return None
    
    try:
        dt = datetime.strptime(date_str.strip(), format_str)
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def parse_datetime(
    dt_str: str,
    format_str: str = DATETIME_FORMAT,
) -> Optional[datetime]:
    """
    Parse datetime string to datetime.
    
    Args:
        dt_str: Datetime string
        format_str: Format string
    
    Returns:
        Datetime object or None
    
    Examples:
        >>> parse_datetime("2024-01-01 12:00:00")
        datetime.datetime(2024, 1, 1, 12, 0, 0)
        
        >>> parse_datetime("invalid")
        None
    """
    if not dt_str:
        return None
    
    try:
        dt = datetime.strptime(dt_str.strip(), format_str)
        return dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """
    Parse ISO 8601 datetime string.
    
    Args:
        iso_str: ISO 8601 string
    
    Returns:
        Datetime object or None
    
    Examples:
        >>> parse_iso_datetime("2024-01-01T12:00:00Z")
        datetime.datetime(2024, 1, 1, 12, 0, 0)
        
        >>> parse_iso_datetime("2024-01-01T12:00:00+05:00")
        datetime.datetime(2024, 1, 1, 7, 0, 0)
    """
    if not iso_str:
        return None
    
    try:
        # Handle Z suffix
        if iso_str.endswith('Z'):
            iso_str = iso_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(iso_str)
        
        # Convert to UTC
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        else:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except (ValueError, TypeError):
        return None


# ============================================================
# DATE CALCULATIONS
# ============================================================

def days_between(
    date1: datetime,
    date2: Optional[datetime] = None,
) -> int:
    """
    Calculate days between two dates.
    
    Args:
        date1: First date
        date2: Second date (default: now)
    
    Returns:
        Number of days between dates
    
    Examples:
        >>> days_between(datetime(2024, 1, 1), datetime(2024, 1, 10))
        9
        
        >>> days_between(datetime(2024, 1, 1))
        Number of days since Jan 1
    """
    if date2 is None:
        date2 = now_utc()
    
    # Ensure both are timezone-aware
    if date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    
    delta = date2 - date1
    return abs(delta.days)


def hours_between(
    date1: datetime,
    date2: Optional[datetime] = None,
) -> float:
    """
    Calculate hours between two dates.
    
    Args:
        date1: First date
        date2: Second date (default: now)
    
    Returns:
        Number of hours between dates
    
    Examples:
        >>> hours_between(datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 12, 30))
        2.5
    """
    if date2 is None:
        date2 = now_utc()
    
    if date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    
    delta = date2 - date1
    return abs(delta.total_seconds() / 3600)


def minutes_between(
    date1: datetime,
    date2: Optional[datetime] = None,
) -> float:
    """
    Calculate minutes between two dates.
    
    Args:
        date1: First date
        date2: Second date (default: now)
    
    Returns:
        Number of minutes between dates
    """
    if date2 is None:
        date2 = now_utc()
    
    if date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    
    delta = date2 - date1
    return abs(delta.total_seconds() / 60)


# ============================================================
# DATE MANIPULATION
# ============================================================

def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to datetime.
    
    Args:
        dt: Datetime object
        days: Number of days to add (can be negative)
    
    Returns:
        New datetime with days added
    
    Examples:
        >>> add_days(datetime(2024, 1, 1), 5)
        datetime.datetime(2024, 1, 6)
        
        >>> add_days(datetime(2024, 1, 1), -5)
        datetime.datetime(2023, 12, 27)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Add hours to datetime.
    
    Args:
        dt: Datetime object
        hours: Number of hours to add (can be negative)
    
    Returns:
        New datetime with hours added
    
    Examples:
        >>> add_hours(datetime(2024, 1, 1, 10, 0), 2)
        datetime.datetime(2024, 1, 1, 12, 0)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt + timedelta(hours=hours)


def add_minutes(dt: datetime, minutes: int) -> datetime:
    """
    Add minutes to datetime.
    
    Args:
        dt: Datetime object
        minutes: Number of minutes to add (can be negative)
    
    Returns:
        New datetime with minutes added
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt + timedelta(minutes=minutes)


# ============================================================
# DATE BOUNDARIES
# ============================================================

def start_of_day(dt: datetime) -> datetime:
    """
    Get start of day (00:00:00).
    
    Args:
        dt: Datetime object
    
    Returns:
        Datetime at 00:00:00
    
    Examples:
        >>> start_of_day(datetime(2024, 1, 1, 12, 30, 45))
        datetime.datetime(2024, 1, 1, 0, 0, 0)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """
    Get end of day (23:59:59.999999).
    
    Args:
        dt: Datetime object
    
    Returns:
        Datetime at 23:59:59.999999
    
    Examples:
        >>> end_of_day(datetime(2024, 1, 1, 12, 30, 45))
        datetime.datetime(2024, 1, 1, 23, 59, 59, 999999)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_week(dt: datetime) -> datetime:
    """
    Get start of week (Monday 00:00:00).
    
    Args:
        dt: Datetime object
    
    Returns:
        Datetime at Monday 00:00:00
    
    Examples:
        >>> start_of_week(datetime(2024, 1, 4))  # Thursday
        datetime.datetime(2024, 1, 1, 0, 0, 0)  # Monday
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Monday = 0, Sunday = 6
    days_since_monday = dt.weekday()
    return start_of_day(dt - timedelta(days=days_since_monday))


def start_of_month(dt: datetime) -> datetime:
    """
    Get start of month (1st day 00:00:00).
    
    Args:
        dt: Datetime object
    
    Returns:
        Datetime at first day of month 00:00:00
    
    Examples:
        >>> start_of_month(datetime(2024, 1, 15))
        datetime.datetime(2024, 1, 1, 0, 0, 0)
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return start_of_day(dt.replace(day=1))


# ============================================================
# DATE CHECKS
# ============================================================

def is_expired(dt: datetime) -> bool:
    """
    Check if datetime is in the past.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if datetime is in the past
    
    Examples:
        >>> is_expired(datetime(2024, 1, 1))
        True  # If today is after 2024-01-01
        
        >>> is_expired(datetime(2025, 1, 1))
        False  # If today is before 2025-01-01
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt < now_utc()


def is_future(dt: datetime) -> bool:
    """
    Check if datetime is in the future.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if datetime is in the future
    
    Examples:
        >>> is_future(datetime(2025, 1, 1))
        True  # If today is before 2025-01-01
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt > now_utc()


def is_today(dt: datetime) -> bool:
    """
    Check if datetime is today.
    
    Args:
        dt: Datetime to check
    
    Returns:
        True if datetime is today
    
    Examples:
        >>> is_today(datetime.now())
        True
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    today = now_utc()
    return dt.date() == today.date()


def is_same_day(date1: datetime, date2: datetime) -> bool:
    """
    Check if two datetimes are on the same day.
    
    Args:
        date1: First datetime
        date2: Second datetime
    
    Returns:
        True if same day
    
    Examples:
        >>> is_same_day(datetime(2024, 1, 1, 10, 0), datetime(2024, 1, 1, 20, 0))
        True
    """
    if date1.tzinfo is None:
        date1 = date1.replace(tzinfo=timezone.utc)
    if date2.tzinfo is None:
        date2 = date2.replace(tzinfo=timezone.utc)
    
    return date1.date() == date2.date()


# ============================================================
# HUMAN READABLE TIME
# ============================================================

def human_readable_time(dt: datetime, include_seconds: bool = False) -> str:
    """
    Convert datetime to human readable format (e.g., "2 hours ago").
    
    Args:
        dt: Datetime to format
        include_seconds: Include seconds in output
    
    Returns:
        Human readable time string
    
    Examples:
        >>> human_readable_time(datetime.now() - timedelta(hours=2))
        "2 hours ago"
        
        >>> human_readable_time(datetime.now() - timedelta(days=5))
        "5 days ago"
    """
    if dt is None:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = now_utc()
    diff = now - dt
    seconds = diff.total_seconds()

    # Handle future dates
    if seconds < 0:
        return "in the future"

    # Handle different time units
    if seconds < 60:
        if include_seconds:
            return f"{int(seconds)} seconds ago"
        return "just now"

    if seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"

    if seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"

    if seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days > 1 else ''} ago"

    if seconds < 2592000:
        weeks = int(seconds / 604800)
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"

    if seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months > 1 else ''} ago"

    years = int(seconds / 31536000)
    return f"{years} year{'s' if years > 1 else ''} ago"


def human_readable_duration(seconds: int) -> str:
    """
    Convert seconds to human readable duration.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Human readable duration string
    
    Examples:
        >>> human_readable_duration(3665)
        "1 hour, 1 minute"
        
        >>> human_readable_duration(7200)
        "2 hours"
    """
    if seconds < 0:
        return ""
    
    if seconds < 60:
        return f"{int(seconds)} seconds"
    
    minutes = int(seconds / 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        if remaining_seconds > 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''}, {remaining_seconds} seconds"
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    
    hours = int(minutes / 60)
    remaining_minutes = int(minutes % 60)
    
    if hours < 24:
        if remaining_minutes > 0:
            return f"{hours} hour{'s' if hours > 1 else ''}, {remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
        return f"{hours} hour{'s' if hours > 1 else ''}"
    
    days = int(hours / 24)
    remaining_hours = int(hours % 24)
    
    if remaining_hours > 0:
        return f"{days} day{'s' if days > 1 else ''}, {remaining_hours} hour{'s' if remaining_hours > 1 else ''}"
    return f"{days} day{'s' if days > 1 else ''}"


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Current time
    'now_utc',
    'now_utc_naive',
    'today_utc',
    
    # Formatting
    'format_datetime',
    'format_date',
    'format_time',
    'to_iso_format',
    
    # Parsing
    'parse_date',
    'parse_datetime',
    'parse_iso_datetime',
    
    # Calculations
    'days_between',
    'hours_between',
    'minutes_between',
    
    # Manipulation
    'add_days',
    'add_hours',
    'add_minutes',
    
    # Boundaries
    'start_of_day',
    'end_of_day',
    'start_of_week',
    'start_of_month',
    
    # Checks
    'is_expired',
    'is_future',
    'is_today',
    'is_same_day',
    
    # Human readable
    'human_readable_time',
    'human_readable_duration',
]