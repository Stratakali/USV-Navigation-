"""
Helper module for risk assessment in the web interface.

This module provides functions to interact with the risk assessment
modules of the USV Mission Planner system.
"""

import os
import sys
import json
from typing import Dict, List, Any, Tuple

# Helper function to create a mission configuration
def create_mission_config(mission_type: str, mission_data: Dict) -> Dict[str, Any]:
    """
    Create a mission configuration for risk assessment.
    
    Args:
        mission_type: Type of mission (waypoint, station_keeping, docking)
        mission_data: Mission data from the web interface
        
    Returns:
        Dict containing mission configuration
    """
    # Base mission configuration
    mission_config = {
        'mission_type': mission_type,
        'system_redundancy': {
            'power': True,
            'propulsion': True,
            'navigation': True,
            'communication': True,
            'control': True
        },
        'mission_duration': 60  # Default to 60 minutes
    }
    
    # Handle specific mission types
    if mission_type == 'waypoint':
        # Extract waypoints
        waypoints = [(wp['lat'], wp['lng']) for wp in mission_data['waypoints']]
        mission_config['waypoints'] = waypoints
        mission_config['mission_duration'] = len(waypoints) * 15  # Estimate 15 min per waypoint
        
    elif mission_type == 'station_keeping':
        location = mission_data['location']
        mission_config['station_position'] = (location['lat'], location['lng'])
        mission_config['station_radius'] = 20.0  # meters
        mission_config['station_duration'] = mission_data.get('duration', 300)  # seconds
        mission_config['mission_duration'] = mission_data.get('duration', 300) / 60  # minutes
        
    elif mission_type == 'docking':
        location = mission_data['location']
        mission_config['docking_position'] = (location['lat'], location['lng'])
        mission_config['docking_heading'] = mission_data.get('heading', 0.0)  # degrees
        mission_config['approach_distance'] = 50.0  # meters
        mission_config['mission_duration'] = 30  # Estimate 30 min for docking
    
    return mission_config

# Helper function to create an environment configuration
def create_environment_config(env_condition: str = 'good') -> Dict[str, Any]:
    """
    Create an environment configuration for risk assessment.
    
    Args:
        env_condition: Environmental conditions (good, moderate, poor)
        
    Returns:
        Dict containing environment configuration
    """
    if env_condition == 'good':
        return {
            'wind_speed': 3.0,  # m/s
            'wave_height': 0.5,  # meters
            'current_speed': 0.2,  # m/s
            'visibility': 10.0,  # km
            'is_daytime': True,
            'precipitation': 0.0,  # mm/hour
            'gps_quality': 'good',
            'rtk_available': True,
            'ins_available': True,
            'communications': {
                'range': 10000,  # meters
                'base_station': (37.7749, -122.4194),
                'satellite_available': True,
                'interference': 'low'
            }
        }
    
    elif env_condition == 'moderate':
        return {
            'wind_speed': 8.0,  # m/s
            'wave_height': 1.2,  # meters
            'current_speed': 0.5,  # m/s
            'visibility': 5.0,  # km
            'is_daytime': True,
            'precipitation': 2.0,  # mm/hour
            'gps_quality': 'moderate',
            'rtk_available': False,
            'ins_available': True,
            'communications': {
                'range': 5000,  # meters
                'base_station': (37.7749, -122.4194),
                'satellite_available': True,
                'interference': 'medium'
            }
        }
    
    else:  # poor
        return {
            'wind_speed': 15.0,  # m/s
            'wave_height': 2.5,  # meters
            'current_speed': 1.2,  # m/s
            'visibility': 0.5,  # km
            'is_daytime': False,
            'precipitation': 10.0,  # mm/hour
            'gps_quality': 'poor',
            'rtk_available': False,
            'ins_available': False,
            'communications': {
                'range': 2000,  # meters
                'base_station': (37.7749, -122.4194),
                'satellite_available': False,
                'interference': 'high'
            }
        }

# Function to serialize risk assessment results for JSON
def serialize_risk_factor(risk_factor):
    """Convert risk factor to a serializable dict."""
    return {
        'name': risk_factor.name,
        'description': risk_factor.description,
        'level': risk_factor.level.name,
        'level_value': risk_factor.level.value,
        'mitigation': risk_factor.mitigation
    }

# Function to assess operational risks for a mission
def assess_mission_risks(mission_type, mission_data, env_condition):
    """
    Assess operational risks for a mission.
    
    Args:
        mission_type: Type of mission
        mission_data: Mission data from the web interface
        env_condition: Environmental condition
        
    Returns:
        Dict containing risk assessment results
    """
    # Add USV mission planner to the Python path
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'usv_mission_planner'))
    
    # Import risk assessment module
    from usv_mission_planner.risk_assessment.operational_risks import OperationalRiskAssessor
    from usv_mission_planner.risk_assessment.risk_analyzer import RiskLevel
    
    # Create mission and environment configurations
    mission_config = create_mission_config(mission_type, mission_data)
    env_config = create_environment_config(env_condition)
    
    # Create operational risk assessor
    assessor = OperationalRiskAssessor()
    
    # Assess operational risks
    risk_factors = assessor.assess_risks(mission_config, env_config)
    
    # Count risks by level
    level_counts = {
        'LOW': 0,
        'MEDIUM': 0,
        'HIGH': 0,
        'CRITICAL': 0
    }
    
    for risk in risk_factors:
        level_counts[risk.level.name] += 1
    
    # Serialize risk factors for JSON
    serialized_factors = [serialize_risk_factor(risk) for risk in risk_factors]
    
    # Prepare result
    result = {
        'mission_type': mission_type,
        'env_condition': env_condition,
        'risk_summary': level_counts,
        'risk_factors': serialized_factors,
        'overall_risk_level': calculate_overall_risk_level(level_counts)
    }
    
    return result

def calculate_overall_risk_level(level_counts):
    """
    Calculate overall risk level based on counts of risk factors at each level.
    
    Args:
        level_counts: Dict with counts of risks at each level
        
    Returns:
        String indicating overall risk level
    """
    if level_counts['CRITICAL'] > 0:
        return 'CRITICAL'
    elif level_counts['HIGH'] > 0:
        return 'HIGH'
    elif level_counts['MEDIUM'] > 0:
        return 'MEDIUM'
    else:
        return 'LOW'