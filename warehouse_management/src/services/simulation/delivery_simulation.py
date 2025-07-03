"""
Delivery simulation module for the warehouse management system.

This module provides functions for simulating delivery operations.
"""
import logging
import datetime
import random
import uuid
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

from src.utils.helpers import get_db_session

logger = logging.getLogger(__name__)

def simulate_deliveries(config: Dict[str, Any],
                      order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Simulate delivery operations.
    
    Args:
        config: Simulation configuration
        order_data: Optional order data from order simulation
        
    Returns:
        Dictionary with simulation results
    """
    logger.info("Simulating delivery operations")
    
    # Check if we have order data
    if not order_data:
        return {
            "status": "error",
            "message": "No order data provided for delivery simulation",
            "deliveries": []
        }
    
    # Filter orders that can be delivered
    deliverable_orders = [
        order for order in order_data
        if order['status'] in ['placed', 'processing', 'shipped']
    ]
    
    if not deliverable_orders:
        return {
            "status": "warning",
            "message": "No deliverable orders found",
            "deliveries": []
        }
    
    # Generate deliveries
    deliveries = []
    delivery_times = {}
    delivery_distances = {}
    delivery_statuses = defaultdict(int)
    
    # Set simulation parameters
    avg_speed_kmh = config.get('avg_delivery_speed_kmh', 20)
    delivery_time_std = config.get('delivery_time_std_minutes', 15)
    success_rate = config.get('delivery_success_rate', 0.95)
    
    # Process each order
    for order in deliverable_orders:
        # Extract data
        order_id = order.get('order_id', order.get('id'))  # Support both formats
        warehouse_id = order['warehouse_fulfilled']
        warehouse_lat = None
        warehouse_lon = None
        
        # In a real system, we would look up the warehouse coordinates
        # For simulation, we'll use random coordinates if not available
        if 'warehouse_latitude' in order and 'warehouse_longitude' in order:
            warehouse_lat = order['warehouse_latitude']
            warehouse_lon = order['warehouse_longitude']
        
        customer_lat = order['customer_latitude']
        customer_lon = order['customer_longitude']
        order_time = datetime.datetime.fromisoformat(order['timestamp'])
        
        # Calculate delivery details
        delivery_details = _calculate_delivery_details(
            order_time=order_time,
            warehouse_lat=warehouse_lat,
            warehouse_lon=warehouse_lon,
            customer_lat=customer_lat,
            customer_lon=customer_lon,
            avg_speed_kmh=avg_speed_kmh,
            delivery_time_std=delivery_time_std,
            config=config
        )
        
        # Determine if delivery is successful
        is_successful = random.random() < success_rate
        
        # Set status
        if is_successful:
            status = "delivered"
        else:
            # Randomly choose failure reason
            failure_reasons = ["customer_unavailable", "address_not_found", "vehicle_breakdown"]
            failure_weights = [0.5, 0.3, 0.2]
            failure_reason = random.choices(failure_reasons, weights=failure_weights)[0]
            status = f"failed_{failure_reason}"
        
        # Create delivery record
        delivery = {
            "delivery_id": str(uuid.uuid4()),
            "order_id": order_id,
            "warehouse_id": warehouse_id,
            "customer_latitude": customer_lat,
            "customer_longitude": customer_lon,
            "dispatch_time": delivery_details['dispatch_time'].isoformat(),
            "estimated_delivery_time": delivery_details['estimated_delivery_time'].isoformat(),
            "actual_delivery_time": delivery_details['actual_delivery_time'].isoformat(),
            "distance_km": delivery_details['distance_km'],
            "status": status,
            "delivery_agent_id": f"DA{random.randint(1000, 9999)}",
            "route_points": delivery_details['route_points']
        }
        
        deliveries.append(delivery)
        
        # Track metrics
        delivery_time_minutes = (delivery_details['actual_delivery_time'] - 
                                delivery_details['dispatch_time']).total_seconds() / 60
        delivery_times[order_id] = delivery_time_minutes
        delivery_distances[order_id] = delivery_details['distance_km']
        delivery_statuses[status] += 1
    
    # Calculate metrics
    avg_delivery_time = sum(delivery_times.values()) / len(delivery_times) if delivery_times else 0
    avg_delivery_distance = sum(delivery_distances.values()) / len(delivery_distances) if delivery_distances else 0
    on_time_rate = sum(1 for d in deliveries if d['status'] == 'delivered') / len(deliveries) if deliveries else 0
    
    return {
        "status": "success",
        "deliveries": deliveries,
        "summary": {
            "total_deliveries": len(deliveries),
            "average_delivery_time_minutes": avg_delivery_time,
            "average_delivery_distance_km": avg_delivery_distance,
            "on_time_delivery_rate": on_time_rate,
            "delivery_statuses": dict(delivery_statuses)
        }
    }

def _calculate_delivery_details(order_time: datetime.datetime,
                              warehouse_lat: Optional[float],
                              warehouse_lon: Optional[float],
                              customer_lat: float,
                              customer_lon: float,
                              avg_speed_kmh: float,
                              delivery_time_std: float,
                              config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate delivery details including times and route.
    
    Args:
        order_time: Order timestamp
        warehouse_lat: Warehouse latitude (or None)
        warehouse_lon: Warehouse longitude (or None)
        customer_lat: Customer latitude
        customer_lon: Customer longitude
        avg_speed_kmh: Average delivery speed in km/h
        delivery_time_std: Standard deviation of delivery time in minutes
        config: Simulation configuration
        
    Returns:
        Dictionary with delivery details
    """
    # Generate warehouse coordinates if not provided
    if warehouse_lat is None or warehouse_lon is None:
        # Generate random warehouse location within ~5km of customer
        radius_km = 5
        warehouse_lat, warehouse_lon = _generate_random_nearby_point(
            customer_lat, customer_lon, radius_km
        )
    
    # Calculate distance
    distance_km = _haversine_distance(
        warehouse_lat, warehouse_lon,
        customer_lat, customer_lon
    )
    
    # Add some randomness to distance (e.g., not straight line)
    distance_factor = random.uniform(1.1, 1.3)
    adjusted_distance_km = distance_km * distance_factor
    
    # Calculate estimated delivery time
    # Order processing time
    processing_minutes = random.uniform(
        config.get('min_processing_minutes', 10),
        config.get('max_processing_minutes', 30)
    )
    
    # Travel time
    travel_minutes = (adjusted_distance_km / avg_speed_kmh) * 60
    
    # Total estimated time
    total_estimated_minutes = processing_minutes + travel_minutes
    
    # Calculate dispatch time (after processing)
    dispatch_time = order_time + datetime.timedelta(minutes=processing_minutes)
    
    # Calculate estimated delivery time
    estimated_delivery_time = dispatch_time + datetime.timedelta(minutes=travel_minutes)
    
    # Add randomness to actual delivery time
    time_variation_minutes = np.random.normal(0, delivery_time_std)
    actual_delivery_time = estimated_delivery_time + datetime.timedelta(minutes=time_variation_minutes)
    
    # Generate route points
    route_points = _generate_route_points(
        warehouse_lat, warehouse_lon,
        customer_lat, customer_lon,
        num_points=config.get('route_points', 5)
    )
    
    return {
        "dispatch_time": dispatch_time,
        "estimated_delivery_time": estimated_delivery_time,
        "actual_delivery_time": actual_delivery_time,
        "distance_km": adjusted_distance_km,
        "route_points": route_points
    }

def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the Haversine distance between two points in kilometers.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    
    return c * r

def _generate_random_nearby_point(lat: float, lon: float, radius_km: float) -> Tuple[float, float]:
    """
    Generate a random point within a given radius of a center point.
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Radius in kilometers
        
    Returns:
        Tuple of (latitude, longitude)
    """
    # Convert radius from kilometers to degrees (approximate)
    radius_deg = radius_km / 111.32  # 1 degree is approximately 111.32 km
    
    # Generate random angle and distance
    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_deg)
    
    # Calculate new point
    new_lat = lat + distance * math.cos(angle)
    new_lon = lon + distance * math.sin(angle) / math.cos(math.radians(lat))
    
    return new_lat, new_lon

