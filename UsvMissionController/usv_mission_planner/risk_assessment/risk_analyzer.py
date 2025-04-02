"""
Risk Analyzer module for USV Mission Planner.

This module provides core risk assessment functionality for analyzing
and evaluating mission risks across different categories.
"""

import enum
from typing import Dict, List, Tuple, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class RiskLevel(enum.Enum):
    """Risk severity levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    def get_color(self):
        """Get color code for risk level visualization."""
        colors = {
            RiskLevel.LOW: "#28a745",      # Green
            RiskLevel.MEDIUM: "#ffc107",   # Yellow/Amber
            RiskLevel.HIGH: "#fd7e14",     # Orange
            RiskLevel.CRITICAL: "#dc3545", # Red
        }
        return colors.get(self, "#6c757d")  # Default gray

class RiskFactor:
    """
    Represents a specific risk factor that can affect mission safety.
    
    Attributes:
        name: Name of the risk factor
        category: Category of risk (environmental, collision, operational)
        level: Current risk level
        description: Detailed description of the risk
        mitigation: Suggested mitigation measures
        weight: Weight of this risk in overall calculation (0.0-1.0)
    """
    
    def __init__(
        self,
        name: str,
        category: str,
        level: RiskLevel = RiskLevel.LOW,
        description: str = "",
        mitigation: str = "",
        weight: float = 1.0
    ):
        """
        Initialize a risk factor.
        
        Args:
            name: Name of the risk factor
            category: Category of risk
            level: Current risk level
            description: Detailed description of the risk
            mitigation: Suggested mitigation measures
            weight: Weight of this risk in overall calculation (0.0-1.0)
        """
        self.name = name
        self.category = category
        self.level = level
        self.description = description
        self.mitigation = mitigation
        self.weight = max(0.0, min(1.0, weight))  # Clamp between 0 and 1
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert risk factor to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the risk factor
        """
        return {
            "name": self.name,
            "category": self.category,
            "level": self.level.name,
            "level_value": self.level.value,
            "description": self.description,
            "mitigation": self.mitigation,
            "weight": self.weight,
            "color": self.level.get_color()
        }

