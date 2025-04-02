"""
Waypoint Mission implementation for USV.

This module provides functionality for navigating through a series
of waypoints defined by GPS coordinates.
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from utils.geo_utils import calculate_bearing, calculate_distance
from utils.logger import get_logger

logger = get_logger(__name__)

class WaypointMission:
    """
    A mission to navigate through a series of waypoints.
    
    Attributes:
        waypoints (List[Tuple[float, float]]): List of waypoints as (lat, lon) coordinates
        current_waypoint_index (int): Index of the current target waypoint
        arrival_radius (float): Distance in meters to consider a waypoint reached
        mission_complete (bool): Flag indicating if all waypoints have been reached
    """
    
    def __init__(self, waypoints: List[Tuple[float, float]], arrival_radius: float = 5.0):
        """
        Initialize the waypoint mission.
        
        Args:
            waypoints: List of (latitude, longitude) tuples defining the mission path
            arrival_radius: Distance in meters to consider a waypoint reached
        """
        if not waypoints or len(waypoints) < 1:
            raise ValueError("Waypoint mission requires at least one waypoint")
        
        self.waypoints = waypoints
        self.current_waypoint_index = 0
        self.arrival_radius = arrival_radius
        self.mission_complete = False
        logger.info(f"Created waypoint mission with {len(waypoints)} waypoints")
        
    def get_current_waypoint(self) -> Tuple[float, float]:
        """
        Get the coordinates of the current target waypoint.
        
        Returns:
            Tuple containing (latitude, longitude) of current target waypoint
        """
        return self.waypoints[self.current_waypoint_index]
    
    def get_next_waypoint(self) -> Optional[Tuple[float, float]]:
        """
        Get the coordinates of the next waypoint, if any.
        
        Returns:
            Tuple containing (latitude, longitude) of next waypoint or None if at last waypoint
        """
        if self.current_waypoint_index + 1 < len(self.waypoints):
            return self.waypoints[self.current_waypoint_index + 1]
        return None
    
    def update(self, current_position: Tuple[float, float]) -> Dict[str, Any]:
        """
        Update mission state based on current position.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            
        Returns:
            Dict containing mission status information including:
                - 'distance_to_waypoint': Distance to current waypoint in meters
                - 'bearing_to_waypoint': Bearing to current waypoint in degrees
                - 'waypoint_reached': Boolean indicating if waypoint was reached
                - 'mission_complete': Boolean indicating if all waypoints have been reached
                - 'current_waypoint': Index of the current waypoint
        """
        if self.mission_complete:
            return {
                'distance_to_waypoint': 0.0,
                'bearing_to_waypoint': 0.0,
                'waypoint_reached': False,
                'mission_complete': True,
                'current_waypoint': self.current_waypoint_index
            }
        
        target_waypoint = self.get_current_waypoint()
        
        # Calculate distance and bearing to current waypoint
        distance = calculate_distance(
            current_position[0], current_position[1],
            target_waypoint[0], target_waypoint[1]
        )
        
        bearing = calculate_bearing(
            current_position[0], current_position[1],
            target_waypoint[0], target_waypoint[1]
        )
        
        # Check if waypoint has been reached
        waypoint_reached = distance <= self.arrival_radius
        
        if waypoint_reached:
            logger.info(f"Reached waypoint {self.current_waypoint_index} at {target_waypoint}")
            
            # Move to next waypoint if there is one
            if self.current_waypoint_index + 1 < len(self.waypoints):
                self.current_waypoint_index += 1
                logger.info(f"Moving to waypoint {self.current_waypoint_index}: {self.get_current_waypoint()}")
            else:
                logger.info("Final waypoint reached. Mission complete.")
                self.mission_complete = True
        
        return {
            'distance_to_waypoint': distance,
            'bearing_to_waypoint': bearing,
            'waypoint_reached': waypoint_reached,
            'mission_complete': self.mission_complete,
            'current_waypoint': self.current_waypoint_index
        }
    
    def get_guidance_command(self, current_position: Tuple[float, float]) -> Dict[str, Any]:
        """
        Calculate guidance command for the vehicle to reach the next waypoint.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            
        Returns:
            Dict containing:
                - 'heading': Desired heading in degrees
                - 'distance': Distance to waypoint in meters
                - 'is_complete': Whether the mission is complete
        """
        if self.mission_complete:
            return {
                'heading': 0.0,
                'distance': 0.0,
                'is_complete': True
            }
        
        target_waypoint = self.get_current_waypoint()
        
        bearing = calculate_bearing(
            current_position[0], current_position[1],
            target_waypoint[0], target_waypoint[1]
        )
        
        distance = calculate_distance(
            current_position[0], current_position[1],
            target_waypoint[0], target_waypoint[1]
        )
        
        return {
            'heading': bearing,
            'distance': distance,
            'is_complete': False
        }
