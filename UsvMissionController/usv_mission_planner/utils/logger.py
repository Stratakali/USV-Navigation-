"""
Logging utilities for USV Mission Planner.

This module provides a standardized logging setup for the application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(level='INFO', log_file='usv_mission.log'):
    """
    Set up application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file
    """
    # Set up root logger level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create a file handler for logging to a file
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB max file size
        backupCount=3  # Keep 3 backup files
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Add the file handler to the root logger
    logging.getLogger('').addHandler(file_handler)
    
    # Return the root logger
    return logging.getLogger('')

def get_logger(name=None):
    """
    Get a logger for a specific module.
    
    Args:
        name: Logger name, typically __name__ from the calling module
        
    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)