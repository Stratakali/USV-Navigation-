"""
Demonstration of the risk assessment module in action.

This script demonstrates how to use the risk assessment framework
to evaluate mission safety for various scenarios.
"""

import json
from risk_assessment.risk_analyzer import RiskAnalyzer
from risk_assessment.environmental_risks import EnvironmentalRiskAssessor
from risk_assessment.collision_risks import CollisionRiskAssessor
from risk_assessment.operational_risks import OperationalRiskAssessor


def create_sample_mission(mission_type='waypoint', complexity='simple'):
    """
    Create a sample mission configuration.
    
    Args:
        mission_type: Type of mission (waypoint, station_keeping, docking)
        complexity: Mission complexity (simple, moderate, complex)
        
    Returns:
        Dict containing mission configuration
    """
    # Base mission in San Francisco Bay
    if complexity == 'simple':
        waypoints = [
            (37.7749, -122.4194),  # San Francisco
            (37.8045, -122.4159),  # Golden Gate Bridge
            (37.7749, -122.4194),  # Back to San Francisco
        ]
    elif complexity == 'moderate':
        waypoints = [
            (37.7749, -122.4194),  # San Francisco
            (37.8045, -122.4159),  # Golden Gate Bridge
            (37.8265, -122.3806),  # Alcatraz
            (37.8155, -122.3440),  # Berkeley
            (37.7955, -122.3828),  # Bay Area
            (37.7749, -122.4194),  # Back to San Francisco
        ]
    else:  # complex
        waypoints = [
            (37.7749, -122.4194),  # San Francisco
            (37.8045, -122.4159),  # Golden Gate Bridge
            (37.8265, -122.3806),  # Alcatraz
            (37.8155, -122.3440),  # Berkeley
            (37.7955, -122.3828),  # Bay Area
            (37.7949, -122.3994),  # Treasure Island
            (37.8083, -122.4156),  # Fort Mason
            (37.8273, -122.4230),  # Marina District
            (37.8545, -122.4255),  # Sausalito
            (37.8719, -122.3656),  # Tiburon
            (37.7749, -122.4194),  # Back to San Francisco
        ]
    
    # System redundancy based on mission complexity
    if complexity == 'simple':
        redundancy = {
            'power': True,
            'propulsion': True,
            'navigation': True,
            'communication': True,
            'control': True
        }
    elif complexity == 'moderate':
        redundancy = {
            'power': True,
            'propulsion': True,
            'navigation': False,
            'communication': True,
            'control': False
        }
    else:  # complex
        redundancy = {
            'power': False,
            'propulsion': False,
            'navigation': False,
            'communication': False,
            'control': False
        }
    
    # Create mission configuration
    mission = {
        'mission_type': mission_type,
        'waypoints': waypoints,
        'system_redundancy': redundancy,
        'mission_duration': len(waypoints) * 30,  # Estimated minutes
    }
    
    # Add mission-specific parameters
    if mission_type == 'station_keeping':
        mission['station_position'] = waypoints[0]
        mission['station_radius'] = 20.0  # meters
        mission['station_duration'] = 3600  # seconds
    
    elif mission_type == 'docking':
        mission['docking_position'] = waypoints[-1]
        mission['docking_heading'] = 90.0  # degrees
        mission['approach_distance'] = 50.0  # meters
    
    return mission


