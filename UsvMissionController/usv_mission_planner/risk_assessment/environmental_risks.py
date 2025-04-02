"""
Environmental Risk Assessment for USV Mission Planner.

This module evaluates environmental risks such as weather conditions,
water currents, and tide levels that may impact mission safety.
"""

from typing import Dict, List, Any, Optional, Tuple
from utils.logger import get_logger
from risk_assessment.risk_analyzer import RiskFactor, RiskLevel

logger = get_logger(__name__)

class EnvironmentalRiskAssessor:
    """
    Assesses environmental risks for USV missions.
    
    Evaluates risks related to:
    - Weather conditions (wind, precipitation, visibility)
    - Water conditions (waves, currents)
    - Tidal conditions
    - Time of day (daylight vs night operations)
    """
    
    def __init__(self):
        """Initialize the environmental risk assessor."""
        logger.info("Environmental risk assessor initialized")
    
    def assess_risks(
        self, 
        mission_data: Dict[str, Any],
        environment_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskFactor]:
        """
        Assess environmental risks for a mission.
        
        Args:
            mission_data: Mission configuration and waypoints
            environment_data: Environmental conditions data
            
        Returns:
            List of environmental risk factors
        """
        risk_factors = []
        
        # Use provided environmental data or default to safe conditions
        env_data = environment_data or {}
        
        # Assess wind conditions
        wind_speed = env_data.get('wind_speed', 5.0)  # m/s
        wind_risk = self._assess_wind_risk(wind_speed)
        risk_factors.append(wind_risk)
        
        # Assess wave conditions
        wave_height = env_data.get('wave_height', 0.5)  # meters
        wave_risk = self._assess_wave_risk(wave_height)
        risk_factors.append(wave_risk)
        
        # Assess visibility conditions
        visibility = env_data.get('visibility', 10.0)  # kilometers
        visibility_risk = self._assess_visibility_risk(visibility)
        risk_factors.append(visibility_risk)
        
        # Assess current speed
        current_speed = env_data.get('current_speed', 0.5)  # m/s
        current_risk = self._assess_current_risk(current_speed)
        risk_factors.append(current_risk)
        
        # Assess time of day
        is_daytime = env_data.get('is_daytime', True)
        time_risk = self._assess_time_of_day_risk(is_daytime)
        risk_factors.append(time_risk)
        
        # Assess precipitation
        precipitation = env_data.get('precipitation', 0.0)  # mm/hour
        precip_risk = self._assess_precipitation_risk(precipitation)
        risk_factors.append(precip_risk)
        
        logger.info(f"Completed environmental risk assessment with {len(risk_factors)} factors")
        return risk_factors
    
    def _assess_wind_risk(self, wind_speed: float) -> RiskFactor:
        """
        Assess risk based on wind speed.
        
        Args:
            wind_speed: Wind speed in m/s
            
        Returns:
            Wind risk factor
        """
        if wind_speed < 5.0:
            level = RiskLevel.LOW
            desc = "Light winds, minimal impact on vessel operations."
            mitigation = "No specific mitigation required."
        elif wind_speed < 10.0:
            level = RiskLevel.MEDIUM
            desc = "Moderate winds may affect vessel control."
            mitigation = "Adjust course to minimize crosswind exposure."
        elif wind_speed < 15.0:
            level = RiskLevel.HIGH
            desc = "Strong winds will significantly affect vessel control and mission duration."
            mitigation = "Consider postponing mission or limiting operational area."
        else:
            level = RiskLevel.CRITICAL
            desc = "Severe winds make safe operation extremely difficult."
            mitigation = "Mission should be postponed until winds decrease."
        
        return RiskFactor(
            name="Wind Conditions",
            category="Environmental",
            level=level,
            description=desc + f" Current wind speed: {wind_speed:.1f} m/s.",
            mitigation=mitigation,
            weight=0.9
        )
    
    def _assess_wave_risk(self, wave_height: float) -> RiskFactor:
        """
        Assess risk based on wave height.
        
        Args:
            wave_height: Wave height in meters
            
        Returns:
            Wave risk factor
        """
        if wave_height < 0.5:
            level = RiskLevel.LOW
            desc = "Calm water conditions."
            mitigation = "No specific mitigation required."
        elif wave_height < 1.0:
            level = RiskLevel.MEDIUM
            desc = "Moderate waves may affect sensor readings and stability."
            mitigation = "Adjust mission parameters for increased stability requirements."
        elif wave_height < 2.0:
            level = RiskLevel.HIGH
            desc = "Rough water conditions will significantly impact operations."
            mitigation = "Consider postponing mission or limiting operational area."
        else:
            level = RiskLevel.CRITICAL
            desc = "Severe wave conditions make safe operation hazardous."
            mitigation = "Mission should be postponed until water conditions improve."
        
        return RiskFactor(
            name="Wave Conditions",
            category="Environmental",
            level=level,
            description=desc + f" Current wave height: {wave_height:.1f} meters.",
            mitigation=mitigation,
            weight=0.8
        )
    
    def _assess_visibility_risk(self, visibility: float) -> RiskFactor:
        """
        Assess risk based on visibility.
        
        Args:
            visibility: Visibility in kilometers
            
        Returns:
            Visibility risk factor
        """
        if visibility > 5.0:
            level = RiskLevel.LOW
            desc = "Good visibility allows for safe visual operations."
            mitigation = "No specific mitigation required."
        elif visibility > 2.0:
            level = RiskLevel.MEDIUM
            desc = "Reduced visibility increases collision risks."
            mitigation = "Reduce operational speed and increase sensor reliance."
        elif visibility > 0.5:
            level = RiskLevel.HIGH
            desc = "Poor visibility significantly increases operational risks."
            mitigation = "Consider postponing mission or operate only in open areas."
        else:
            level = RiskLevel.CRITICAL
            desc = "Extremely poor visibility makes safe operation hazardous."
            mitigation = "Mission should be postponed until visibility improves."
        
        return RiskFactor(
            name="Visibility Conditions",
            category="Environmental",
            level=level,
            description=desc + f" Current visibility: {visibility:.1f} km.",
            mitigation=mitigation,
            weight=0.9
        )
    
    def _assess_current_risk(self, current_speed: float) -> RiskFactor:
        """
        Assess risk based on water current speed.
        
        Args:
            current_speed: Current speed in m/s
            
        Returns:
            Current risk factor
        """
        if current_speed < 0.5:
            level = RiskLevel.LOW
            desc = "Light currents, minimal impact on vessel operations."
            mitigation = "No specific mitigation required."
        elif current_speed < 1.0:
            level = RiskLevel.MEDIUM
            desc = "Moderate currents may affect precise positioning."
            mitigation = "Account for drift in mission planning."
        elif current_speed < 2.0:
            level = RiskLevel.HIGH
            desc = "Strong currents will significantly affect vessel control."
            mitigation = "Adjust mission plan to account for currents, increase power reserves."
        else:
            level = RiskLevel.CRITICAL
            desc = "Severe currents make safe operation extremely difficult."
            mitigation = "Mission should be postponed until currents decrease."
        
        return RiskFactor(
            name="Current Conditions",
            category="Environmental",
            level=level,
            description=desc + f" Current speed: {current_speed:.1f} m/s.",
            mitigation=mitigation,
            weight=0.7
        )
    
    def _assess_time_of_day_risk(self, is_daytime: bool) -> RiskFactor:
        """
        Assess risk based on time of day (daylight vs night).
        
        Args:
            is_daytime: True if operation is during daylight hours
            
        Returns:
            Time of day risk factor
        """
        if is_daytime:
            level = RiskLevel.LOW
            desc = "Daytime operations provide optimal visibility."
            mitigation = "No specific mitigation required."
        else:
            level = RiskLevel.MEDIUM
            desc = "Night operations have inherently higher risk due to reduced visibility."
            mitigation = "Use additional lighting and rely more on non-visual sensors."
        
        return RiskFactor(
            name="Time of Day",
            category="Environmental",
            level=level,
            description=desc,
            mitigation=mitigation,
            weight=0.6
        )
    
    def _assess_precipitation_risk(self, precipitation: float) -> RiskFactor:
        """
        Assess risk based on precipitation amount.
        
        Args:
            precipitation: Precipitation in mm/hour
            
        Returns:
            Precipitation risk factor
        """
        if precipitation < 1.0:
            level = RiskLevel.LOW
            desc = "No or light precipitation, minimal impact on operations."
            mitigation = "No specific mitigation required."
        elif precipitation < 5.0:
            level = RiskLevel.MEDIUM
            desc = "Moderate precipitation may affect sensor performance."
            mitigation = "Ensure water-sensitive equipment is properly protected."
        elif precipitation < 10.0:
            level = RiskLevel.HIGH
            desc = "Heavy precipitation will impact visibility and may affect electronics."
            mitigation = "Consider postponing mission or limiting duration."
        else:
            level = RiskLevel.CRITICAL
            desc = "Severe precipitation makes safe operation hazardous."
            mitigation = "Mission should be postponed until precipitation decreases."
        
        return RiskFactor(
            name="Precipitation",
            category="Environmental",
            level=level,
            description=desc + f" Current precipitation: {precipitation:.1f} mm/hour.",
            mitigation=mitigation,
            weight=0.5
        )