class RiskAnalyzer:
    """
    Main risk analyzer that aggregates different risk assessors and calculates
    overall mission risk.
    
    Attributes:
        risk_factors: List of risk factors affecting the mission
        risk_assessors: List of specialized risk assessors
    """
    
    def __init__(self):
        """Initialize the risk analyzer."""
        self.risk_factors: List[RiskFactor] = []
        self.risk_assessors = []
        logger.info("Risk analyzer initialized")
    
    def add_risk_assessor(self, assessor: Any) -> None:
        """
        Add a specialized risk assessor.
        
        Args:
            assessor: Risk assessor object that provides risk factors
        """
        self.risk_assessors.append(assessor)
        logger.info(f"Added risk assessor: {assessor.__class__.__name__}")
    
    def assess_mission_risks(
        self,
        mission_data: Dict[str, Any],
        environment_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform a comprehensive risk assessment for a mission.
        
        Args:
            mission_data: Mission configuration and waypoints
            environment_data: Environmental conditions data
            
        Returns:
            Dictionary containing risk assessment results
        """
        # Reset risk factors
        self.risk_factors = []
        
        # Collect risk factors from all assessors
        for assessor in self.risk_assessors:
            risk_factors = assessor.assess_risks(mission_data, environment_data)
            self.risk_factors.extend(risk_factors)
        
        # Calculate overall risk metrics
        results = self._calculate_risk_metrics()
        
        logger.info(f"Completed risk assessment with {len(self.risk_factors)} factors. " +
                   f"Overall risk level: {results['overall_risk_level']}")
        
        return results
    
    def _calculate_risk_metrics(self) -> Dict[str, Any]:
        """
        Calculate overall risk metrics from individual risk factors.
        
        Returns:
            Dictionary containing risk metrics and summary
        """
        if not self.risk_factors:
            return {
                "overall_risk_level": RiskLevel.LOW.name,
                "overall_risk_value": RiskLevel.LOW.value,
                "overall_risk_color": RiskLevel.LOW.get_color(),
                "risk_factors": [],
                "category_risks": {},
                "risk_summary": "No risk factors identified."
            }
        
        # Count risks by level and calculate weighted average
        level_counts = {level: 0 for level in RiskLevel}
        category_risks = {}
        total_weight = 0.0
        weighted_sum = 0.0
        
        for factor in self.risk_factors:
            level_counts[factor.level] += 1
            
            # Track risk by category
            if factor.category not in category_risks:
                category_risks[factor.category] = {
                    "count": 0,
                    "weighted_sum": 0.0,
                    "total_weight": 0.0,
                    "factors": []
                }
            
            category_risks[factor.category]["count"] += 1
            category_risks[factor.category]["weighted_sum"] += factor.level.value * factor.weight
            category_risks[factor.category]["total_weight"] += factor.weight
            category_risks[factor.category]["factors"].append(factor.to_dict())
            
            # Overall weighted calculation
            weighted_sum += factor.level.value * factor.weight
            total_weight += factor.weight
        
        # Calculate overall risk level
        if total_weight > 0:
            average_risk = weighted_sum / total_weight
        else:
            average_risk = 1.0  # Default to LOW if no weights
        
        # Determine overall risk level based on average and presence of CRITICAL risks
        if level_counts[RiskLevel.CRITICAL] > 0:
            overall_risk = RiskLevel.CRITICAL
        elif average_risk >= 3.5:
            overall_risk = RiskLevel.CRITICAL
        elif average_risk >= 2.5:
            overall_risk = RiskLevel.HIGH
        elif average_risk >= 1.5:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        # Calculate category risk levels
        for category in category_risks:
            cat_data = category_risks[category]
            if cat_data["total_weight"] > 0:
                cat_avg = cat_data["weighted_sum"] / cat_data["total_weight"]
                
                if cat_avg >= 3.5:
                    cat_risk = RiskLevel.CRITICAL
                elif cat_avg >= 2.5:
                    cat_risk = RiskLevel.HIGH
                elif cat_avg >= 1.5:
                    cat_risk = RiskLevel.MEDIUM
                else:
                    cat_risk = RiskLevel.LOW
                    
                cat_data["risk_level"] = cat_risk.name
                cat_data["risk_value"] = cat_risk.value
                cat_data["risk_color"] = cat_risk.get_color()
        
        # Generate risk summary
        risk_summary = self._generate_risk_summary(level_counts, overall_risk)
        
        return {
            "overall_risk_level": overall_risk.name,
            "overall_risk_value": overall_risk.value,
            "overall_risk_color": overall_risk.get_color(),
            "risk_factors": [factor.to_dict() for factor in self.risk_factors],
            "category_risks": category_risks,
            "level_counts": {level.name: count for level, count in level_counts.items()},
            "risk_summary": risk_summary
        }
    
    def _generate_risk_summary(self, level_counts: Dict[RiskLevel, int], overall_risk: RiskLevel) -> str:
        """
        Generate a human-readable risk summary.
        
        Args:
            level_counts: Count of risks by level
            overall_risk: Overall assessed risk level
            
        Returns:
            String containing risk summary
        """
        total_factors = sum(level_counts.values())
        critical_count = level_counts[RiskLevel.CRITICAL]
        high_count = level_counts[RiskLevel.HIGH]
        
        if overall_risk == RiskLevel.CRITICAL:
            return (f"CRITICAL RISK ASSESSMENT: This mission has {critical_count} critical risk factors "
                   f"out of {total_factors} total factors. Mission execution is NOT recommended "
                   f"without addressing critical risks.")
        
        elif overall_risk == RiskLevel.HIGH:
            return (f"HIGH RISK ASSESSMENT: This mission has {high_count} high risk factors "
                   f"out of {total_factors} total factors. Consider implementing recommended "
                   f"mitigation measures before proceeding.")
        
        elif overall_risk == RiskLevel.MEDIUM:
            return (f"MEDIUM RISK ASSESSMENT: This mission has moderate risk. "
                   f"Review identified risk factors and consider mitigation measures.")
        
        else:
            return (f"LOW RISK ASSESSMENT: This mission has minimal risk factors. "
                   f"Standard safety protocols are sufficient.")