"""
Mission Manager implementation for USV.

This module provides functionality for managing and executing
different types of missions for an unmanned surface vehicle.
"""

import time
from typing import Dict, Any, Tuple, List, Optional, Union
from enum import Enum

from missions.waypoint_mission import WaypointMission
from missions.station_keeping import StationKeepingMission
from missions.docking import DockingMission
from utils.logger import get_logger

logger = get_logger(__name__)

class MissionStatus(Enum):
    """Mission status enumeration."""
    IDLE = "IDLE"               # No active mission
    RUNNING = "RUNNING"         # Mission is currently active
    PAUSED = "PAUSED"           # Mission is paused
    COMPLETED = "COMPLETED"     # Mission has completed successfully
    ABORTED = "ABORTED"         # Mission was aborted
    ERROR = "ERROR"             # Error occurred during mission

class MissionManager:
    """
    Manages the execution of different missions for an USV.
    
    Attributes:
        current_mission: The currently active mission object
        mission_queue: Queue of missions to execute in sequence
        status: Current status of the mission manager
        current_position: Last known position of the vehicle
        current_heading: Last known heading of the vehicle
        mission_history: Record of completed missions
    """
    
    def __init__(self):
        """Initialize the mission manager."""
        self.current_mission = None
        self.mission_queue = []
        self.status = MissionStatus.IDLE
        self.current_position = (0.0, 0.0)  # Default position
        self.current_heading = 0.0  # Default heading
        self.mission_history = []
        self.mission_start_time = None
        logger.info("Mission Manager initialized")
    
    def add_waypoint_mission(
        self, 
        waypoints: List[Tuple[float, float]], 
        arrival_radius: float = 5.0
    ) -> None:
        """
        Add a waypoint mission to the queue.
        
        Args:
            waypoints: List of (latitude, longitude) waypoints
            arrival_radius: Distance in meters to consider waypoint reached
        """
        mission = WaypointMission(waypoints, arrival_radius)
        self.mission_queue.append(("waypoint", mission))
        logger.info(f"Added waypoint mission with {len(waypoints)} points to queue")
    
    def add_station_keeping_mission(
        self, 
        position: Tuple[float, float], 
        radius: float = 10.0, 
        duration: float = 300.0
    ) -> None:
        """
        Add a station keeping mission to the queue.
        
        Args:
            position: (latitude, longitude) to maintain position
            radius: Acceptable radius in meters
            duration: How long to maintain position in seconds
        """
        mission = StationKeepingMission(position, radius, duration)
        self.mission_queue.append(("station_keeping", mission))
        logger.info(f"Added station keeping mission at {position} to queue")
    
    def add_docking_mission(
        self, 
        dock_position: Tuple[float, float], 
        dock_heading: float,
        approach_distance: float = 20.0,
        approach_speed: float = 0.3
    ) -> None:
        """
        Add a docking mission to the queue.
        
        Args:
            dock_position: (latitude, longitude) of the dock
            dock_heading: Heading of the dock in degrees
            approach_distance: Distance for final approach in meters
            approach_speed: Speed for final approach
        """
        mission = DockingMission(dock_position, dock_heading, approach_distance, approach_speed)
        self.mission_queue.append(("docking", mission))
        logger.info(f"Added docking mission at {dock_position} to queue")
    
    def start_missions(self) -> None:
        """Start executing missions from the queue."""
        if self.status == MissionStatus.RUNNING:
            logger.warning("Missions already running")
            return
        
        if not self.mission_queue and not self.current_mission:
            logger.warning("No missions in queue to start")
            return
        
        # If no active mission but queue has missions, get the next one
        if not self.current_mission and self.mission_queue:
            mission_type, self.current_mission = self.mission_queue.pop(0)
            logger.info(f"Starting {mission_type} mission")
        
        self.status = MissionStatus.RUNNING
        self.mission_start_time = time.time()
        logger.info("Mission execution started")
    
    def pause_missions(self) -> None:
        """Pause the current mission execution."""
        if self.status == MissionStatus.RUNNING:
            self.status = MissionStatus.PAUSED
            logger.info("Mission execution paused")
    
    def resume_missions(self) -> None:
        """Resume the current mission execution if paused."""
        if self.status == MissionStatus.PAUSED:
            self.status = MissionStatus.RUNNING
            logger.info("Mission execution resumed")
    
    def abort_missions(self) -> None:
        """Abort all missions and clear the queue."""
        prev_status = self.status
        self.status = MissionStatus.ABORTED
        self.mission_queue = []
        
        if prev_status != MissionStatus.IDLE:
            if self.current_mission:
                self.mission_history.append({
                    "mission_type": self._get_mission_type(self.current_mission),
                    "status": "aborted",
                    "timestamp": time.time()
                })
            self.current_mission = None
        
        logger.info("All missions aborted")
    
    def update(self, position: Tuple[float, float], heading: float) -> Dict[str, Any]:
        """
        Update the mission manager with current vehicle state.
        
        Args:
            position: Current (latitude, longitude) of the vehicle
            heading: Current heading of the vehicle in degrees
            
        Returns:
            Dict containing mission status and guidance information
        """
        # Update position and heading
        self.current_position = position
        self.current_heading = heading
        
        # Default return for non-running states
        if self.status != MissionStatus.RUNNING:
            return {
                "status": self.status.value,
                "guidance": None,
                "mission_info": None,
                "mission_type": None
            }
        
        # If no current mission but queue has missions, get the next one
        if not self.current_mission and self.mission_queue:
            mission_type, self.current_mission = self.mission_queue.pop(0)
            self.mission_start_time = time.time()
            logger.info(f"Starting {mission_type} mission")
        
        # If no missions at all, go to idle
        if not self.current_mission:
            self.status = MissionStatus.IDLE
            return {
                "status": self.status.value,
                "guidance": None,
                "mission_info": None,
                "mission_type": None
            }
        
        # Update the current mission
        mission_type = self._get_mission_type(self.current_mission)
        mission_info = None
        guidance = None
        
        try:
            # Different update method signature for docking mission
            if mission_type == "docking":
                mission_info = self.current_mission.update(position, heading)
                guidance = self.current_mission.get_guidance_command(position, heading)
            else:
                mission_info = self.current_mission.update(position)
                guidance = self.current_mission.get_guidance_command(position)
                
            # Check if mission is complete
            if mission_info.get('mission_complete', False) or guidance.get('is_complete', False):
                logger.info(f"{mission_type.capitalize()} mission completed")
                
                # Record in history
                if self.mission_start_time is not None:
                    self.mission_history.append({
                        "mission_type": mission_type,
                        "status": "completed",
                        "duration": time.time() - self.mission_start_time,
                        "timestamp": time.time()
                    })
                else:
                    self.mission_history.append({
                        "mission_type": mission_type,
                        "status": "completed",
                        "duration": 0.0,
                        "timestamp": time.time()
                    })
                
                # Move to next mission if available
                if self.mission_queue:
                    next_mission_type, self.current_mission = self.mission_queue.pop(0)
                    self.mission_start_time = time.time()
                    logger.info(f"Starting next mission: {next_mission_type}")
                else:
                    self.current_mission = None
                    self.status = MissionStatus.COMPLETED
                    logger.info("All missions completed")
        
        except Exception as e:
            logger.error(f"Error updating mission: {str(e)}")
            self.status = MissionStatus.ERROR
        
        return {
            "status": self.status.value,
            "guidance": guidance,
            "mission_info": mission_info,
            "mission_type": mission_type
        }
    
    def _get_mission_type(self, mission) -> str:
        """
        Get the type of mission from mission object.
        
        Args:
            mission: Mission object
            
        Returns:
            String representing mission type
        """
        if isinstance(mission, WaypointMission):
            return "waypoint"
        elif isinstance(mission, StationKeepingMission):
            return "station_keeping"
        elif isinstance(mission, DockingMission):
            return "docking"
        else:
            return "unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the mission manager.
        
        Returns:
            Dict containing status information
        """
        result = {
            "status": self.status.value,
            "missions_queued": len(self.mission_queue),
            "current_position": self.current_position,
            "current_heading": self.current_heading,
            "missions_completed": len(self.mission_history)
        }
        
        if self.current_mission:
            result["active_mission"] = {
                "type": self._get_mission_type(self.current_mission),
                "running_time": time.time() - self.mission_start_time if self.mission_start_time is not None else 0
            }
        
        return result
