"""
Main entry point for the USV Mission Planner.

This script demonstrates how to use the mission planner to create and
execute missions for an unmanned surface vehicle.
"""

import time
import math
import argparse
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict, Any

from missions.waypoint_mission import WaypointMission
from missions.station_keeping import StationKeepingMission
from missions.docking import DockingMission
from planners.mission_manager import MissionManager, MissionStatus
from planners.path_planner import PathPlanner
from utils.geo_utils import calculate_distance, calculate_bearing, offset_position, haversine_distance
from utils.config import load_config, get_config_value
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

class USVSimulator:
    """
    Simple USV simulator for testing the mission planner.
    
    Attributes:
        position: Current (latitude, longitude) of the simulated USV
        heading: Current heading in degrees
        speed: Current speed in m/s
        max_speed: Maximum speed in m/s
        turn_rate: Maximum turn rate in degrees/s
    """
    
    def __init__(
        self, 
        initial_position: Tuple[float, float],
        initial_heading: float = 0.0,
        max_speed: float = 2.0,
        turn_rate: float = 15.0
    ):
        """
        Initialize the USV simulator.
        
        Args:
            initial_position: Starting (latitude, longitude)
            initial_heading: Starting heading in degrees
            max_speed: Maximum speed in m/s
            turn_rate: Maximum turn rate in degrees/s
        """
        self.position = initial_position
        self.heading = initial_heading
        self.speed = 0.0
        self.max_speed = max_speed
        self.turn_rate = turn_rate
        self.track = [initial_position]
        logger.info(f"Initialized USV simulator at {initial_position} with heading {initial_heading}°")
    
    def update(self, desired_heading: float, desired_speed: float, dt: float) -> None:
        """
        Update the USV state for one time step.
        
        Args:
            desired_heading: Target heading in degrees
            desired_speed: Target speed in m/s
            dt: Time step in seconds
        """
        # Limit desired speed to max
        desired_speed = min(desired_speed, self.max_speed)
        
        # Calculate heading change
        heading_error = ((desired_heading - self.heading + 180) % 360) - 180
        max_heading_change = self.turn_rate * dt
        heading_change = max(min(heading_error, max_heading_change), -max_heading_change)
        
        # Update heading
        self.heading = (self.heading + heading_change) % 360
        
        # Update speed (with simple dynamics)
        accel = 0.5  # m/s²
        speed_change = min(accel * dt, abs(desired_speed - self.speed))
        
        if self.speed < desired_speed:
            self.speed += speed_change
        elif self.speed > desired_speed:
            self.speed -= speed_change
        
        # Move the USV based on heading and speed
        if self.speed > 0.001:  # Only move if speed is non-zero
            distance = self.speed * dt
            new_position = offset_position(
                self.position[0], self.position[1],
                self.heading, distance
            )
            self.position = new_position
            self.track.append(new_position)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the USV.
        
        Returns:
            Dict containing position, heading, and speed
        """
        return {
            'position': self.position,
            'heading': self.heading,
            'speed': self.speed
        }

def run_simulation(config_path: str = "", display: bool = True):
    """
    Run a simulation with the mission planner.
    
    Args:
        config_path: Path to configuration file
        display: Whether to display the visualization
    """
    # Load configuration
    config = load_config(config_path)
    
    # Setup logging
    log_level = get_config_value("logging", "level", "INFO")
    log_file = get_config_value("logging", "file_path", "usv_mission.log")
    setup_logging(log_level, log_file)
    
    logger.info("Starting USV mission planner simulation")
    
    # Create mission manager
    mission_manager = MissionManager()
    
    # Create simulated USV
    start_position = (-41.2865, 174.7762)  # Wellington, New Zealand
    usv = USVSimulator(
        initial_position=start_position,
        initial_heading=0.0,
        max_speed=get_config_value("vehicle", "max_speed", 2.0),
        turn_rate=get_config_value("vehicle", "turn_rate", 15.0)
    )
    
    # Define some waypoints around New Zealand
    waypoints = [
        (-41.2865, 174.7762),  # Wellington
        (-36.8485, 174.7633),  # Auckland
        (-43.5321, 172.6362),  # Christchurch
        (-45.0312, 168.6626),  # Queenstown
        (-37.7833, 175.2833)   # Hamilton
    ]
    
    # Define station keeping point
    station_point = (-41.2865, 174.7762)  # Wellington Harbor
    
    # Define docking point
    dock_point = (-36.8485, 174.7633)  # Auckland Marina
    dock_heading = 270.0
    
    # Add missions to the mission manager
    mission_manager.add_waypoint_mission(waypoints)
    mission_manager.add_station_keeping_mission(
        station_point, 
        radius=get_config_value("mission", "default_station_keeping_radius", 10.0),
        duration=get_config_value("mission", "default_station_keeping_duration", 300.0)
    )
    mission_manager.add_docking_mission(dock_point, dock_heading)
    
    # Start the missions
    mission_manager.start_missions()
    
    # Setup visualization if enabled
    if display:
        plt.figure(figsize=(10, 8))
        plt.ion()  # Enable interactive mode
    
    # Simulation parameters
    dt = get_config_value("simulation", "time_step", 0.1)
    sim_time = 0.0
    max_sim_time = 1000.0  # Maximum simulation time
    
    # Time acceleration factor
    time_accel = 10.0  # Run simulation 10x faster than real-time
    
    # Set up simulation status tracking
    last_display_time = 0.0
    display_interval = 1.0  # Update display every 1 simulated second
    
    # Main simulation loop
    while sim_time < max_sim_time:
        # Get USV state
        usv_state = usv.get_state()
        
        # Update mission manager with current position
        result = mission_manager.update(usv_state['position'], usv_state['heading'])
        
        # Get guidance command
        guidance = result.get('guidance')
        
        # Check if missions are complete
        if result['status'] == MissionStatus.COMPLETED.value:
            logger.info("All missions completed!")
            break
        
        # Check if there's an error
        if result['status'] in [MissionStatus.ERROR.value, MissionStatus.ABORTED.value]:
            logger.error(f"Mission error or aborted: {result['status']}")
            break
        
        # Apply guidance if available
        if guidance and result['status'] == MissionStatus.RUNNING.value:
            desired_heading = guidance.get('heading', usv_state['heading'])
            
            # Calculate desired speed based on thrust
            if 'thrust' in guidance:
                desired_speed = guidance['thrust'] * usv.max_speed
            else:
                # For waypoint missions, adjust speed based on distance
                distance = guidance.get('distance', 0.0)
                if distance > 100.0:
                    desired_speed = usv.max_speed
                elif distance > 20.0:
                    desired_speed = usv.max_speed * 0.7
                else:
                    desired_speed = usv.max_speed * 0.4
        else:
            # No guidance, stop the USV
            desired_heading = usv_state['heading']
            desired_speed = 0.0
        
        # Update USV simulation
        usv.update(desired_heading, desired_speed, dt)
        
        # Update visualization at regular intervals
        if display and (sim_time - last_display_time >= display_interval):
            last_display_time = sim_time
            
            # Clear the plot
            plt.clf()
            
            # Plot the track
            track = np.array(usv.track)
            plt.plot(track[:, 1], track[:, 0], 'b-', alpha=0.5)
            plt.plot(track[-1, 1], track[-1, 0], 'bo', markersize=8)
            
            # Plot waypoints
            if result['mission_type'] == 'waypoint':
                wp_array = np.array(waypoints)
                plt.plot(wp_array[:, 1], wp_array[:, 0], 'ro', markersize=6)
                
                # Connect waypoints with solid lines
                plt.plot(wp_array[:, 1], wp_array[:, 0], 'r-', alpha=0.7)
                
                # Highlight current waypoint
                if mission_manager.current_mission:
                    current_wp_idx = mission_manager.current_mission.current_waypoint_index
                    if current_wp_idx < len(waypoints):
                        current_wp = waypoints[current_wp_idx]
                        plt.plot(current_wp[1], current_wp[0], 'go', markersize=10)
                        
                        # Calculate and display distance to next waypoint
                        dist_to_wp = haversine_distance(usv_state['position'], current_wp)
                        wp_text = f"{dist_to_wp:.0f}m"
                        text_x = (usv_state['position'][1] + current_wp[1]) / 2
                        text_y = (usv_state['position'][0] + current_wp[0]) / 2
                        plt.text(text_x, text_y, wp_text, fontsize=9, 
                                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Plot station keeping point
            elif result['mission_type'] == 'station_keeping':
                plt.plot(station_point[1], station_point[0], 'ro', markersize=10)
                
                # Draw the station keeping circle
                if mission_manager.current_mission:
                    radius_deg = mission_manager.current_mission.tolerance_radius / 111000.0  # Approx conversion
                    circle = plt.Circle(
                        (station_point[1], station_point[0]), 
                        radius_deg, 
                        fill=False, 
                        color='r',
                        linestyle='--'
                    )
                    plt.gca().add_patch(circle)
                    
                    # Calculate and display distance to station keeping point
                    dist_to_station = haversine_distance(usv_state['position'], station_point)
                    station_text = f"{dist_to_station:.0f}m"
                    text_x = (usv_state['position'][1] + station_point[1]) / 2
                    text_y = (usv_state['position'][0] + station_point[0]) / 2
                    plt.text(text_x, text_y, station_text, fontsize=9, 
                             bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Plot docking point
            elif result['mission_type'] == 'docking':
                plt.plot(dock_point[1], dock_point[0], 'rs', markersize=10)
                
                # Draw docking direction
                arrow_length = 0.001  # About 100 meters
                dx = arrow_length * math.sin(math.radians(dock_heading))
                dy = arrow_length * math.cos(math.radians(dock_heading))
                plt.arrow(
                    dock_point[1], dock_point[0], 
                    dx, dy, 
                    head_width=0.0003, 
                    head_length=0.0005, 
                    fc='r', 
                    ec='r'
                )
                
                # Calculate and display distance to docking point
                dist_to_dock = haversine_distance(usv_state['position'], dock_point)
                dock_text = f"{dist_to_dock:.0f}m"
                text_x = (usv_state['position'][1] + dock_point[1]) / 2
                text_y = (usv_state['position'][0] + dock_point[0]) / 2
                plt.text(text_x, text_y, dock_text, fontsize=9, 
                         bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
            
            # Set plot limits with some padding
            pad = 0.02
            plt.xlim(min(track[:, 1]) - pad, max(track[:, 1]) + pad)
            plt.ylim(min(track[:, 0]) - pad, max(track[:, 0]) + pad)
            
            # Add status information
            status_text = f"Time: {sim_time:.1f}s\n"
            status_text += f"Mission: {result['mission_type']}\n"
            status_text += f"Status: {result['status']}\n"
            status_text += f"Position: ({usv_state['position'][0]:.6f}, {usv_state['position'][1]:.6f})\n"
            status_text += f"Heading: {usv_state['heading']:.1f}°\n"
            status_text += f"Speed: {usv_state['speed']:.2f} m/s"
            
            plt.title(status_text, loc='left')
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.grid(True)
            
            # Update the display
            plt.draw()
            plt.pause(0.001)
        
        # Increment simulation time
        sim_time += dt * time_accel
        
        # Small delay to not overload the CPU
        time.sleep(0.01)
    
    # Final status of mission manager
    logger.info(f"Final mission manager status: {mission_manager.get_status()}")
    
    # Keep plot open if display is enabled
    if display:
        plt.ioff()
        plt.show()

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='USV Mission Planner')
    parser.add_argument(
        '--config', 
        type=str, 
        help='Path to configuration file', 
        default=None
    )
    parser.add_argument(
        '--no-display', 
        action='store_true', 
        help='Disable visualization'
    )
    args = parser.parse_args()
    
    # Run the simulation
    run_simulation(args.config, not args.no_display)

if __name__ == '__main__':
    main()
