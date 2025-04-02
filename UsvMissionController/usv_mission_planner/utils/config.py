"""
Configuration management utilities for USV Mission Planner.

This module provides functionality for loading and accessing configuration values.
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Default configuration
_default_config = {
    "logging": {
        "level": "INFO",
        "file_path": "usv_mission.log"
    },
    "simulation": {
        "time_step": 0.1,
        "max_time": 1000.0
    },
    "vehicle": {
        "max_speed": 2.0,  # m/s
        "turn_rate": 15.0  # degrees/s
    },
    "mission": {
        "default_waypoint_arrival_radius": 5.0,  # meters
        "default_station_keeping_radius": 10.0,  # meters
        "default_station_keeping_duration": 300.0  # seconds
    },
    "path_planning": {
        "default_mode": "waypoint",
        "safe_distance": 10.0,  # meters
        "grid_size": 5.0  # meters
    }
}

# Current active configuration
_config = _default_config.copy()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        The loaded configuration dict
    """
    global _config
    
    # Start with default configuration
    _config = _default_config.copy()
    
    # If config path provided, try to load it
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                
            # Update default config with user values (nested update)
            _update_nested_dict(_config, user_config)
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
    else:
        if config_path:
            logger.warning(f"Configuration file not found: {config_path}")
        logger.info("Using default configuration")
    
    return _config

def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    Get a value from the configuration.
    
    Args:
        section: Section of the configuration
        key: Configuration key
        default: Default value if not found
        
    Returns:
        The configuration value
    """
    global _config
    
    try:
        return _config.get(section, {}).get(key, default)
    except:
        return default

def _update_nested_dict(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a nested dictionary with values from another dict.
    
    Args:
        d: Dictionary to update
        u: Dictionary containing updates
        
    Returns:
        Updated dictionary
    """
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            d[k] = _update_nested_dict(d[k], v)
        else:
            d[k] = v
    return d