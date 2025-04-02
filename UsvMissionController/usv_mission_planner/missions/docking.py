"""
Docking Mission implementation for USV.

This module provides functionality for automated docking with a target
dock specified by GPS coordinates and approach vector.
"""

import time
import numpy as np
from typing import Tuple, Dict, Any, List
from utils.geo_utils import calculate_bearing, calculate_distance, offset_position
from utils.logger import get_logger

logger = get_logger(__name__)

class DockingMission:
    """
    A mission to autonomously dock with a target dock.
    
    Attributes:
        dock_position (Tuple[float, float]): Position of the dock as (lat, lon)
        dock_heading (float): Heading of the dock in degrees (0-360, N=0, E=90)
        approach_distance (float): Distance in meters for final approach
        approach_speed (float): Speed for final approach (0.0-1.0)
        docking_states (List[str]): Sequence of docking states
        current_state (str): Current state in the docking process
        mission_complete (bool): Flag indicating if docking is complete
    """
    
    def __init__(
        self, 
        dock_position: Tuple[float, float],
        dock_heading: float,
        approach_distance: float = 20.0,
        approach_speed: float = 0.3
    ):
        """
        Initialize the docking mission.
        
        Args:
            dock_position: Position of the dock as (latitude, longitude)
            dock_heading: Heading of the dock in degrees (0-360, N=0, E=90)
            approach_distance: Distance in meters for final approach
            approach_speed: Speed for final approach (0.0-1.0)
        """
        self.dock_position = dock_position
        self.dock_heading = dock_heading
        self.approach_distance = approach_distance
        self.approach_speed = approach_speed
        
        # Calculate approach point (position from where to start final approach)
        # This is approach_distance meters away from dock in the opposite direction of dock_heading
        approach_bearing = (dock_heading + 180) % 360  # Opposite of dock heading
        self.approach_position = offset_position(
            dock_position[0], dock_position[1],
            approach_bearing, approach_distance
        )
        
        # Define docking states
        self.docking_states = [
            'NAVIGATE_TO_APPROACH',  # Moving to the approach position
            'ALIGN_WITH_DOCK',       # Aligning with dock heading
            'FINAL_APPROACH',        # Moving towards dock
            'DOCKED'                 # Successfully docked
        ]
        
        # Initialize state
        self.current_state = self.docking_states[0]
        self.mission_complete = False
        self.state_start_time = time.time()
        
        logger.info(f"Created docking mission to dock at {dock_position} with heading {dock_heading}°")
        logger.info(f"Approach position: {self.approach_position}")
    
    def update(self, current_position: Tuple[float, float], current_heading: float) -> Dict[str, Any]:
        """
        Update mission state based on current position and heading.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            current_heading: Current heading of the vehicle in degrees
            
        Returns:
            Dict containing mission status information including:
                - 'state': Current docking state
                - 'distance_to_approach': Distance to approach point in meters
                - 'distance_to_dock': Distance to dock in meters
                - 'heading_error': Difference between current and desired heading
                - 'mission_complete': Boolean indicating if docking is complete
        """
        if self.mission_complete:
            return {
                'state': self.current_state,
                'distance_to_approach': 0.0,
                'distance_to_dock': 0.0,
                'heading_error': 0.0,
                'mission_complete': True
            }
        
        # Calculate distances
        distance_to_approach = calculate_distance(
            current_position[0], current_position[1],
            self.approach_position[0], self.approach_position[1]
        )
        
        distance_to_dock = calculate_distance(
            current_position[0], current_position[1],
            self.dock_position[0], self.dock_position[1]
        )
        
        # Calculate heading error (how far off we are from dock heading)
        heading_error = min((current_heading - self.dock_heading) % 360, 
                            (self.dock_heading - current_heading) % 360)
        
        # State machine for docking
        if self.current_state == 'NAVIGATE_TO_APPROACH':
            if distance_to_approach < 2.0:  # Within 2 meters of approach point
                logger.info("Reached approach position. Aligning with dock.")
                self.current_state = self.docking_states[1]  # ALIGN_WITH_DOCK
                self.state_start_time = time.time()
        
        elif self.current_state == 'ALIGN_WITH_DOCK':
            if heading_error < 5.0:  # Within 5 degrees of dock heading
                logger.info("Aligned with dock. Beginning final approach.")
                self.current_state = self.docking_states[2]  # FINAL_APPROACH
                self.state_start_time = time.time()
        
        elif self.current_state == 'FINAL_APPROACH':
            if distance_to_dock < 1.0:  # Within 1 meter of dock
                logger.info("Successfully docked!")
                self.current_state = self.docking_states[3]  # DOCKED
                self.mission_complete = True
        
        return {
            'state': self.current_state,
            'distance_to_approach': distance_to_approach,
            'distance_to_dock': distance_to_dock,
            'heading_error': heading_error,
            'mission_complete': self.mission_complete
        }
    
    def get_guidance_command(self, current_position: Tuple[float, float], current_heading: float) -> Dict[str, Any]:
        """
        Calculate guidance command for the vehicle to execute the docking procedure.
        
        Args:
            current_position: Current (latitude, longitude) of the vehicle
            current_heading: Current heading of the vehicle in degrees
            
        Returns:
            Dict containing:
                - 'heading': Desired heading in degrees
                - 'thrust': Desired thrust level (0.0-1.0)
                - 'is_complete': Whether the mission is complete
        """
        if self.mission_complete:
            return {
                'heading': self.dock_heading,
                'thrust': 0.0,
                'is_complete': True
            }
        
        # Default values
        desired_heading = 0.0
        desired_thrust = 0.0
        
        # State-specific guidance
        if self.current_state == 'NAVIGATE_TO_APPROACH':
            # Navigate to approach position
            desired_heading = calculate_bearing(
                current_position[0], current_position[1],
                self.approach_position[0], self.approach_position[1]
            )
            
            # Calculate distance to approach
            distance = calculate_distance(
                current_position[0], current_position[1],
                self.approach_position[0], self.approach_position[1]
            )
            
            # Set thrust based on distance
            if distance > 10.0:
                desired_thrust = 0.6  # Higher thrust when far
            else:
                # Gradually reduce thrust as we approach
                desired_thrust = max(0.2, 0.6 * (distance / 10.0))
        
        elif self.current_state == 'ALIGN_WITH_DOCK':
            # Align with dock heading
            desired_heading = self.dock_heading
            
            # Set minimal thrust for rotation
            desired_thrust = 0.1
            
            # Calculate heading error
            heading_error = min((current_heading - self.dock_heading) % 360, 
                               (self.dock_heading - current_heading) % 360)
            
            # If well-aligned, use even less thrust
            if heading_error < 10.0:
                desired_thrust = 0.05
        
        elif self.current_state == 'FINAL_APPROACH':
            # Keep dock heading during approach
            desired_heading = self.dock_heading
            
            # Use configured approach speed
            desired_thrust = self.approach_speed
            
            # Calculate distance to dock
            distance_to_dock = calculate_distance(
                current_position[0], current_position[1],
                self.dock_position[0], self.dock_position[1]
            )
            
            # Reduce thrust as we get very close
            if distance_to_dock < 3.0:
                # Linear decrease from approach_speed to 0.1
                desired_thrust = max(0.1, self.approach_speed * (distance_to_dock / 3.0))
        
        return {
            'heading': desired_heading,
            'thrust': desired_thrust,
            'is_complete': self.mission_complete
        }
