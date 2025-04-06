"""Utility functions for the SCXT library."""

from datetime import datetime, UTC
from typing import Dict, Any, Optional
import json


def iso8601(timestamp: Optional[int] = None) -> str:
    """Convert timestamp to ISO 8601 format.
    
    Args:
        timestamp: Optional Unix timestamp in milliseconds. If None, current time is used.
        
    Returns:
        str: ISO 8601 formatted date string with timezone information.
    """
    if timestamp is None:
        return datetime.now(UTC).isoformat()
    else:
        return datetime.fromtimestamp(timestamp / 1000, UTC).isoformat()


def parse_timeframe(timeframe: str) -> int:
    """Parse timeframe string to seconds.
    
    Args:
        timeframe: String representing a time interval (e.g., "1m", "1h", "1d").
        
    Returns:
        int: Number of seconds in the specified timeframe.
        
    Raises:
        ValueError: If the timeframe format is not supported.
    """
    timeframes = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "12h": 43200,
        "1d": 86400,
        "3d": 259200,
        "1w": 604800,
    }

    if timeframe not in timeframes:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    return timeframes[timeframe]


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file.
    
    Args:
        filepath: Path to the JSON file.
        
    Returns:
        Dict[str, Any]: Parsed JSON as a dictionary.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
        json.JSONDecodeError: If file isn't valid JSON.
    """
    with open(filepath, "r") as f:
        return json.load(f)


def format_precision(value: float, precision: int) -> float:
    """Format a value to the specified precision.
    
    Args:
        value: The floating point value to format.
        precision: Number of decimal places to round to.
        
    Returns:
        float: The formatted value rounded to the specified precision.
    """
    return round(value, precision)
