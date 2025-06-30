"""
Route optimization module for the warehouse management system.
Provides functions for optimizing delivery routes.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import math
import random

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

logger = logging.getLogger(__name__)

def optimize_routes(warehouse_data: Dict[str, Any],
                   purchase_data: List[Dict[str, Any]],
                   pincode_data: List[Dict[str, Any]],
                   config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize delivery routes for a warehouse.
    
    Args:
        warehouse_data: Dictionary with warehouse information
        purchase_data: List of purchase event dictionaries
        pincode_data: List of pincode mapping dictionaries
        config: Optimization configuration
        
    Returns:
        Dictionary with optimization results
    """
    logger.info(f"Optimizing delivery routes for warehouse: {warehouse_data['name']}")
    
    # Convert to DataFrames
    purchases_df = pd.DataFrame(purchase_data)
    pincodes_df = pd.DataFrame(pincode_data)
    
    # Check if DataFrames are empty
    if purchases_df.empty or pincodes_df.empty:
        logger.warning("Not enough data for route optimization")
        return {
            "status": "error",
            "message": "Not enough data for route optimization",
            "routes": []
        }
    
    # Create pincode lookup for coordinates and area names
    pincode_info = {}
    for _, row in pincodes_df.iterrows():
        pincode_info[row['pincode']] = {
            'coords': (row['latitude'], row['longitude']),
            'area_name': row['area_name']
        }
    
    # Group purchases by pincode
    pincode_demand = defaultdict(int)
    for _, row in purchases_df.iterrows():
        pincode_demand[row['customer_pincode']] += row['quantity']
    
    # Filter pincodes with demand
    delivery_pincodes = [
        {
            'pincode': pincode,
            'demand': demand,
            'latitude': pincode_info.get(pincode, {}).get('coords', (0, 0))[0],
            'longitude': pincode_info.get(pincode, {}).get('coords', (0, 0))[1],
            'area_name': pincode_info.get(pincode, {}).get('area_name', 'Unknown')
        }
        for pincode, demand in pincode_demand.items()
        if pincode in pincode_info
    ]
    
    # Check if we have delivery pincodes
    if not delivery_pincodes:
        logger.warning("No delivery pincodes found")
        return {
            "status": "error",
            "message": "No delivery pincodes found",
            "routes": []
        }
    
    # Get warehouse coordinates
    warehouse_coords = (warehouse_data['latitude'], warehouse_data['longitude'])
    
    # Calculate clusters for delivery areas
    max_stops_per_route = config.get('max_stops_per_route', 15)
    max_routes = config.get('max_routes', 10)
    
    clusters = cluster_delivery_points(
        delivery_points=delivery_pincodes,
        warehouse_coords=warehouse_coords,
        max_clusters=max_routes,
        max_points_per_cluster=max_stops_per_route
    )
    
    # Optimize route for each cluster
    routes = []
    
    for i, cluster in enumerate(clusters):
        if not cluster:
            continue
        
        # Optimize route for this cluster
        optimized_route = optimize_cluster_route(
            delivery_points=cluster,
            warehouse_coords=warehouse_coords
        )
        
        # Calculate route metrics
        total_distance = calculate_route_distance(
            route_points=optimized_route,
            warehouse_coords=warehouse_coords
        )
        
        total_demand = sum(point['demand'] for point in cluster)
        
        # Create route object
        route = {
            'route_id': f"R{i+1:02d}",
            'stops': len(cluster),
            'total_distance': round(total_distance, 2),
            'total_demand': total_demand,
            'estimated_time_minutes': int(total_distance * config.get('minutes_per_km', 3)),
            'stops_detail': [
                {
                    'stop_number': j+1,
                    'pincode': point['pincode'],
                    'area_name': point['area_name'],
                    'demand': point['demand'],
                    'latitude': point['latitude'],
                    'longitude': point['longitude']
                }
                for j, point in enumerate(optimized_route)
            ]
        }
        
        routes.append(route)
    
    # Sort routes by total distance
    routes.sort(key=lambda x: x['total_distance'])
    
    return {
        "status": "success",
        "message": "Route optimization completed",
        "warehouse": {
            "id": warehouse_data['id'],
            "name": warehouse_data['name'],
            "latitude": warehouse_data['latitude'],
            "longitude": warehouse_data['longitude']
        },
        "routes": routes,
        "summary": {
            "total_routes": len(routes),
            "total_stops": sum(route['stops'] for route in routes),
            "total_distance": round(sum(route['total_distance'] for route in routes), 2),
            "total_demand": sum(route['total_demand'] for route in routes)
        }
    }

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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

