"""
Operational Risk Assessment for USV Mission Planner.

This module evaluates operational risks such as mission complexity,
battery/fuel requirements, and communication reliability.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from utils.logger import get_logger
from utils.geo_utils import calculate_distance, calculate_bearing
from risk_assessment.risk_analyzer import RiskFactor, RiskLevel

logger = get_logger(__name__)

class OperationalRiskAssessor:
    """
    Assesses operational risks for USV missions.
    
    Evaluates risks related to:
    - Mission duration and complexity
    - Power/fuel requirements
    - Communication reliability and range
    - Navigation accuracy
    - System redundancy
    """
    
    def __init__(self):
        """Initialize the operational risk assessor."""
        logger.info("Operational risk assessor initialized")
    
    def assess_risks(
        self, 
        mission_data: Dict[str, Any],
        environment_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskFactor]:
        """
        Assess operational risks for a mission.
        
        Args:
            mission_data: Mission configuration and waypoints
            environment_data: Environmental conditions data
            
        Returns:
            List of operational risk factors
        """
        risk_factors = []
        
        # Extract mission parameters
        waypoints = self._extract_waypoints(mission_data)
        mission_type = mission_data.get('mission_type', 'unknown')
        
        # Calculate total mission distance
        total_distance = self._calculate_mission_distance(waypoints)
        
        # Assess mission complexity
        complexity_risk = self._assess_mission_complexity(mission_type, waypoints)
        risk_factors.append(complexity_risk)
        
        # Assess power/fuel requirements
        power_risk = self._assess_power_requirements(total_distance, mission_type)
        risk_factors.append(power_risk)
        
        # Assess communication reliability
        comms_risk = self._assess_communication_reliability(waypoints, 
                                                          environment_data)
        risk_factors.append(comms_risk)
        
        # Assess navigation accuracy
        nav_risk = self._assess_navigation_accuracy(mission_type, waypoints, 
                                                  environment_data)
        risk_factors.append(nav_risk)
        
        # Assess redundancy
        redundancy_risk = self._assess_system_redundancy(mission_data)
        risk_factors.append(redundancy_risk)
        
        logger.info(f"Completed operational risk assessment with {len(risk_factors)} factors")
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
    
    def _calculate_mission_distance(self, waypoints: List[Tuple[float, float]]) -> float:
        """
        Calculate total mission distance.
        
        Args:
            waypoints: List of mission waypoints
            
        Returns:
            Total distance in meters
        """
        total_distance = 0.0
        
        for i in range(len(waypoints) - 1):
            start = waypoints[i]
            end = waypoints[i + 1]
            
            segment_distance = calculate_distance(start[0], start[1], end[0], end[1])
            total_distance += segment_distance
        
        return total_distance
    
    def _assess_mission_complexity(
        self, 
        mission_type: str, 
        waypoints: List[Tuple[float, float]]
    ) -> RiskFactor:
        """
        Assess risk based on mission complexity.
        
        Args:
            mission_type: Type of mission
            waypoints: List of mission waypoints
            
        Returns:
            Mission complexity risk factor
        """
        # Count waypoints and calculate path length
        num_waypoints = len(waypoints)
        
        # Calculate number of significant direction changes
        significant_turns = 0
        
        if num_waypoints >= 3:
            for i in range(1, num_waypoints - 1):
                prev_point = waypoints[i-1]
                curr_point = waypoints[i]
                next_point = waypoints[i+1]
                
                # Calculate bearings between segments
                bearing1 = calculate_bearing(prev_point[0], prev_point[1], 
                                            curr_point[0], curr_point[1])
                bearing2 = calculate_bearing(curr_point[0], curr_point[1], 
                                            next_point[0], next_point[1])
                
                # Calculate absolute bearing difference
                bearing_diff = abs(bearing1 - bearing2)
                if bearing_diff > 180:
                    bearing_diff = 360 - bearing_diff
                
                # Count as significant turn if bearing change is > 30 degrees
                if bearing_diff > 30:
                    significant_turns += 1
        
        # Assess complexity based on mission type, waypoints, and turns
        if mission_type == 'docking':
            # Docking is inherently complex
            complexity_level = RiskLevel.HIGH
            desc = "Docking missions involve precise positioning and control."
            mitigation = "Ensure approach vectors are clear and sensors are fully operational."
            
        elif mission_type == 'station_keeping':
            # Station keeping is moderate complexity
            complexity_level = RiskLevel.MEDIUM
            desc = "Station keeping requires maintaining position in varying conditions."
            mitigation = "Verify accurate positioning systems and redundant sensors."
            
        elif num_waypoints > 10 or significant_turns > 5:
            # Complex waypoint mission
            complexity_level = RiskLevel.HIGH
            desc = f"Complex mission with {num_waypoints} waypoints and {significant_turns} significant turns."
            mitigation = "Consider simplifying route or adding intermediate waypoints for smoother transitions."
            
        elif num_waypoints > 5 or significant_turns > 2:
            # Moderate waypoint mission
            complexity_level = RiskLevel.MEDIUM
            desc = f"Moderate mission with {num_waypoints} waypoints and {significant_turns} significant turns."
            mitigation = "Verify path planning and obstacle avoidance systems."
            
        else:
            # Simple waypoint mission
            complexity_level = RiskLevel.LOW
            desc = f"Simple mission with {num_waypoints} waypoints and {significant_turns} significant turns."
            mitigation = "Standard mission procedures are sufficient."
        
        return RiskFactor(
            name="Mission Complexity",
            category="Operational",
            level=complexity_level,
            description=desc,
            mitigation=mitigation,
            weight=0.9
        )
    
    def _assess_power_requirements(self, total_distance: float, mission_type: str) -> RiskFactor:
        """
        Assess risk based on power/fuel requirements.
        
        Args:
            total_distance: Total mission distance in meters
            mission_type: Type of mission
            
        Returns:
            Power risk factor
        """
        # Convert distance to km for display
        distance_km = total_distance / 1000.0
        
        # Base values - could be configured in real implementation
        avg_speed = 2.0  # m/s
        power_consumption_rate = 100.0  # Wh/km
        battery_capacity = 2000.0  # Wh
        
        # Adjust consumption based on mission type
        if mission_type == 'docking':
            # Docking uses more power for precision movements
            power_consumption_rate *= 1.3
        elif mission_type == 'station_keeping':
            # Station keeping involves maintaining position
            power_consumption_rate *= 1.2
            
        # Calculate estimated mission duration and power requirements
        estimated_duration_hours = total_distance / (avg_speed * 3600)
        estimated_power_usage = distance_km * power_consumption_rate
        power_margin = (battery_capacity - estimated_power_usage) / battery_capacity * 100
        
        # Assess risk based on power margin
        if power_margin < 20:
            level = RiskLevel.CRITICAL
            desc = f"Severe power constraints. Mission requires {estimated_power_usage:.1f} Wh with only {power_margin:.1f}% margin."
            mitigation = "Reduce mission scope or upgrade battery capacity."
        elif power_margin < 40:
            level = RiskLevel.HIGH
            desc = f"Limited power margin. Mission requires {estimated_power_usage:.1f} Wh with {power_margin:.1f}% margin."
            mitigation = "Optimize route for energy efficiency or include recharging point."
        elif power_margin < 60:
            level = RiskLevel.MEDIUM
            desc = f"Moderate power usage. Mission requires {estimated_power_usage:.1f} Wh with {power_margin:.1f}% margin."
            mitigation = "Monitor power levels during operation."
        else:
            level = RiskLevel.LOW
            desc = f"Sufficient power available. Mission requires {estimated_power_usage:.1f} Wh with {power_margin:.1f}% margin."
            mitigation = "Standard power management procedures are sufficient."
        
        return RiskFactor(
            name="Power Requirements",
            category="Operational",
            level=level,
            description=desc + f" Total distance: {distance_km:.2f} km, estimated duration: {estimated_duration_hours:.1f} hours.",
            mitigation=mitigation,
            weight=1.0
        )
    
    def _assess_communication_reliability(
        self, 
        waypoints: List[Tuple[float, float]],
        environment_data: Optional[Dict[str, Any]]
    ) -> RiskFactor:
        """
        Assess risk based on communication reliability.
        
        Args:
            waypoints: List of mission waypoints
            environment_data: Environmental data including comms info
            
        Returns:
            Communication risk factor
        """
        # Default values
        comms_range = 5000  # meters, typical radio range
        base_station = (37.7749, -122.4194)  # Default base station location
        has_satellite = False
        interference_level = "low"
        
        # Get comms info from environment data if available
        if environment_data and 'communications' in environment_data:
            comms_data = environment_data['communications']
            comms_range = comms_data.get('range', comms_range)
            base_station = comms_data.get('base_station', base_station)
            has_satellite = comms_data.get('satellite_available', has_satellite)
            interference_level = comms_data.get('interference', interference_level)
        
        # Calculate maximum distance from base station
        max_distance = 0
        furthest_point = None
        
        for waypoint in waypoints:
            distance = calculate_distance(waypoint[0], waypoint[1], 
                                         base_station[0], base_station[1])
            if distance > max_distance:
                max_distance = distance
                furthest_point = waypoint
        
        # Assess comms reliability based on distance and conditions
        if max_distance > comms_range and not has_satellite:
            level = RiskLevel.CRITICAL
            desc = f"Mission exceeds communication range by {max_distance - comms_range:.1f}m with no satellite backup."
            mitigation = "Add satellite communications capability or reduce mission range."
        elif max_distance > comms_range * 0.8 and not has_satellite:
            level = RiskLevel.HIGH
            desc = f"Mission approaches communication range limits with no satellite backup."
            mitigation = "Monitor communications closely and be prepared for autonomous operation."
        elif interference_level.lower() == "high":
            level = RiskLevel.HIGH
            desc = "High interference expected in the operational area."
            mitigation = "Use robust communication protocols and backup channels."
        elif interference_level.lower() == "medium" or max_distance > comms_range * 0.6:
            level = RiskLevel.MEDIUM
            desc = "Moderate communication challenges expected."
            mitigation = "Ensure regular communication checks during mission."
        else:
            level = RiskLevel.LOW
            desc = "Good communication conditions expected throughout mission."
            mitigation = "Standard communication protocols are sufficient."
        
        return RiskFactor(
            name="Communication Reliability",
            category="Operational",
            level=level,
            description=desc + f" Maximum distance from base: {max_distance:.1f}m.",
            mitigation=mitigation,
            weight=0.8
        )
    
    def _assess_navigation_accuracy(
        self, 
        mission_type: str,
        waypoints: List[Tuple[float, float]],
        environment_data: Optional[Dict[str, Any]]
    ) -> RiskFactor:
        """
        Assess risk based on navigation accuracy requirements.
        
        Args:
            mission_type: Type of mission
            waypoints: List of mission waypoints
            environment_data: Environmental data
            
        Returns:
            Navigation risk factor
        """
        # Default values
        gps_quality = "good"  # good, moderate, poor
        has_rtk = False  # Real-Time Kinematic GPS
        has_ins = False  # Inertial Navigation System
        visibility = 10.0  # km
        
        # Get navigation info from environment data if available
        if environment_data:
            gps_quality = environment_data.get('gps_quality', gps_quality)
            has_rtk = environment_data.get('rtk_available', has_rtk)
            has_ins = environment_data.get('ins_available', has_ins)
            visibility = environment_data.get('visibility', visibility)
        
        # Determine navigation accuracy requirements based on mission type
        if mission_type == 'docking':
            # Docking requires highest accuracy
            required_accuracy = 0.1  # meters
        elif mission_type == 'station_keeping':
            # Station keeping needs good accuracy
            required_accuracy = 1.0
        else:
            # Standard waypoint navigation
            required_accuracy = 3.0
        
        # Determine expected accuracy based on available systems
        if gps_quality == "good" and has_rtk:
            expected_accuracy = 0.05  # meters
        elif gps_quality == "good":
            expected_accuracy = 1.0
        elif gps_quality == "moderate" and has_ins:
            expected_accuracy = 2.0
        elif gps_quality == "moderate":
            expected_accuracy = 3.0
        elif has_ins:
            expected_accuracy = 5.0
        else:
            expected_accuracy = 10.0
        
        # Assess navigation risk based on accuracy requirements
        accuracy_ratio = expected_accuracy / required_accuracy
        
        if accuracy_ratio > 3:
            level = RiskLevel.CRITICAL
            desc = f"Navigation accuracy ({expected_accuracy:.1f}m) is insufficient for mission requirements ({required_accuracy:.1f}m)."
            mitigation = "Upgrade navigation systems or change mission type."
        elif accuracy_ratio > 2:
            level = RiskLevel.HIGH
            desc = f"Navigation accuracy ({expected_accuracy:.1f}m) is marginally adequate for requirements ({required_accuracy:.1f}m)."
            mitigation = "Add backup navigation systems or modify mission parameters."
        elif accuracy_ratio > 1:
            level = RiskLevel.MEDIUM
            desc = f"Navigation accuracy ({expected_accuracy:.1f}m) meets minimum requirements ({required_accuracy:.1f}m)."
            mitigation = "Monitor navigation performance during operation."
        else:
            level = RiskLevel.LOW
            desc = f"Navigation accuracy ({expected_accuracy:.1f}m) exceeds requirements ({required_accuracy:.1f}m)."
            mitigation = "Standard navigation procedures are sufficient."
        
        # Special case for poor visibility affecting visual navigation
        if visibility < 1.0 and (mission_type == 'docking' or mission_type == 'station_keeping'):
            # Instead of using max(), we'll use an if statement to determine the higher risk level
            if level.value < RiskLevel.HIGH.value:
                level = RiskLevel.HIGH
            desc += " Poor visibility will significantly impact visual navigation aids."
            mitigation += " Rely on non-visual navigation systems."
        
        return RiskFactor(
            name="Navigation Accuracy",
            category="Operational",
            level=level,
            description=desc,
            mitigation=mitigation,
            weight=0.9
        )
    
    def _assess_system_redundancy(self, mission_data: Dict[str, Any]) -> RiskFactor:
        """
        Assess risk based on system redundancy.
        
        Args:
            mission_data: Mission configuration data
            
        Returns:
            System redundancy risk factor
        """
        # Extract redundancy information
        redundancy_info = mission_data.get('system_redundancy', {})
        
        # Default values
        has_redundant_power = redundancy_info.get('power', False)
        has_redundant_propulsion = redundancy_info.get('propulsion', False)
        has_redundant_navigation = redundancy_info.get('navigation', False)
        has_redundant_communication = redundancy_info.get('communication', False)
        has_fallback_control = redundancy_info.get('control', False)
        
        # Count redundant systems
        redundant_count = sum([
            has_redundant_power,
            has_redundant_propulsion,
            has_redundant_navigation,
            has_redundant_communication,
            has_fallback_control
        ])
        
        # Assess risk based on number of redundant systems
        if redundant_count == 0:
            level = RiskLevel.CRITICAL
            desc = "No redundant systems available. Single point failures could compromise mission."
            mitigation = "Add redundancy for critical systems before mission."
        elif redundant_count < 2:
            level = RiskLevel.HIGH
            desc = "Limited system redundancy available."
            mitigation = "Add redundancy for navigation and propulsion systems."
        elif redundant_count < 4:
            level = RiskLevel.MEDIUM
            desc = "Moderate system redundancy available."
            mitigation = "Consider adding redundancy for remaining critical systems."
        else:
            level = RiskLevel.LOW
            desc = "Good system redundancy available."
            mitigation = "Standard system monitoring procedures are sufficient."
        
        # Build detailed description
        detail = "\nRedundant systems: "
        if has_redundant_power:
            detail += "Power, "
        if has_redundant_propulsion:
            detail += "Propulsion, "
        if has_redundant_navigation:
            detail += "Navigation, "
        if has_redundant_communication:
            detail += "Communication, "
        if has_fallback_control:
            detail += "Control, "
        
        if redundant_count > 0:
            detail = detail[:-2]  # Remove trailing comma and space
        else:
            detail += "None"
        
        return RiskFactor(
            name="System Redundancy",
            category="Operational",
            level=level,
            description=desc + detail,
            mitigation=mitigation,
            weight=0.8
        )