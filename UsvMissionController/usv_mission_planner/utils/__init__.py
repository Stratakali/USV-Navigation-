"""
Utility modules for USV Mission Planner.

This package contains utility functions including:
- Geographic utilities for GPS calculations
- Configuration management
- Logging facilities
"""

from .geo_utils import (
    calculate_distance, calculate_bearing, offset_position
)
from .config import get_config_value
from .logger import get_logger

__all__ = [
    'calculate_distance', 'calculate_bearing', 'offset_position',
    'get_config_value', 'get_logger'
]
