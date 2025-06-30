"""
Helper functions for the warehouse management system.
"""
import os
import logging
import random
import uuid
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime, timedelta, date
import json
import csv

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.config.constants import (
    BANGALORE_BOUNDS, HOURLY_DEMAND_PATTERNS,
    DAILY_DEMAND_PATTERNS, MONTHLY_DEMAND_PATTERNS
)

logger = logging.getLogger(__name__)

def generate_bangalore_pincode() -> str:
    """
    Generate a random Bangalore pincode.
    
    Returns:
        Bangalore pincode string
    """
    # Bangalore pincodes are in the range 560001-560100
    return f"56{random.randint(0, 1)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"

def generate_bangalore_coordinates() -> Tuple[float, float]:
    """
    Generate random coordinates within Bangalore bounds.
    
    Returns:
        Tuple of (latitude, longitude)
    """
    lat = random.uniform(BANGALORE_BOUNDS['south'], BANGALORE_BOUNDS['north'])
    lon = random.uniform(BANGALORE_BOUNDS['west'], BANGALORE_BOUNDS['east'])
    return (lat, lon)

def generate_bangalore_area_name() -> str:
    """
    Generate a random Bangalore area name.
    
    Returns:
        Area name string
    """
    areas = [
        "Whitefield", "Koramangala", "Indiranagar", "HSR Layout", "Jayanagar",
        "JP Nagar", "Bannerghatta Road", "Electronic City", "Marathahalli",
        "Hebbal", "Yelahanka", "Malleswaram", "Rajajinagar", "Basavanagudi",
        "BTM Layout", "Banashankari", "Vijayanagar", "RT Nagar", "Banaswadi",
        "CV Raman Nagar", "Domlur", "Old Airport Road", "Sarjapur Road",
        "Bellandur", "Kadugodi", "Hoodi", "KR Puram", "Hennur", "Kalyan Nagar",
        "Kammanahalli", "Ramamurthy Nagar", "Horamavu", "Benson Town", "Cox Town",
        "Frazer Town", "Richards Town", "Shivajinagar", "MG Road", "Brigade Road",
        "Residency Road", "Richmond Road", "Lavelle Road", "Church Street",
        "Infantry Road", "Commercial Street", "Cunningham Road", "Race Course Road",
        "Sadashivanagar", "Vasanth Nagar", "Jayamahal", "Dollars Colony"
    ]
    return random.choice(areas)

def get_demand_multiplier(timestamp: datetime) -> float:
    """
    Calculate demand multiplier based on time patterns.
    
    Args:
        timestamp: Datetime to calculate demand for
        
    Returns:
        Demand multiplier (float)
    """
    # Get hour, day of week, and month
    hour = timestamp.hour
    day_of_week = timestamp.weekday()  # 0-6 for Monday-Sunday
    month = timestamp.month - 1  # 0-11 for January-December
    
    # Get base multipliers
    is_weekend = day_of_week >= 5  # Saturday or Sunday
    hourly_pattern = HOURLY_DEMAND_PATTERNS['weekend' if is_weekend else 'weekday']
    hourly_multiplier = hourly_pattern[hour]
    daily_multiplier = DAILY_DEMAND_PATTERNS[day_of_week]
    monthly_multiplier = MONTHLY_DEMAND_PATTERNS[month]
    
    # Combine multipliers
    return hourly_multiplier * daily_multiplier * monthly_multiplier

def calculate_delivery_time(distance_km: float) -> int:
    """
    Calculate delivery time based on distance.
    
    Args:
        distance_km: Distance in kilometers
        
    Returns:
        Delivery time in minutes
    """
    # Base time for order processing
    base_time = 15
    
    # Time per kilometer (varies with traffic)
    # Assume average speed of 20 km/h in city traffic
    time_per_km = 3  # minutes
    
    # Add some randomness to account for traffic variations
    traffic_factor = random.uniform(0.8, 1.5)
    
    # Calculate total delivery time
    delivery_time = base_time + (distance_km * time_per_km * traffic_factor)
    
    return int(round(delivery_time))

def save_to_json(data: Union[List, Dict], filepath: str) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Save data to JSON file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Data saved to {filepath}")

def save_to_csv(data: List[Dict], filepath: str) -> None:
    """
    Save data to CSV file.
    
    Args:
        data: List of dictionaries to save
        filepath: Path to save file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Check if data is empty
    if not data:
        logger.warning(f"No data to save to {filepath}")
        return
    
    # Get fieldnames from first item
    fieldnames = data[0].keys()
    
    # Save data to CSV file
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Data saved to {filepath}")

def format_timestamp(timestamp: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        timestamp: Datetime to format
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse timestamp string to datetime.
    
    Args:
        timestamp_str: Timestamp string
        
    Returns:
        Datetime object
    """
    return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generate a list of dates between start and end dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of dates
    """
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]

def calculate_stock_percentage(current_stock: int, max_capacity: int) -> float:
    """
    Calculate stock percentage.
    
    Args:
        current_stock: Current stock level
        max_capacity: Maximum capacity
        
    Returns:
        Stock percentage
    """
    if max_capacity <= 0:
        return 0.0
    return (current_stock / max_capacity) * 100.0

def get_alert_level(stock_percentage: float) -> str:
    """
    Get alert level based on stock percentage.
    
    Args:
        stock_percentage: Stock percentage
        
    Returns:
        Alert level string
    """
    if stock_percentage <= 10:
        return "critical"
    elif stock_percentage <= 20:
        return "low"
    elif stock_percentage >= 90:
        return "overstocked"
    else:
        return "normal"

def get_recommendation(alert_level: str, product_name: str, warehouse_name: str) -> str:
    """
    Get recommendation based on alert level.
    
    Args:
        alert_level: Alert level
        product_name: Product name
        warehouse_name: Warehouse name
        
    Returns:
        Recommendation string
    """
    if alert_level == "critical":
        return f"URGENT: Immediate restocking required for {product_name} at {warehouse_name}"
    elif alert_level == "low":
        return f"Schedule restocking for {product_name} at {warehouse_name} within 24 hours"
    elif alert_level == "overstocked":
        return f"Consider redistributing excess {product_name} from {warehouse_name} to other warehouses"
    else:
        return "No action required"
