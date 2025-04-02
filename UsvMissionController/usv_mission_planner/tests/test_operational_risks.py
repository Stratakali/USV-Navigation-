"""
Test script for the Operational Risk Assessor.

This module tests the operational risk assessment functionality.
"""

import unittest
from risk_assessment.operational_risks import OperationalRiskAssessor
from risk_assessment.risk_analyzer import RiskLevel


class TestOperationalRisks(unittest.TestCase):
    """Test case for operational risk assessment."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.assessor = OperationalRiskAssessor()
        
        # Sample mission data for testing
        self.simple_mission = {
            'mission_type': 'waypoint',
            'waypoints': [
                (37.7749, -122.4194),  # San Francisco
                (37.8045, -122.4159),  # Golden Gate Bridge
                (37.8265, -122.3806),  # Alcatraz
            ],
            'system_redundancy': {
                'power': True,
                'propulsion': True,
                'navigation': False,
                'communication': False,
                'control': False
            }
        }
        
        self.complex_mission = {
            'mission_type': 'waypoint',
            'waypoints': [
                (37.7749, -122.4194),  # San Francisco
                (37.8045, -122.4159),  # Golden Gate Bridge
                (37.8265, -122.3806),  # Alcatraz
                (37.8155, -122.3440),  # Berkeley
                (37.7955, -122.3828),  # Bay Area
                (37.7749, -122.4194),  # Return to San Francisco
                (37.7845, -122.4159),  # Additional waypoint 1
                (37.7865, -122.3806),  # Additional waypoint 2
                (37.7755, -122.3440),  # Additional waypoint 3
                (37.7655, -122.3828),  # Additional waypoint 4
                (37.7549, -122.4294),  # Additional waypoint 5
                (37.7749, -122.4194),  # Final return to San Francisco
            ],
            'system_redundancy': {
                'power': False,
                'propulsion': False,
                'navigation': False,
                'communication': False,
                'control': False
            }
        }
        
        self.docking_mission = {
            'mission_type': 'docking',
            'waypoints': [
                (37.7749, -122.4194),  # Start
                (37.7755, -122.4190),  # Approach
                (37.7760, -122.4185),  # Dock
            ],
            'docking_position': (37.7760, -122.4185),
            'docking_heading': 90.0,
            'system_redundancy': {
                'power': True,
                'propulsion': True,
                'navigation': True,
                'communication': True,
                'control': True
            }
        }
        
        # Sample environment data for testing
        self.good_environment = {
            'gps_quality': 'good',
            'rtk_available': True,
            'ins_available': True,
            'visibility': 10.0,
            'communications': {
                'range': 10000,
                'satellite_available': True,
                'interference': 'low'
            }
        }
        
        self.poor_environment = {
            'gps_quality': 'poor',
            'rtk_available': False,
            'ins_available': False,
            'visibility': 0.5,
            'communications': {
                'range': 3000,
                'satellite_available': False,
                'interference': 'high'
            }
        }
    
    def test_simple_mission_good_environment(self):
        """Test risk assessment for a simple mission in good environment."""
        risks = self.assessor.assess_risks(self.simple_mission, self.good_environment)
        
        # Should have 5 risk factors
        self.assertEqual(len(risks), 5)
        
        # Check risk levels
        risk_levels = [risk.level for risk in risks]
        
        # In good environment with simple mission, most risks should be low or medium
        self.assertIn(RiskLevel.LOW, risk_levels)
        
        # Count risk levels
        low_count = sum(1 for level in risk_levels if level == RiskLevel.LOW)
        medium_count = sum(1 for level in risk_levels if level == RiskLevel.MEDIUM)
        high_count = sum(1 for level in risk_levels if level == RiskLevel.HIGH)
        critical_count = sum(1 for level in risk_levels if level == RiskLevel.CRITICAL)
        
        # Simple mission in good conditions should have more low/medium risks than high/critical
        self.assertGreaterEqual(low_count + medium_count, high_count + critical_count)
    
    def test_complex_mission_poor_environment(self):
        """Test risk assessment for a complex mission in poor environment."""
        risks = self.assessor.assess_risks(self.complex_mission, self.poor_environment)
        
        # Should have 5 risk factors
        self.assertEqual(len(risks), 5)
        
        # Check risk levels
        risk_levels = [risk.level for risk in risks]
        
        # In poor environment with complex mission, most risks should be high or critical
        self.assertIn(RiskLevel.HIGH, risk_levels)
        self.assertIn(RiskLevel.CRITICAL, risk_levels)
        
        # Count risk levels
        low_count = sum(1 for level in risk_levels if level == RiskLevel.LOW)
        medium_count = sum(1 for level in risk_levels if level == RiskLevel.MEDIUM)
        high_count = sum(1 for level in risk_levels if level == RiskLevel.HIGH)
        critical_count = sum(1 for level in risk_levels if level == RiskLevel.CRITICAL)
        
        # Complex mission in poor conditions should have more high/critical risks than low/medium
        self.assertGreaterEqual(high_count + critical_count, low_count + medium_count)
    
    def test_docking_mission(self):
        """Test risk assessment for a docking mission."""
        risks = self.assessor.assess_risks(self.docking_mission, self.good_environment)
        
        # Should have 5 risk factors
        self.assertEqual(len(risks), 5)
        
        # Find mission complexity risk factor
        complexity_risk = next((risk for risk in risks if risk.name == "Mission Complexity"), None)
        
        # Docking missions should have high complexity risk
        self.assertIsNotNone(complexity_risk)
        self.assertEqual(complexity_risk.level, RiskLevel.HIGH)
    
    def test_power_requirements(self):
        """Test power requirements risk calculation."""
        # Create a mission with a very long distance to test power risk
        long_mission = {
            'mission_type': 'waypoint',
            'waypoints': [
                (37.7749, -122.4194),  # San Francisco
                (38.7749, -121.4194),  # Far away point (approx 100km)
            ]
        }
        
        risks = self.assessor.assess_risks(long_mission, self.good_environment)
        
        # Find power requirements risk factor
        power_risk = next((risk for risk in risks if risk.name == "Power Requirements"), None)
        
        # Long distance should result in high or critical power risk
        self.assertIsNotNone(power_risk)
        self.assertIn(power_risk.level, [RiskLevel.HIGH, RiskLevel.CRITICAL])
    
    def test_communication_reliability(self):
        """Test communication reliability risk calculation."""
        # Create a mission with points far beyond communication range
        far_mission = {
            'mission_type': 'waypoint',
            'waypoints': [
                (37.7749, -122.4194),  # San Francisco
                (40.7128, -74.0060),   # New York (far beyond comm range)
            ]
        }
        
        # Use environment with limited comm range and no satellite
        limited_comms_env = {
            'communications': {
                'range': 5000,
                'satellite_available': False,
                'interference': 'low'
            }
        }
        
        risks = self.assessor.assess_risks(far_mission, limited_comms_env)
        
        # Find communication reliability risk factor
        comms_risk = next((risk for risk in risks if risk.name == "Communication Reliability"), None)
        
        # Distance beyond comm range with no satellite should be critical
        self.assertIsNotNone(comms_risk)
        self.assertEqual(comms_risk.level, RiskLevel.CRITICAL)
    
    def test_system_redundancy(self):
        """Test system redundancy risk calculation."""
        # Create missions with different redundancy profiles
        no_redundancy = {
            'mission_type': 'waypoint',
            'waypoints': [(37.7749, -122.4194)],
            'system_redundancy': {
                'power': False,
                'propulsion': False,
                'navigation': False,
                'communication': False,
                'control': False
            }
        }
        
        full_redundancy = {
            'mission_type': 'waypoint',
            'waypoints': [(37.7749, -122.4194)],
            'system_redundancy': {
                'power': True,
                'propulsion': True,
                'navigation': True,
                'communication': True,
                'control': True
            }
        }
        
        # Assess risks for both missions
        no_redundancy_risks = self.assessor.assess_risks(no_redundancy, self.good_environment)
        full_redundancy_risks = self.assessor.assess_risks(full_redundancy, self.good_environment)
        
        # Find redundancy risk factors
        no_redundancy_risk = next((risk for risk in no_redundancy_risks if risk.name == "System Redundancy"), None)
        full_redundancy_risk = next((risk for risk in full_redundancy_risks if risk.name == "System Redundancy"), None)
        
        # No redundancy should be critical, full redundancy should be low
        self.assertIsNotNone(no_redundancy_risk)
        self.assertIsNotNone(full_redundancy_risk)
        self.assertEqual(no_redundancy_risk.level, RiskLevel.CRITICAL)
        self.assertEqual(full_redundancy_risk.level, RiskLevel.LOW)


if __name__ == '__main__':
    unittest.main()