"""
Geographic utilities for USV Mission Planner.

This module provides functions for geographic calculations, such as
distance and bearing between coordinates.
"""

import math
from typing import Tuple

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two points on the Earth's surface.
    
    Uses the Haversine formula for calculating great-circle distance.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        
    Returns:
        Distance in meters between the two points
    """
    # Earth's radius in meters
    R = 6371000.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differences
    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad
    
    # Haversine formula
    a = math.sin(d_lat/2) * math.sin(d_lat/2) + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * \
        math.sin(d_lon/2) * math.sin(d_lon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the bearing from one point to another.
    
    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees
        
    Returns:
        Bearing in degrees (0-360, where 0 is North)
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Calculate the bearing
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing_rad = math.atan2(y, x)
    
    # Convert to degrees and normalize to 0-360
    bearing_deg = math.degrees(bearing_rad)
    bearing_normalized = (bearing_deg + 360) % 360
    
    return bearing_normalized

def offset_position(lat: float, lon: float, bearing: float, distance: float) -> Tuple[float, float]:
    """
    Calculate the resulting position after moving from a starting position.
    
    Args:
        lat: Starting latitude in degrees
        lon: Starting longitude in degrees
        bearing: Direction of movement in degrees (0-360, where 0 is North)
        distance: Distance to move in meters
        
    Returns:
        Tuple of (latitude, longitude) for the new position
    """
    # Earth's radius in meters
    R = 6371000.0
    
    # Convert to radians
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing)
    
    # Angular distance in radians
    angular_distance = distance / R
    
    # Calculate new latitude
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing_rad)
    )
    
    # Calculate new longitude
    new_lon_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )
    
    # Convert back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    
    return (new_lat, new_lon)

def haversine_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Calculate the distance between two points on the Earth's surface.
    
    Uses the Haversine formula for calculating great-circle distance.
    
    Args:
        point1: Tuple of (latitude, longitude) for the first point
        point2: Tuple of (latitude, longitude) for the second point
        
    Returns:
        Distance in meters between the two points
    """
    return calculate_distance(point1[0], point1[1], point2[0], point2[1])