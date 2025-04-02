"""
Collision Risk Assessment for USV Mission Planner.

This module evaluates collision risks such as obstacles, shipping lanes,
and proximity to shore or restricted areas.
"""

from typing import Dict, List, Any, Optional, Tuple
import math
from utils.logger import get_logger
from utils.geo_utils import calculate_distance
from risk_assessment.risk_analyzer import RiskFactor, RiskLevel

logger = get_logger(__name__)

class CollisionRiskAssessor:
    """
    Assesses collision risks for USV missions.
    
    Evaluates risks related to:
    - Static obstacles in the operational area
    - Proximity to shipping lanes
    - Proximity to shore
    - Restricted or regulated areas
    - Traffic density
    """
    
    def __init__(self):
        """Initialize the collision risk assessor."""
        logger.info("Collision risk assessor initialized")
    
    def assess_risks(
        self, 
        mission_data: Dict[str, Any],
        environment_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskFactor]:
        """
        Assess collision risks for a mission.
        
        Args:
            mission_data: Mission configuration and waypoints
            environment_data: Environmental conditions data including obstacles
            
        Returns:
            List of collision risk factors
        """
        risk_factors = []
        
        # Extract waypoints from mission data
        waypoints = self._extract_waypoints(mission_data)
        
        # Get obstacle data (static or from environment data)
        obstacles = self._get_obstacles(environment_data)
        
        # Assess risks related to static obstacles
        obstacle_risk = self._assess_obstacle_risk(waypoints, obstacles)
        risk_factors.append(obstacle_risk)
        
        # Assess proximity to shipping lanes
        shipping_lanes = self._get_shipping_lanes(environment_data)
        shipping_risk = self._assess_shipping_lane_risk(waypoints, shipping_lanes)
        risk_factors.append(shipping_risk)
        
        # Assess proximity to shore
        shorelines = self._get_shorelines(environment_data)
        shore_risk = self._assess_shore_proximity_risk(waypoints, shorelines)
        risk_factors.append(shore_risk)
        
        # Assess restricted areas
        restricted_areas = self._get_restricted_areas(environment_data)
        restricted_risk = self._assess_restricted_area_risk(waypoints, restricted_areas)
        risk_factors.append(restricted_risk)
        
        # Assess traffic density
        traffic_density = environment_data.get('traffic_density', 'low') if environment_data else 'low'
        traffic_risk = self._assess_traffic_density_risk(traffic_density)
        risk_factors.append(traffic_risk)
        
        logger.info(f"Completed collision risk assessment with {len(risk_factors)} factors")
        return risk_factors
    
    def _extract_waypoints(self, mission_data: Dict[str, Any]) -> List[Tuple[float, float]]:
        """
        Extract waypoints from mission data.
        
        Args:
            mission_data: Mission configuration and waypoints
            
        Returns:
            List of waypoints as (lat, lon) tuples
        """
        waypoints = []
        
        # Try to extract waypoints from different mission types
        if 'waypoints' in mission_data:
            waypoints = mission_data['waypoints']
        elif 'route' in mission_data:
            waypoints = mission_data['route']
        elif 'path' in mission_data:
            waypoints = mission_data['path']
        
        # For a complex mission with multiple segments
        if not waypoints and 'segments' in mission_data:
            for segment in mission_data['segments']:
                if 'waypoints' in segment:
                    waypoints.extend(segment['waypoints'])
        
        # Default waypoint for San Francisco Bay if none provided
        if not waypoints:
            waypoints = [
                (37.7749, -122.4194),  # San Francisco
                (37.8045, -122.4159),  # Golden Gate Bridge
                (37.8265, -122.3806),  # Alcatraz
                (37.8155, -122.3440),  # Berkeley
                (37.7955, -122.3828)   # Bay Area
            ]
        
        return waypoints
    
    def _get_obstacles(self, environment_data: Optional[Dict[str, Any]]) -> List[Tuple[float, float, float]]:
        """
        Get obstacles from environment data.
        
        Args:
            environment_data: Environmental data including obstacles
            
        Returns:
            List of obstacles as (lat, lon, radius) tuples
        """
        if not environment_data or 'obstacles' not in environment_data:
            # Default set of obstacles in San Francisco Bay
            return [
                (37.8270, -122.3770, 0.20),  # Obstacle near Alcatraz
                (37.8100, -122.4000, 0.15),  # Obstacle in the bay
                (37.7900, -122.3900, 0.10)   # Another obstacle
            ]
        
        return environment_data['obstacles']
    
    def _get_shipping_lanes(self, environment_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get shipping lanes from environment data.
        
        Args:
            environment_data: Environmental data including shipping lanes
            
        Returns:
            List of shipping lanes
        """
        if not environment_data or 'shipping_lanes' not in environment_data:
            # Default shipping lane in San Francisco Bay
            return [
                {
                    'name': 'SF Bay Main Channel',
                    'points': [
                        (37.8090, -122.4410),  # Start near Golden Gate
                        (37.8230, -122.3850),  # Middle of Bay near Alcatraz
                        (37.7930, -122.3560)   # East Bay
                    ],
                    'width': 1.0  # km
                }
            ]
        
        return environment_data['shipping_lanes']
    
    def _get_shorelines(self, environment_data: Optional[Dict[str, Any]]) -> List[List[Tuple[float, float]]]:
        """
        Get shorelines from environment data.
        
        Args:
            environment_data: Environmental data including shorelines
            
        Returns:
            List of shoreline coordinates
        """
        if not environment_data or 'shorelines' not in environment_data:
            # Simplified shoreline segments for San Francisco Bay
            return [
                # San Francisco shoreline segment
                [
                    (37.7580, -122.4150),
                    (37.7800, -122.4250),
                    (37.8000, -122.4400),
                    (37.8080, -122.4490)
                ],
                # Alcatraz Island
                [
                    (37.8262, -122.4228),
                    (37.8271, -122.4223),
                    (37.8279, -122.4227),
                    (37.8276, -122.4236),
                    (37.8267, -122.4238),
                    (37.8262, -122.4228)
                ]
            ]
        
        return environment_data['shorelines']
    
    def _get_restricted_areas(self, environment_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get restricted areas from environment data.
        
        Args:
            environment_data: Environmental data including restricted areas
            
        Returns:
            List of restricted areas
        """
        if not environment_data or 'restricted_areas' not in environment_data:
            # Default restricted areas in San Francisco Bay
            return [
                {
                    'name': 'Naval Restricted Zone',
                    'center': (37.7985, -122.3718),
                    'radius': 1.0  # km
                },
                {
                    'name': 'Protected Marine Area',
                    'center': (37.8290, -122.4020),
                    'radius': 0.5  # km
                }
            ]
        
        return environment_data['restricted_areas']
    
    def _assess_obstacle_risk(
        self, 
        waypoints: List[Tuple[float, float]],
        obstacles: List[Tuple[float, float, float]]
    ) -> RiskFactor:
        """
        Assess risk from obstacles along the mission path.
        
        Args:
            waypoints: List of mission waypoints
            obstacles: List of obstacles as (lat, lon, radius) tuples
            
        Returns:
            Obstacle risk factor
        """
        if not obstacles:
            return RiskFactor(
                name="Obstacle Collision",
                category="Collision",
                level=RiskLevel.LOW,
                description="No known obstacles in the operational area.",
                mitigation="Standard lookout procedures are sufficient.",
                weight=1.0
            )
        
        # Calculate minimum distance to any obstacle from any path segment
        min_distance = float('inf')
        closest_obstacle = None
        
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            
            for obstacle in obstacles:
                obs_lat, obs_lon, obs_radius = obstacle
                
                # Convert radius from km to meters for comparison
                obs_radius_m = obs_radius * 1000
                
                # Check distance from path segment to obstacle
                distance = self._point_to_line_segment_distance(
                    (obs_lat, obs_lon), start, end)
                
                # Convert to meters for comparison
                distance_m = distance * 1000
                
                if distance_m - obs_radius_m < min_distance:
                    min_distance = distance_m - obs_radius_m
                    closest_obstacle = obstacle
        
        # Assess risk based on minimum distance
        if min_distance < 0:  # Path intersects obstacle
            level = RiskLevel.CRITICAL
            desc = "Mission path intersects with an obstacle."
            mitigation = "Reroute mission path to avoid obstacle."
        elif min_distance < 50:
            level = RiskLevel.HIGH
            desc = "Mission path passes extremely close to an obstacle."
            mitigation = "Increase clearance from obstacle or add waypoints for safer navigation."
        elif min_distance < 200:
            level = RiskLevel.MEDIUM
            desc = "Mission path passes close to an obstacle."
            mitigation = "Monitor obstacle during mission execution and be prepared to adjust course."
        else:
            level = RiskLevel.LOW
            desc = "Mission path maintains safe distance from all obstacles."
            mitigation = "Standard obstacle avoidance procedures are sufficient."
        
        obstacle_info = ""
        if closest_obstacle:
            obs_lat, obs_lon, obs_radius = closest_obstacle
            obstacle_info = f" Closest obstacle at ({obs_lat:.4f}, {obs_lon:.4f}) with {obs_radius*1000:.0f}m radius."
        
        return RiskFactor(
            name="Obstacle Collision",
            category="Collision",
            level=level,
            description=desc + f" Minimum clearance: {max(0, min_distance):.1f}m." + obstacle_info,
            mitigation=mitigation,
            weight=1.0
        )
    
    def _assess_shipping_lane_risk(
        self, 
        waypoints: List[Tuple[float, float]],
        shipping_lanes: List[Dict[str, Any]]
    ) -> RiskFactor:
        """
        Assess risk from proximity to shipping lanes.
        
        Args:
            waypoints: List of mission waypoints
            shipping_lanes: List of shipping lanes
            
        Returns:
            Shipping lane risk factor
        """
        if not shipping_lanes:
            return RiskFactor(
                name="Shipping Lane Proximity",
                category="Collision",
                level=RiskLevel.LOW,
                description="No shipping lanes in the operational area.",
                mitigation="Normal traffic awareness procedures are sufficient.",
                weight=0.9
            )
        
        # Calculate minimum distance to any shipping lane from any path segment
        min_distance = float('inf')
        crossing_lanes = 0
        closest_lane = None
        
        for i in range(len(waypoints) - 1):
            path_segment = (waypoints[i], waypoints[i + 1])
            
            for lane in shipping_lanes:
                lane_points = lane['points']
                lane_width = lane['width']  # in km
                
                # Check if path crosses this lane
                for j in range(len(lane_points) - 1):
                    lane_segment = (lane_points[j], lane_points[j + 1])
                    
                    if self._line_segments_intersect(path_segment, lane_segment):
                        crossing_lanes += 1
                        min_distance = 0
                        closest_lane = lane
                        break
                
                if min_distance == 0:
                    continue
                
                # If not crossing, find minimum distance to lane
                for j in range(len(lane_points) - 1):
                    lane_segment = (lane_points[j], lane_points[j + 1])
                    
                    # Calculate minimum distance between path and lane segment
                    for wp in waypoints:
                        dist = self._point_to_line_segment_distance(wp, lane_segment[0], lane_segment[1])
                        
                        # Convert to meters and account for lane width
                        dist_m = (dist * 1000) - (lane_width * 500)  # Half width on each side
                        
                        if dist_m < min_distance:
                            min_distance = dist_m
                            closest_lane = lane
        
        # Assess risk based on crossing and minimum distance
        if crossing_lanes > 0:
            level = RiskLevel.HIGH
            desc = f"Mission path crosses {crossing_lanes} shipping lane(s)."
            mitigation = "Plan crossing perpendicular to lane direction and monitor marine traffic."
        elif min_distance < 100:
            level = RiskLevel.MEDIUM
            desc = "Mission path passes very close to a shipping lane."
            mitigation = "Monitor marine traffic and be prepared to give way."
        elif min_distance < 500:
            level = RiskLevel.LOW
            desc = "Mission path passes near a shipping lane."
            mitigation = "Standard traffic monitoring procedures are sufficient."
        else:
            level = RiskLevel.LOW
            desc = "Mission path maintains safe distance from all shipping lanes."
            mitigation = "Normal traffic awareness procedures are sufficient."
        
        lane_info = ""
        if closest_lane:
            lane_info = f" Closest lane: {closest_lane['name']}."
        
        return RiskFactor(
            name="Shipping Lane Proximity",
            category="Collision",
            level=level,
            description=desc + f" Minimum distance: {max(0, min_distance):.1f}m." + lane_info,
            mitigation=mitigation,
            weight=0.9
        )
    
    def _assess_shore_proximity_risk(
        self, 
        waypoints: List[Tuple[float, float]],
        shorelines: List[List[Tuple[float, float]]]
    ) -> RiskFactor:
        """
        Assess risk from proximity to shore.
        
        Args:
            waypoints: List of mission waypoints
            shorelines: List of shoreline coordinate lists
            
        Returns:
            Shore proximity risk factor
        """
        if not shorelines:
            return RiskFactor(
                name="Shore Proximity",
                category="Collision",
                level=RiskLevel.LOW,
                description="No shoreline data available for analysis.",
                mitigation="Use updated nautical charts for navigation.",
                weight=0.8
            )
        
        # Calculate minimum distance to any shoreline from any waypoint
        min_distance = float('inf')
        
        for waypoint in waypoints:
            for shoreline in shorelines:
                for i in range(len(shoreline) - 1):
                    shore_segment = (shoreline[i], shoreline[i + 1])
                    
                    dist = self._point_to_line_segment_distance(
                        waypoint, shore_segment[0], shore_segment[1])
                    
                    # Convert to meters
                    dist_m = dist * 1000
                    
                    if dist_m < min_distance:
                        min_distance = dist_m
        
        # Assess risk based on minimum distance to shore
        if min_distance < 25:
            level = RiskLevel.CRITICAL
            desc = "Mission path passes dangerously close to shore."
            mitigation = "Reroute to maintain safe distance from shore."
        elif min_distance < 100:
            level = RiskLevel.HIGH
            desc = "Mission path passes very close to shore."
            mitigation = "Adjust waypoints to increase clearance from shore."
        elif min_distance < 250:
            level = RiskLevel.MEDIUM
            desc = "Mission path passes near shore."
            mitigation = "Monitor position carefully when near shore."
        else:
            level = RiskLevel.LOW
            desc = "Mission path maintains safe distance from shore."
            mitigation = "Standard navigation procedures are sufficient."
        
        return RiskFactor(
            name="Shore Proximity",
            category="Collision",
            level=level,
            description=desc + f" Minimum distance to shore: {min_distance:.1f}m.",
            mitigation=mitigation,
            weight=0.8
        )
    
    def _assess_restricted_area_risk(
        self, 
        waypoints: List[Tuple[float, float]],
        restricted_areas: List[Dict[str, Any]]
    ) -> RiskFactor:
        """
        Assess risk from proximity to restricted areas.
        
        Args:
            waypoints: List of mission waypoints
            restricted_areas: List of restricted areas
            
        Returns:
            Restricted area risk factor
        """
        if not restricted_areas:
            return RiskFactor(
                name="Restricted Areas",
                category="Collision",
                level=RiskLevel.LOW,
                description="No restricted areas in the operational area.",
                mitigation="Standard navigation procedures are sufficient.",
                weight=0.7
            )
        
        # Check if any waypoint is inside a restricted area
        inside_areas = []
        min_distance = float('inf')
        closest_area = None
        
        for waypoint in waypoints:
            for area in restricted_areas:
                center = area['center']
                radius = area['radius']  # in km
                
                # Calculate distance to area center
                dist = calculate_distance(
                    waypoint[0], waypoint[1], center[0], center[1]) / 1000  # convert to km
                
                if dist < radius:
                    # Waypoint is inside restricted area
                    inside_areas.append(area['name'])
                elif dist - radius < min_distance:
                    min_distance = dist - radius
                    closest_area = area
        
        # Convert min_distance back to meters for display
        min_distance_m = min_distance * 1000
        
        # Assess risk based on inside areas and minimum distance
        if inside_areas:
            level = RiskLevel.CRITICAL
            areas_str = ", ".join(inside_areas)
            desc = f"Mission path enters restricted area(s): {areas_str}."
            mitigation = "Reroute mission to avoid all restricted areas."
        elif min_distance_m < 100:
            level = RiskLevel.HIGH
            desc = "Mission path passes very close to a restricted area."
            mitigation = "Adjust waypoints to increase clearance from restricted area."
        elif min_distance_m < 500:
            level = RiskLevel.MEDIUM
            desc = "Mission path passes near a restricted area."
            mitigation = "Monitor position carefully when near restricted area."
        else:
            level = RiskLevel.LOW
            desc = "Mission path maintains safe distance from all restricted areas."
            mitigation = "Standard navigation procedures are sufficient."
        
        area_info = ""
        if closest_area and not inside_areas:
            area_info = f" Closest restricted area: {closest_area['name']}."
        
        return RiskFactor(
            name="Restricted Areas",
            category="Collision",
            level=level,
            description=desc + f" Minimum distance: {max(0, min_distance_m):.1f}m." + area_info,
            mitigation=mitigation,
            weight=0.7
        )
    
    def _assess_traffic_density_risk(self, traffic_density: str) -> RiskFactor:
        """
        Assess risk based on traffic density in the operational area.
        
        Args:
            traffic_density: Traffic density classification (low, medium, high)
            
        Returns:
            Traffic density risk factor
        """
        if traffic_density.lower() == 'low':
            level = RiskLevel.LOW
            desc = "Low vessel traffic density in the operational area."
            mitigation = "Standard collision avoidance procedures are sufficient."
        elif traffic_density.lower() == 'medium':
            level = RiskLevel.MEDIUM
            desc = "Medium vessel traffic density in the operational area."
            mitigation = "Maintain vigilant watch and be prepared to adjust course frequently."
        elif traffic_density.lower() == 'high':
            level = RiskLevel.HIGH
            desc = "High vessel traffic density in the operational area."
            mitigation = "Consider rescheduling mission during lower traffic periods."
        else:
            level = RiskLevel.MEDIUM
            desc = "Unknown traffic density, assuming medium risk."
            mitigation = "Maintain vigilant watch and be prepared to adjust course."
        
        return RiskFactor(
            name="Traffic Density",
            category="Collision",
            level=level,
            description=desc,
            mitigation=mitigation,
            weight=0.6
        )
    
    def _point_to_line_segment_distance(
        self,
        point: Tuple[float, float],
        line_start: Tuple[float, float],
        line_end: Tuple[float, float]
    ) -> float:
        """
        Calculate the shortest distance from a point to a line segment.
        
        Args:
            point: The point (lat, lon)
            line_start: Start of line segment (lat, lon)
            line_end: End of line segment (lat, lon)
            
        Returns:
            Distance in kilometers
        """
        # Convert to simpler variable names
        p = point
        a = line_start
        b = line_end
        
        # Calculate full distance in km
        ab_dist = calculate_distance(a[0], a[1], b[0], b[1]) / 1000
        
        # If segment is actually a point, return distance to the point
        if ab_dist < 1e-10:
            return calculate_distance(p[0], p[1], a[0], a[1]) / 1000
        
        # Calculate projection of point onto line
        # This is an approximation for small distances
        ap_dist = calculate_distance(a[0], a[1], p[0], p[1]) / 1000
        ab_bearing = math.atan2(b[1] - a[1], b[0] - a[0])
        ap_bearing = math.atan2(p[1] - a[1], p[0] - a[0])
        
        # Calculate the angle between the vectors
        angle = abs(ab_bearing - ap_bearing)
        
        # Calculate the projection length
        projection = ap_dist * math.cos(angle)
        
        # Clamp projection to segment
        projection = max(0, min(ab_dist, projection))
        
        # Calculate closest point on segment
        t = projection / ab_dist
        closest_lat = a[0] + t * (b[0] - a[0])
        closest_lon = a[1] + t * (b[1] - a[1])
        
        # Return distance to closest point in km
        return calculate_distance(p[0], p[1], closest_lat, closest_lon) / 1000
    
    def _line_segments_intersect(
        self,
        segment1: Tuple[Tuple[float, float], Tuple[float, float]],
        segment2: Tuple[Tuple[float, float], Tuple[float, float]]
    ) -> bool:
        """
        Check if two line segments intersect.
        
        Args:
            segment1: First line segment ((lat1, lon1), (lat2, lon2))
            segment2: Second line segment ((lat1, lon1), (lat2, lon2))
            
        Returns:
            True if segments intersect, False otherwise
        """
        # Extract points
        p1, p2 = segment1
        p3, p4 = segment2
        
        # Convert to simpler variable names
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        # Calculate determinants
        d1 = (x1 - x3) * (y4 - y3) - (y1 - y3) * (x4 - x3)
        d2 = (x2 - x3) * (y4 - y3) - (y2 - y3) * (x4 - x3)
        d3 = (x1 - x3) * (y2 - y1) - (y1 - y3) * (x2 - x1)
        d4 = (x4 - x3) * (y2 - y1) - (y4 - y3) * (x2 - x1)
        
        # Check for intersection
        return (d1 * d2 <= 0) and (d3 * d4 <= 0)