def _generate_route_points(start_lat: float, start_lon: float,
                         end_lat: float, end_lon: float,
                         num_points: int = 5) -> List[Dict[str, float]]:
    """
    Generate intermediate points along a route.
    
    Args:
        start_lat: Starting latitude
        start_lon: Starting longitude
        end_lat: Ending latitude
        end_lon: Ending longitude
        num_points: Number of intermediate points
        
    Returns:
        List of dictionaries with latitude and longitude
    """
    points = []
    
    # Add starting point
    points.append({
        "latitude": start_lat,
        "longitude": start_lon,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # Generate intermediate points
    for i in range(1, num_points + 1):
        # Calculate fraction of the way
        fraction = i / (num_points + 1)
        
        # Linear interpolation
        lat = start_lat + fraction * (end_lat - start_lat)
        lon = start_lon + fraction * (end_lon - start_lon)
        
        # Add some randomness to make it realistic
        lat_jitter = random.uniform(-0.002, 0.002)
        lon_jitter = random.uniform(-0.002, 0.002)
        
        points.append({
            "latitude": lat + lat_jitter,
            "longitude": lon + lon_jitter,
            "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=i*10)).isoformat()
        })
    
    # Add ending point
    points.append({
        "latitude": end_lat,
        "longitude": end_lon,
        "timestamp": (datetime.datetime.now() + datetime.timedelta(minutes=(num_points+1)*10)).isoformat()
    })
    
    return points

def calculate_delivery_metrics(deliveries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate delivery performance metrics.
    
    Args:
        deliveries: List of delivery dictionaries
        
    Returns:
        Dictionary with metrics
    """
    if not deliveries:
        return {
            "total_deliveries": 0,
            "on_time_rate": 0,
            "average_delay_minutes": 0
        }
    
    total = len(deliveries)
    on_time_count = 0
    delays = []
    distances = []
    
    for delivery in deliveries:
        # Extract times
        estimated_time = datetime.datetime.fromisoformat(delivery['estimated_delivery_time'])
        actual_time = datetime.datetime.fromisoformat(delivery['actual_delivery_time'])
        
        # Calculate delay
        delay_minutes = (actual_time - estimated_time).total_seconds() / 60
        
        # Check if on time (allow 5 minute buffer)
        if delay_minutes <= 5:
            on_time_count += 1
        
        delays.append(delay_minutes)
        distances.append(delivery['distance_km'])
    
    # Calculate metrics
    on_time_rate = on_time_count / total
    average_delay = sum(delays) / len(delays)
    average_distance = sum(distances) / len(distances)
    
    return {
        "total_deliveries": total,
        "on_time_rate": on_time_rate,
        "average_delay_minutes": average_delay,
        "average_distance_km": average_distance
    }


class DeliverySimulation:
    """
    Class for simulating delivery operations.
    
    This class provides methods to simulate deliveries based on orders and
    delivery agent configurations.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the delivery simulation with optional configuration.
        
        Args:
            config: Configuration dictionary for the simulation
        """
        self.config = config or {
            'avg_delivery_speed_kmh': 20,
            'delivery_time_std_minutes': 15,
            'delivery_success_rate': 0.95,
            'num_delivery_agents': 10
        }
    
    def simulate(self, order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run the delivery simulation with order data.
        
        Args:
            order_data: Order data from order simulation
            
        Returns:
            Dictionary with simulation results
        """
        return simulate_deliveries(self.config, order_data)
    
    def create_and_run_custom_scenario(self, scenario_config: Dict[str, Any], 
                                      order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create and run a custom delivery scenario.
        
        Args:
            scenario_config: Configuration for the custom scenario
            order_data: Order data from order simulation
            
        Returns:
            Dictionary with scenario results
        """
        # Extract delivery configuration from scenario
        delivery_config = scenario_config.get('delivery_config', {})
        
        # Merge with default config
        config = {**self.config, **delivery_config}
        
        # Run simulation with merged config
        return simulate_deliveries(config, order_data)
