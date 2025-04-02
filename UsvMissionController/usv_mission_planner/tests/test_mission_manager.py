"""
Unit tests for the Mission Manager.

This module contains tests to verify the functionality of the 
MissionManager class.
"""

import unittest
from unittest.mock import patch
import time
from usv_mission_planner.planners.mission_manager import MissionManager, MissionStatus
from usv_mission_planner.missions.waypoint_mission import WaypointMission
from usv_mission_planner.missions.station_keeping import StationKeepingMission
from usv_mission_planner.missions.docking import DockingMission

class TestMissionManager(unittest.TestCase):
    """Test cases for the MissionManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a MissionManager instance for testing
        self.mission_manager = MissionManager()
        
        # Define test coordinates
        self.test_coords = [(37.7749, -122.4194), (37.7750, -122.4180), (37.7755, -122.4130)]
        self.test_position = (37.7748, -122.4195)  # Starting position
    
    def test_init(self):
        """Test the initialization of the MissionManager."""
        self.assertEqual(self.mission_manager.status, MissionStatus.IDLE)
        self.assertEqual(self.mission_manager.mission_queue, [])
        self.assertIsNone(self.mission_manager.current_mission)
    
    def test_add_waypoint_mission(self):
        """Test adding a waypoint mission to the queue."""
        self.mission_manager.add_waypoint_mission(self.test_coords)
        
        # Check that mission was added to queue
        self.assertEqual(len(self.mission_manager.mission_queue), 1)
        self.assertEqual(self.mission_manager.mission_queue[0][0], "waypoint")
        
        # Check mission object
        mission_obj = self.mission_manager.mission_queue[0][1]
        self.assertIsInstance(mission_obj, WaypointMission)
        self.assertEqual(mission_obj.waypoints, self.test_coords)
    
    def test_add_station_keeping_mission(self):
        """Test adding a station keeping mission to the queue."""
        position = self.test_coords[0]
        radius = 15.0
        duration = 120.0
        
        self.mission_manager.add_station_keeping_mission(position, radius, duration)
        
        # Check that mission was added to queue
        self.assertEqual(len(self.mission_manager.mission_queue), 1)
        self.assertEqual(self.mission_manager.mission_queue[0][0], "station_keeping")
        
        # Check mission object
        mission_obj = self.mission_manager.mission_queue[0][1]
        self.assertIsInstance(mission_obj, StationKeepingMission)
        self.assertEqual(mission_obj.target_position, position)
        self.assertEqual(mission_obj.tolerance_radius, radius)
        self.assertEqual(mission_obj.duration, duration)
    
    def test_add_docking_mission(self):
        """Test adding a docking mission to the queue."""
        dock_position = self.test_coords[0]
        dock_heading = 45.0
        
        self.mission_manager.add_docking_mission(dock_position, dock_heading)
        
        # Check that mission was added to queue
        self.assertEqual(len(self.mission_manager.mission_queue), 1)
        self.assertEqual(self.mission_manager.mission_queue[0][0], "docking")
        
        # Check mission object
        mission_obj = self.mission_manager.mission_queue[0][1]
        self.assertIsInstance(mission_obj, DockingMission)
        self.assertEqual(mission_obj.dock_position, dock_position)
        self.assertEqual(mission_obj.dock_heading, dock_heading)
    
    def test_start_missions(self):
        """Test starting mission execution."""
        # Add a mission
        self.mission_manager.add_waypoint_mission(self.test_coords)
        
        # Start missions
        self.mission_manager.start_missions()
        
        # Check status
        self.assertEqual(self.mission_manager.status, MissionStatus.RUNNING)
        self.assertIsNotNone(self.mission_manager.current_mission)
        self.assertEqual(len(self.mission_manager.mission_queue), 0)
    
    def test_pause_resume_missions(self):
        """Test pausing and resuming mission execution."""
        # Add and start a mission
        self.mission_manager.add_waypoint_mission(self.test_coords)
        self.mission_manager.start_missions()
        
        # Pause mission
        self.mission_manager.pause_missions()
        self.assertEqual(self.mission_manager.status, MissionStatus.PAUSED)
        
        # Resume mission
        self.mission_manager.resume_missions()
        self.assertEqual(self.mission_manager.status, MissionStatus.RUNNING)
    
    def test_abort_missions(self):
        """Test aborting mission execution."""
        # Add and start missions
        self.mission_manager.add_waypoint_mission(self.test_coords)
        self.mission_manager.add_station_keeping_mission(self.test_coords[0])
        self.mission_manager.start_missions()
        
        # Abort missions
        self.mission_manager.abort_missions()
        
        # Check status
        self.assertEqual(self.mission_manager.status, MissionStatus.ABORTED)
        self.assertIsNone(self.mission_manager.current_mission)
        self.assertEqual(len(self.mission_manager.mission_queue), 0)
        self.assertEqual(len(self.mission_manager.mission_history), 1)
    
    def test_update(self):
        """Test updating the mission manager with a position."""
        # Add and start a waypoint mission
        waypoints = [
            (37.7749, -122.4194),  # Only 10 meters from test_position
            (37.8000, -122.4180)   # Far away
        ]
        self.mission_manager.add_waypoint_mission(waypoints, arrival_radius=15.0)
        self.mission_manager.start_missions()
        
        # Update with position close to first waypoint (should reach it)
        result = self.mission_manager.update(self.test_position, 90.0)
        
        # Check result
        self.assertEqual(result["status"], MissionStatus.RUNNING.value)
        self.assertEqual(result["mission_type"], "waypoint")
        self.assertIsNotNone(result["guidance"])
        self.assertIsNotNone(result["mission_info"])
        
        # Should have moved to the next waypoint
        self.assertEqual(self.mission_manager.current_mission.current_waypoint_index, 1)
    
    def test_mission_completion(self):
        """Test that missions complete correctly and the queue advances."""
        # Add two missions
        self.mission_manager.add_waypoint_mission([self.test_position], arrival_radius=10.0)
        self.mission_manager.add_station_keeping_mission(self.test_coords[0])
        
        # Start missions
        self.mission_manager.start_missions()
        
        # Update with position at the waypoint (should complete waypoint mission)
        result = self.mission_manager.update(self.test_position, 90.0)
        
        # Check that first mission completed and second started
        self.assertEqual(result["status"], MissionStatus.RUNNING.value)
        self.assertEqual(result["mission_type"], "station_keeping")
        self.assertEqual(len(self.mission_manager.mission_history), 1)
    
    def test_get_status(self):
        """Test getting the status of the mission manager."""
        status = self.mission_manager.get_status()
        
        # Check basic status fields
        self.assertEqual(status["status"], MissionStatus.IDLE.value)
        self.assertEqual(status["missions_queued"], 0)
        self.assertEqual(status["missions_completed"], 0)
        
        # Add and start a mission
        self.mission_manager.add_waypoint_mission(self.test_coords)
        self.mission_manager.start_missions()
        
        # Get updated status
        status = self.mission_manager.get_status()
        
        # Check updated fields
        self.assertEqual(status["status"], MissionStatus.RUNNING.value)
        self.assertEqual(status["missions_queued"], 0)
        self.assertEqual(status["missions_completed"], 0)
        self.assertIn("active_mission", status)
        self.assertEqual(status["active_mission"]["type"], "waypoint")

if __name__ == '__main__':
    unittest.main()