def create_sample_environment(conditions='good'):
    """
    Create a sample environment configuration.
    
    Args:
        conditions: Environmental conditions (good, moderate, poor)
        
    Returns:
        Dict containing environment configuration
    """
    if conditions == 'good':
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
            'obstacles': [
                (37.8250, -122.4100, 50.0),  # (lat, lon, radius in meters)
            ],
            'shipping_lanes': [
                {
                    'name': 'Main Channel',
                    'coordinates': [
                        (37.8045, -122.4159),
                        (37.8155, -122.3940)
                    ],
                    'width': 200.0  # meters
                }
            ],
            'communications': {
                'range': 10000,  # meters
                'base_station': (37.7749, -122.4194),
                'satellite_available': True,
                'interference': 'low'
            }
        }
    
    elif conditions == 'moderate':
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
            'obstacles': [
                (37.8250, -122.4100, 50.0),
                (37.8155, -122.3940, 75.0),
                (37.7955, -122.3950, 100.0)
            ],
            'shipping_lanes': [
                {
                    'name': 'Main Channel',
                    'coordinates': [
                        (37.8045, -122.4159),
                        (37.8155, -122.3940)
                    ],
                    'width': 200.0  # meters
                }
            ],
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
            'obstacles': [
                (37.8250, -122.4100, 50.0),
                (37.8155, -122.3940, 75.0),
                (37.7955, -122.3950, 100.0),
                (37.8045, -122.4050, 150.0),
                (37.7855, -122.4150, 200.0)
            ],
            'shipping_lanes': [
                {
                    'name': 'Main Channel',
                    'coordinates': [
                        (37.8045, -122.4159),
                        (37.8155, -122.3940)
                    ],
                    'width': 200.0  # meters
                },
                {
                    'name': 'Ferry Route',
                    'coordinates': [
                        (37.7749, -122.4194),
                        (37.8155, -122.3440)
                    ],
                    'width': 150.0  # meters
                }
            ],
            'communications': {
                'range': 2000,  # meters
                'base_station': (37.7749, -122.4194),
                'satellite_available': False,
                'interference': 'high'
            }
        }


def print_risk_summary(results, mission_type, complexity, conditions):
    """
    Print a summary of risk assessment results.
    
    Args:
        results: Risk assessment results from RiskAnalyzer
        mission_type: Type of mission
        complexity: Mission complexity
        conditions: Environmental conditions
    """
    print(f"\n{'=' * 80}")
    print(f"RISK ASSESSMENT: {mission_type.upper()} mission ({complexity}) in {conditions} conditions")
    print(f"{'=' * 80}")
    
    print(f"\nOverall Risk: {results['overall_risk_level']} ({results['overall_risk_value']})")
    print(f"\n{results['risk_summary']}")
    
    print(f"\nRisk Factors by Level:")
    for level, count in results['level_counts'].items():
        if count > 0:
            print(f"  {level}: {count}")
    
    print(f"\nRisk Factors by Category:")
    for category, data in results['category_risks'].items():
        print(f"  {category}: {data['risk_level']} ({data['count']} factors)")
    
    print(f"\nTop Risk Factors (Critical and High):")
    critical_high_risks = [r for r in results['risk_factors'] 
                         if r['level'] in ('CRITICAL', 'HIGH')]
    
    if critical_high_risks:
        for risk in critical_high_risks:
            print(f"  - {risk['name']} ({risk['level']}):")
            print(f"    {risk['description']}")
            print(f"    Mitigation: {risk['mitigation']}")
    else:
        print("  No critical or high risks identified.")
    
    print(f"\n{'-' * 80}\n")


def run_risk_assessments():
    """Run risk assessments for various mission scenarios."""
    # Create risk analyzer with assessors
    analyzer = RiskAnalyzer()
    analyzer.add_risk_assessor(EnvironmentalRiskAssessor())
    analyzer.add_risk_assessor(CollisionRiskAssessor())
    analyzer.add_risk_assessor(OperationalRiskAssessor())
    
    # Scenarios to test
    scenarios = [
        # (mission_type, complexity, conditions)
        ('waypoint', 'simple', 'good'),
        ('waypoint', 'complex', 'poor'),
        ('station_keeping', 'moderate', 'moderate'),
        ('docking', 'simple', 'good'),
        ('docking', 'simple', 'poor')
    ]
    
    # Run assessments for each scenario
    for mission_type, complexity, conditions in scenarios:
        mission = create_sample_mission(mission_type, complexity)
        environment = create_sample_environment(conditions)
        
        # Assess risks
        results = analyzer.assess_mission_risks(mission, environment)
        
        # Print results summary
        print_risk_summary(results, mission_type, complexity, conditions)
        
    print("Risk assessment demonstration complete.")


if __name__ == '__main__':
    run_risk_assessments()