def cluster_delivery_points(delivery_points: List[Dict[str, Any]],
                          warehouse_coords: Tuple[float, float],
                          max_clusters: int,
                          max_points_per_cluster: int) -> List[List[Dict[str, Any]]]:
    """
    Cluster delivery points into routes.
    
    Args:
        delivery_points: List of delivery point dictionaries
        warehouse_coords: Warehouse coordinates (latitude, longitude)
        max_clusters: Maximum number of clusters
        max_points_per_cluster: Maximum points per cluster
        
    Returns:
        List of clusters, each containing delivery points
    """
    # If we have few points, just put them all in one cluster
    if len(delivery_points) <= max_points_per_cluster:
        return [delivery_points]
    
    # Extract coordinates
    coords = np.array([[point['latitude'], point['longitude']] for point in delivery_points])
    
    # Calculate distance matrix
    distances = squareform(pdist(coords, metric='euclidean'))
    
    # Simple greedy clustering
    clusters = []
    remaining_points = list(range(len(delivery_points)))
    
    # Start with points farthest from warehouse
    warehouse_lat, warehouse_lon = warehouse_coords
    distances_from_warehouse = [
        haversine_distance(
            warehouse_lat, warehouse_lon,
            delivery_points[i]['latitude'], delivery_points[i]['longitude']
        )
        for i in range(len(delivery_points))
    ]
    
    # Sort by distance from warehouse (descending)
    remaining_points.sort(key=lambda i: -distances_from_warehouse[i])
    
    while remaining_points and len(clusters) < max_clusters:
        # Start a new cluster with the point farthest from warehouse
        current_cluster = [remaining_points.pop(0)]
        
        # Add nearest neighbors until we reach max size or run out of points
        while len(current_cluster) < max_points_per_cluster and remaining_points:
            # Find closest point to any point in current cluster
            min_dist = float('inf')
            closest_idx = -1
            
            for i, point_idx in enumerate(remaining_points):
                for cluster_idx in current_cluster:
                    dist = distances[point_idx][cluster_idx]
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
            
            if closest_idx >= 0:
                # Add closest point to cluster
                current_cluster.append(remaining_points.pop(closest_idx))
            else:
                break
        
        # Add cluster to list
        clusters.append([delivery_points[i] for i in current_cluster])
    
    # If we still have points, add them to the nearest cluster
    if remaining_points:
        for point_idx in remaining_points:
            # Find closest cluster
            min_dist = float('inf')
            closest_cluster = 0
            
            for i, cluster in enumerate(clusters):
                for cluster_point in cluster:
                    dist = haversine_distance(
                        delivery_points[point_idx]['latitude'],
                        delivery_points[point_idx]['longitude'],
                        cluster_point['latitude'],
                        cluster_point['longitude']
                    )
                    if dist < min_dist:
                        min_dist = dist
                        closest_cluster = i
            
            # Add to closest cluster
            clusters[closest_cluster].append(delivery_points[point_idx])
    
    return clusters

def optimize_cluster_route(delivery_points: List[Dict[str, Any]],
                         warehouse_coords: Tuple[float, float]) -> List[Dict[str, Any]]:
    """
    Optimize route for a cluster using a simple heuristic.
    
    Args:
        delivery_points: List of delivery point dictionaries
        warehouse_coords: Warehouse coordinates (latitude, longitude)
        
    Returns:
        Optimized route as list of delivery points
    """
    # If we have few points, just return them
    if len(delivery_points) <= 2:
        return delivery_points
    
    # Extract coordinates
    points = [(i, point['latitude'], point['longitude']) for i, point in enumerate(delivery_points)]
    
    # Nearest neighbor algorithm
    warehouse_lat, warehouse_lon = warehouse_coords
    route_indices = []
    unvisited = set(range(len(points)))
    
    # Start from warehouse and find nearest point
    current_lat, current_lon = warehouse_lat, warehouse_lon
    
    while unvisited:
        # Find nearest unvisited point
        nearest_idx = -1
        min_dist = float('inf')
        
        for i in unvisited:
            _, lat, lon = points[i]
            dist = haversine_distance(current_lat, current_lon, lat, lon)
            
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        # Add to route
        route_indices.append(nearest_idx)
        unvisited.remove(nearest_idx)
        
        # Update current position
        current_lat, current_lon = points[nearest_idx][1], points[nearest_idx][2]
    
    # Return route
    return [delivery_points[i] for i in route_indices]

def calculate_route_distance(route_points: List[Dict[str, Any]],
                           warehouse_coords: Tuple[float, float]) -> float:
    """
    Calculate total distance of a route.
    
    Args:
        route_points: List of route point dictionaries
        warehouse_coords: Warehouse coordinates (latitude, longitude)
        
    Returns:
        Total distance in kilometers
    """
    if not route_points:
        return 0
    
    warehouse_lat, warehouse_lon = warehouse_coords
    total_distance = 0
    
    # Distance from warehouse to first point
    first_point = route_points[0]
    total_distance += haversine_distance(
        warehouse_lat, warehouse_lon,
        first_point['latitude'], first_point['longitude']
    )
    
    # Distance between consecutive points
    for i in range(len(route_points) - 1):
        point1 = route_points[i]
        point2 = route_points[i + 1]
        
        total_distance += haversine_distance(
            point1['latitude'], point1['longitude'],
            point2['latitude'], point2['longitude']
        )
    
    # Distance from last point back to warehouse
    last_point = route_points[-1]
    total_distance += haversine_distance(
        last_point['latitude'], last_point['longitude'],
        warehouse_lat, warehouse_lon
    )
    
    return total_distance
