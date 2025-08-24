"""
Timezone utilities for Taara Internet Monitor
Handles timezone conversions for proper display of timestamps
"""

from datetime import datetime, timezone, timedelta
import pytz
from app.config import Config

# Define timezone objects
UTC = timezone.utc
NAIROBI_TZ = pytz.timezone(Config.TIMEZONE)

def utc_to_local(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to local timezone (Nairobi/EAT)
    
    Args:
        utc_dt: UTC datetime object
        
    Returns:
        Local datetime object
    """
    if utc_dt is None:
        return None
        
    # If the datetime is naive (no timezone info), assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=UTC)
    
    # Convert to local timezone
    local_dt = utc_dt.astimezone(NAIROBI_TZ)
    return local_dt

def local_to_utc(local_dt: datetime) -> datetime:
    """
    Convert local datetime to UTC
    
    Args:
        local_dt: Local datetime object
        
    Returns:
        UTC datetime object
    """
    if local_dt is None:
        return None
        
    # If the datetime is naive, assume it's in local timezone
    if local_dt.tzinfo is None:
        local_dt = NAIROBI_TZ.localize(local_dt)
    
    # Convert to UTC
    utc_dt = local_dt.astimezone(UTC)
    return utc_dt

def now_local() -> datetime:
    """
    Get current time in local timezone
    
    Returns:
        Current local datetime object
    """
    return datetime.now(NAIROBI_TZ)

def now_utc() -> datetime:
    """
    Get current time in UTC
    
    Returns:
        Current UTC datetime object
    """
    return datetime.now(UTC)

def format_local_time(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime for display in local timezone
    
    Args:
        dt: Datetime object (assumed to be UTC if naive)
        format_str: Format string for strftime
        
    Returns:
        Formatted time string
    """
    if dt is None:
        return "Never"
        
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_str)

def get_timezone_info() -> dict:
    """
    Get timezone information
    
    Returns:
        Dictionary with timezone info
    """
    now = datetime.now()
    local_now = now_local()
    utc_now = now_utc()
    
    return {
        "timezone": Config.TIMEZONE,
        "timezone_name": NAIROBI_TZ.zone,
        "utc_offset": local_now.strftime('%z'),
        "utc_offset_hours": local_now.utcoffset().total_seconds() / 3600,
        "current_local_time": local_now.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "current_utc_time": utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')
    }
