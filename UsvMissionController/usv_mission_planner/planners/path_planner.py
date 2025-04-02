"""
Path Planner implementation for USV.

This module provides functionality for planning paths between waypoints
considering obstacles and environmental constraints.
"""

import numpy as np
import math
from typing import List, Tuple, Dict, Any, Optional
from utils.geo_utils import calculate_distance, calculate_bearing, offset_position
from utils.logger import get_logger

logger = get_logger(__name__)

class PathPlanner:
    """
    Path planner for USV navigation.
    
    Includes functionality for:
    - Simple waypoint-to-waypoint planning
    - A* path planning through obstacle fields
    - RRT (Rapidly-exploring Random Tree) for complex environments
    
    Attributes:
        planning_mode: The algorithm to use for path planning
        safe_distance: Minimum safe distance in meters from obstacles
        grid_size: Size of grid cells in meters for discretized planning
        obstacles: List of obstacle positions and radii
    """
    
    def __init__(
        self, 
        planning_mode: str = "waypoint",
        safe_distance: float = 10.0,
        grid_size: float = 5.0
    ):
        """
        Initialize the path planner.
        
        Args:
            planning_mode: Algorithm to use ('waypoint', 'astar', or 'rrt')
            safe_distance: Minimum distance to keep from obstacles in meters
            grid_size: Size of grid cells in meters for discrete planning
        """
        self.planning_mode = planning_mode
        self.safe_distance = safe_distance
        self.grid_size = grid_size
        self.obstacles = []  # List of (lat, lon, radius) tuples
        logger.info(f"Path planner initialized with {planning_mode} mode")
    
    def set_obstacles(self, obstacles: List[Tuple[float, float, float]]) -> None:
        """
        Set the list of obstacles for path planning.
        
        Args:
            obstacles: List of (latitude, longitude, radius) tuples representing obstacles
        """
        self.obstacles = obstacles
        logger.info(f"Set {len(obstacles)} obstacles for path planning")
    
    def plan_path(
        self, 
        start: Tuple[float, float], 
        goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """
        Plan a path from start to goal position.
        
        Args:
            start: Starting position as (latitude, longitude)
            goal: Goal position as (latitude, longitude)
            
        Returns:
            List of waypoints as (latitude, longitude) tuples forming the path
        """
        if self.planning_mode == "waypoint":
            return self._plan_direct_path(start, goal)
        elif self.planning_mode == "astar":
            return self._plan_astar_path(start, goal)
        elif self.planning_mode == "rrt":
            return self._plan_rrt_path(start, goal)
        else:
            logger.warning(f"Unknown planning mode: {self.planning_mode}, falling back to direct path")
            return self._plan_direct_path(start, goal)
    
    def _plan_direct_path(
        self, 
        start: Tuple[float, float], 
        goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """
        Plan a direct path between start and goal.
        
        Args:
            start: Starting position as (latitude, longitude)
            goal: Goal position as (latitude, longitude)
            
        Returns:
            List containing start and goal waypoints
        """
        logger.info(f"Planning direct path from {start} to {goal}")
        
        # Check for collision with obstacles
        for obs_lat, obs_lon, obs_radius in self.obstacles:
            # Check if the direct path intersects with any obstacle
            intersects = self._line_intersects_circle(
                start, goal, (obs_lat, obs_lon), obs_radius + self.safe_distance
            )
            
            if intersects:
                logger.warning("Direct path intersects obstacle, consider using A* or RRT planner")
                # Still return direct path but with warning
        
        return [start, goal]
    
    def _plan_astar_path(
        self, 
        start: Tuple[float, float], 
        goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """
        Plan a path using A* algorithm.
        
        Args:
            start: Starting position as (latitude, longitude)
            goal: Goal position as (latitude, longitude)
            
        Returns:
            List of waypoints forming the path
        """
        logger.info(f"Planning A* path from {start} to {goal}")
        
        # Create simplified grid representation for demonstration purposes
        # Note: A full A* implementation would use a proper grid and heuristic
        
        # This is a simplified implementation that:
        # 1. Creates intermediate waypoints between start and goal
        # 2. Checks each waypoint for obstacle collision
        # 3. If collision detected, creates a waypoint to go around the obstacle
        
        path = [start]
        current = start
        
        # Set a maximum number of iterations to prevent infinite loops
        max_iterations = 100
        iteration = 0
        
        # Keep trying to reach the goal
        while iteration < max_iterations and calculate_distance(current[0], current[1], goal[0], goal[1]) > self.grid_size:
            iteration += 1
            
            # Direct bearing to goal
            bearing = calculate_bearing(current[0], current[1], goal[0], goal[1])
            
            # Tentative next point at one grid step towards goal
            distance_to_goal = calculate_distance(current[0], current[1], goal[0], goal[1])
            step_distance = min(self.grid_size, distance_to_goal)
            
            next_point = offset_position(current[0], current[1], bearing, step_distance)
            
            # Check for obstacle collisions
            collision = False
            avoidance_point = None
            
            for obs_lat, obs_lon, obs_radius in self.obstacles:
                distance_to_obs = calculate_distance(next_point[0], next_point[1], obs_lat, obs_lon)
                
                if distance_to_obs < (obs_radius + self.safe_distance):
                    collision = True
                    
                    # Calculate avoidance waypoint
                    # Determine which side to go around the obstacle
                    obs_bearing = calculate_bearing(current[0], current[1], obs_lat, obs_lon)
                    bearing_diff = (obs_bearing - bearing) % 360
                    
                    if bearing_diff < 180:
                        # Go right of obstacle
                        avoidance_bearing = (obs_bearing + 90) % 360
                    else:
                        # Go left of obstacle
                        avoidance_bearing = (obs_bearing - 90) % 360
                    
                    # Create waypoint that avoids the obstacle
                    avoidance_distance = obs_radius + self.safe_distance + 5.0  # Extra margin
                    avoidance_point = offset_position(obs_lat, obs_lon, avoidance_bearing, avoidance_distance)
                    break
            
            if collision and avoidance_point:
                # Add the avoidance point to path
                path.append(avoidance_point)
                current = avoidance_point
                logger.info(f"Added avoidance waypoint at {avoidance_point}")
            else:
                # No collision, proceed toward goal
                path.append(next_point)
                current = next_point
        
        # Add goal to path if not already reached
        if path[-1] != goal:
            path.append(goal)
        
        logger.info(f"A* planning completed with {len(path)} waypoints")
        return path
    
    def _plan_rrt_path(
        self, 
        start: Tuple[float, float], 
        goal: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        """
        Plan a path using RRT (Rapidly-exploring Random Tree) algorithm.
        
        Args:
            start: Starting position as (latitude, longitude)
            goal: Goal position as (latitude, longitude)
            
        Returns:
            List of waypoints forming the path
        """
        logger.info(f"Planning RRT path from {start} to {goal}")
        
        # Simple RRT implementation for demonstration
        # In a real implementation, this would be more sophisticated
        
        # Initialize the tree with start position
        tree = [start]
        parents = {0: None}  # Maps node index to parent index
        
        # Define the bounding box for sampling random points
        # Calculate a reasonable bounding box around start and goal
        lat_min = min(start[0], goal[0]) - 0.01  # Approx 1 km
        lat_max = max(start[0], goal[0]) + 0.01
        lon_min = min(start[1], goal[1]) - 0.01
        lon_max = max(start[1], goal[1]) + 0.01
        
        # RRT parameters
        max_iterations = 200
        goal_sample_rate = 0.1  # Probability of sampling the goal directly
        max_step_size = self.grid_size * 2
        
        # Run RRT algorithm
        goal_idx = None
        
        for i in range(max_iterations):
            # Sample random point (with bias toward goal)
            if np.random.random() < goal_sample_rate:
                random_point = goal
            else:
                random_lat = np.random.uniform(lat_min, lat_max)
                random_lon = np.random.uniform(lon_min, lon_max)
                random_point = (random_lat, random_lon)
            
            # Find nearest node in tree
            nearest_idx = self._find_nearest_node(tree, random_point)
            nearest_node = tree[nearest_idx]
            
            # Create new node in the direction of random point
            bearing = calculate_bearing(nearest_node[0], nearest_node[1], random_point[0], random_point[1])
            distance = calculate_distance(nearest_node[0], nearest_node[1], random_point[0], random_point[1])
            
            # Limit step size
            if distance > max_step_size:
                distance = max_step_size
            
            # Create new node
            new_node = offset_position(nearest_node[0], nearest_node[1], bearing, distance)
            
            # Check if new node collides with obstacles
            if self._is_collision_free(nearest_node, new_node):
                # Add new node to tree
                tree.append(new_node)
                new_idx = len(tree) - 1
                parents[new_idx] = nearest_idx
                
                # Check if we can connect to goal
                distance_to_goal = calculate_distance(new_node[0], new_node[1], goal[0], goal[1])
                
                if distance_to_goal < max_step_size:
                    # Try connecting to goal
                    if self._is_collision_free(new_node, goal):
                        # Successfully connected to goal
                        tree.append(goal)
                        goal_idx = len(tree) - 1
                        parents[goal_idx] = new_idx
                        break
        
        # Reconstruct path if goal was reached
        path = []
        if goal_idx is not None:
            # Follow parents backward from goal to start
            current_idx = goal_idx
            while current_idx is not None:
                path.append(tree[current_idx])
                current_idx = parents[current_idx]
            
            # Reverse path to get start-to-goal order
            path.reverse()
            logger.info(f"RRT planning completed with {len(path)} waypoints")
        else:
            logger.warning("RRT failed to reach goal, fallback to direct path")
            path = [start, goal]
        
        return path
    
    def _find_nearest_node(self, tree: List[Tuple[float, float]], point: Tuple[float, float]) -> int:
        """
        Find the nearest node in the tree to the given point.
        
        Args:
            tree: List of nodes in the tree
            point: Target point
            
        Returns:
            Index of the nearest node in the tree
        """
        min_dist = float('inf')
        min_idx = 0
        
        for i, node in enumerate(tree):
            dist = calculate_distance(node[0], node[1], point[0], point[1])
            if dist < min_dist:
                min_dist = dist
                min_idx = i
        
        return min_idx
    
    def _is_collision_free(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """
        Check if a path segment is collision-free.
        
        Args:
            start: Starting point of segment
            end: Ending point of segment
            
        Returns:
            True if the segment is collision-free, False otherwise
        """
        for obs_lat, obs_lon, obs_radius in self.obstacles:
            if self._line_intersects_circle(start, end, (obs_lat, obs_lon), obs_radius + self.safe_distance):
                return False
        
        return True
    
    def _line_intersects_circle(
        self, 
        line_start: Tuple[float, float], 
        line_end: Tuple[float, float],
        circle_center: Tuple[float, float],
        circle_radius: float
    ) -> bool:
        """
        Check if a line segment intersects with a circle.
        
        Args:
            line_start: Starting point of line segment
            line_end: Ending point of line segment
            circle_center: Center of the circle
            circle_radius: Radius of the circle in meters
            
        Returns:
            True if the line intersects the circle, False otherwise
        """
        # Convert to simpler variable names for readability
        x1, y1 = line_start
        x2, y2 = line_end
        cx, cy = circle_center
        r = circle_radius
        
        # Check if either endpoint is inside the circle
        if calculate_distance(x1, y1, cx, cy) <= r or calculate_distance(x2, y2, cx, cy) <= r:
            return True
        
        # Calculate the closest point on the line segment to the circle center
        # This is a simplified approximation since we're working with geographic coordinates
        
        # Vector from line_start to line_end
        dx = x2 - x1
        dy = y2 - y1
        
        # Square of the length of the line segment
        line_length_sq = dx*dx + dy*dy
        
        # If the line segment has zero length, it's just a point
        if line_length_sq == 0:
            return False  # Already checked endpoints above
        
        # Calculate the projection of the circle center onto the line
        t = max(0, min(1, ((cx - x1) * dx + (cy - y1) * dy) / line_length_sq))
        
        # Closest point on line segment to circle center
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Check if the closest point is within the circle radius
        closest_distance = calculate_distance(closest_x, closest_y, cx, cy)
        
        return closest_distance <= r
