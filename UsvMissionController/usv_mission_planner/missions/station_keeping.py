"""
Station Keeping Mission implementation for USV.

This module provides functionality for maintaining position at a
specified GPS coordinate within a given radius.
"""

import time
import numpy as np
from typing import Tuple, Dict, Any
from utils.geo_utils import calculate_bearing, calculate_distance
from utils.logger import get_logger

logger = get_logger(__name__)

class StationKeepingMission:
    """
    A mission to maintain position at a specified location.
    
    Attributes:
        target_position (Tuple[float, float]): Target position as (lat, lon)
        tolerance_radius (float): Acceptable radius in meters from target position
        duration (float): How long to maintain position in seconds
        start_time (float): When the station keeping started
        is_keeping_station (bool): Whether currently in station keeping mode
        mission_complete (bool): Flag indicating if station keeping is complete
    """
    
    def __init__(
        self, 
        target_position: Tuple[float, float],
        tolerance_radius: float = 10.0,
        duration: float = 300.0  # 5 minutes default
    ):
        """
        Initialize the station keeping mission.
        
        Args:
            target_position: Target (latitude, longitude) to maintain
            tolerance_radius: Acceptable distance in meters from target position
            duration: How long to maintain position in seconds
        """
        self.target_position = target_position
        self.tolerance_radius = tolerance_radius
        self.duration = duration
        self.start_time = None
        self.is_keeping_station = False
        self.mission_complete = False
        logger.info(f"Created station keeping mission at {target_position}")
    
    def update(self, current_position: Tuple[float, float]) -> Dict[str, Any]:
        """
        Update mission state based on current position.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            
        Returns:
            Dict containing mission status information including:
                - 'distance_to_station': Distance to station point in meters
                - 'bearing_to_station': Bearing to station point in degrees
                - 'in_tolerance_zone': Boolean indicating if within tolerance radius
                - 'time_remaining': Seconds remaining in station keeping (if started)
                - 'mission_complete': Boolean indicating if station keeping is complete
        """
        if self.mission_complete:
            return {
                'distance_to_station': 0.0,
                'bearing_to_station': 0.0,
                'in_tolerance_zone': True,
                'time_remaining': 0.0,
                'mission_complete': True
            }
        
        # Calculate distance and bearing to station point
        distance = calculate_distance(
            current_position[0], current_position[1],
            self.target_position[0], self.target_position[1]
        )
        
        bearing = calculate_bearing(
            current_position[0], current_position[1],
            self.target_position[0], self.target_position[1]
        )
        
        # Check if within tolerance zone
        in_tolerance_zone = distance <= self.tolerance_radius
        
        # Handle station keeping timing
        current_time = time.time()
        time_remaining = 0.0
        
        if in_tolerance_zone:
            if not self.is_keeping_station:
                # Just entered the tolerance zone
                self.is_keeping_station = True
                self.start_time = current_time
                logger.info(f"Started station keeping at {self.target_position} with radius {self.tolerance_radius}m")
            
            # Calculate time remaining
            if self.start_time is not None:
                elapsed_time = current_time - self.start_time
                time_remaining = max(0.0, self.duration - elapsed_time)
            else:
                time_remaining = self.duration
            
            # Check if station keeping duration has been reached
            if time_remaining <= 0:
                logger.info("Station keeping duration complete. Mission complete.")
                self.mission_complete = True
                time_remaining = 0.0
        else:
            # Outside tolerance zone
            if self.is_keeping_station:
                # Reset if we drift outside tolerance
                logger.warning("Drifted outside station keeping tolerance zone. Resetting timer.")
                self.is_keeping_station = False
                self.start_time = None
        
        return {
            'distance_to_station': distance,
            'bearing_to_station': bearing,
            'in_tolerance_zone': in_tolerance_zone,
            'time_remaining': time_remaining,
            'mission_complete': self.mission_complete
        }
    
    def get_guidance_command(self, current_position: Tuple[float, float]) -> Dict[str, Any]:
        """
        Calculate guidance command for the vehicle to maintain station.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            
        Returns:
            Dict containing:
                - 'heading': Desired heading in degrees
                - 'distance': Distance to station point in meters
                - 'thrust': Recommended thrust level (0.0-1.0)
                - 'is_complete': Whether the mission is complete
        """
        if self.mission_complete:
            return {
                'heading': 0.0,
                'distance': 0.0,
                'thrust': 0.0,
                'is_complete': True
            }
        
        # Calculate distance and bearing to station point
        distance = calculate_distance(
            current_position[0], current_position[1],
            self.target_position[0], self.target_position[1]
        )
        
        bearing = calculate_bearing(
            current_position[0], current_position[1],
            self.target_position[0], self.target_position[1]
        )
        
        # Calculate thrust based on distance
        # More thrust when further away, less when closer
        if distance > self.tolerance_radius:
            # Outside tolerance zone, move toward target
            thrust = min(0.8, distance / 100.0)  # Cap at 0.8
        else:
            # Inside tolerance zone, minimal corrections
            thrust = min(0.2, distance / (self.tolerance_radius * 2))
        
        return {
            'heading': bearing,
            'distance': distance,
            'thrust': thrust,
            'is_complete': self.mission_complete
        }
