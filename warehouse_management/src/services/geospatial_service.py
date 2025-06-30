"""
Geospatial service for the warehouse management system.

This service provides geospatial functionality including:
- Distance calculations between points
- Service area calculations for warehouses
- Nearest warehouse determination
- Delivery zone optimization
- Geospatial clustering and visualization
"""
import logging
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.spatial import Voronoi
from scipy.spatial.distance import cdist
import folium
from folium.plugins import HeatMap, MarkerCluster
from sklearn.cluster import DBSCAN

from src.utils.helpers import get_db_session
from src.utils.visualization import create_choropleth, add_warehouse_markers

logger = logging.getLogger(__name__)

class GeospatialService:
    """Service for geospatial operations in the warehouse management system."""
    
    def __init__(self):
        """Initialize the geospatial service."""
        logger.info("GeospatialService initialized")
    
    def calculate_distance(self, 
                         lat1: float, 
                         lon1: float, 
                         lat2: float, 
                         lon2: float, 
                         method: str = 'haversine') -> float:
        """
        Calculate distance between two points.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            method: Method to use for calculation ('haversine', 'euclidean')
            
        Returns:
            Distance in kilometers
        """
        if method == 'haversine':
            # Haversine formula for distance on a sphere (Earth)
            R = 6371  # Earth radius in kilometers
            
            # Convert to radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Differences
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Haversine formula
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c
            
            return distance
        elif method == 'euclidean':
            # Simple Euclidean distance (for small areas)
            # Note: This is not accurate for large distances on Earth
            return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111  # Approx 111km per degree
        else:
            raise ValueError(f"Unknown distance calculation method: {method}")
    
    def calculate_distance_matrix(self, 
                                locations: List[Dict[str, Any]], 
                                method: str = 'haversine') -> np.ndarray:
        """
        Calculate distance matrix between multiple locations.
        
        Args:
            locations: List of location dictionaries with 'latitude' and 'longitude' keys
            method: Method to use for calculation ('haversine', 'euclidean')
            
        Returns:
            Distance matrix as numpy array
        """
        n = len(locations)
        distance_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                distance = self.calculate_distance(
                    locations[i]['latitude'], locations[i]['longitude'],
                    locations[j]['latitude'], locations[j]['longitude'],
                    method=method
                )
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance
        
        return distance_matrix
    
    def find_nearest_warehouse(self, 
                             lat: float, 
                             lon: float, 
                             warehouses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Find nearest warehouse to a point.
        
        Args:
            lat: Latitude of point
            lon: Longitude of point
            warehouses: List of warehouse dictionaries with 'latitude' and 'longitude' keys
            
        Returns:
            Dictionary with nearest warehouse and distance
        """
        if not warehouses:
            return {"warehouse": None, "distance": None}
        
        min_distance = float('inf')
        nearest_warehouse = None
        
        for warehouse in warehouses:
            distance = self.calculate_distance(
                lat, lon,
                warehouse['latitude'], warehouse['longitude']
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_warehouse = warehouse
        
        return {
            "warehouse": nearest_warehouse,
            "distance": min_distance
        }
    
    def calculate_service_areas(self, warehouses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate service areas for warehouses using Voronoi diagrams.
        
        Args:
            warehouses: List of warehouse dictionaries with 'latitude' and 'longitude' keys
            
        Returns:
            Dictionary with service area information
        """
        if len(warehouses) < 2:
            logger.warning("Need at least 2 warehouses to calculate service areas")
            return {"status": "error", "message": "Need at least 2 warehouses"}
        
        # Extract warehouse coordinates
        points = np.array([[w['latitude'], w['longitude']] for w in warehouses])
        
        # Compute Voronoi diagram
        vor = Voronoi(points)
        
        # Process regions
        service_areas = []
        
        for i, warehouse in enumerate(warehouses):
            # Get region for this warehouse
            region_idx = vor.point_region[i]
            region = vor.regions[region_idx]
            
            # Skip if region is unbounded
            if -1 in region:
                continue
            
            # Get vertices for this region
            vertices = [vor.vertices[v].tolist() for v in region]
            
            # Calculate area (approximate)
            area = self._calculate_polygon_area(vertices)
            
            service_areas.append({
                "warehouse_id": warehouse['id'],
                "warehouse_name": warehouse['name'],
                "vertices": vertices,
                "area_km2": area,
                "center": [warehouse['latitude'], warehouse['longitude']]
            })
        
        return {
            "status": "success",
            "service_areas": service_areas
        }
    
    def _calculate_polygon_area(self, vertices: List[List[float]]) -> float:
        """
        Calculate area of a polygon using Shoelace formula.
        
        Args:
            vertices: List of [lat, lon] coordinates
            
        Returns:
            Area in square kilometers (approximate)
        """
        if len(vertices) < 3:
            return 0
        
        # Convert to radians and apply Shoelace formula
        n = len(vertices)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            # Approximate conversion to km (very rough)
            area += vertices[i][0] * vertices[j][1]
            area -= vertices[j][0] * vertices[i][1]
        
        area = abs(area) / 2.0
        # Rough conversion to square km (this is an approximation)
        area *= 111 * 111  # Approx 111km per degree
        
        return area
    
    def cluster_delivery_points(self, 
                              delivery_points: List[Dict[str, Any]], 
                              eps: float = 1.0, 
                              min_samples: int = 5) -> Dict[str, Any]:
        """
        Cluster delivery points using DBSCAN.
        
        Args:
            delivery_points: List of delivery point dictionaries with 'latitude' and 'longitude' keys
            eps: Maximum distance between points in a cluster
            min_samples: Minimum number of points to form a cluster
            
        Returns:
            Dictionary with clustering results
        """
        if not delivery_points:
            return {"status": "error", "message": "No delivery points provided"}
        
        # Extract coordinates
        coords = np.array([[p['latitude'], p['longitude']] for p in delivery_points])
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine').fit(coords)
        
        # Get cluster labels
        labels = clustering.labels_
        
        # Count clusters (excluding noise points with label -1)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        
        # Group points by cluster
        clusters = defaultdict(list)
        
        for i, label in enumerate(labels):
            cluster_id = int(label)  # Convert numpy int to Python int
            point = delivery_points[i].copy()
            point['cluster_id'] = cluster_id
            clusters[cluster_id].append(point)
        
        # Calculate cluster statistics
        cluster_stats = []
        
        for cluster_id, points in clusters.items():
            if cluster_id == -1:
                # Skip noise points
                continue
            
            # Calculate centroid
            centroid_lat = sum(p['latitude'] for p in points) / len(points)
            centroid_lon = sum(p['longitude'] for p in points) / len(points)
            
            # Calculate radius (maximum distance from centroid)
            max_distance = max(
                self.calculate_distance(
                    centroid_lat, centroid_lon,
                    p['latitude'], p['longitude']
                )
                for p in points
            )
            
            cluster_stats.append({
                "cluster_id": cluster_id,
                "point_count": len(points),
                "centroid": [centroid_lat, centroid_lon],
                "radius_km": max_distance
            })
        
        return {
            "status": "success",
            "total_points": len(delivery_points),
            "cluster_count": n_clusters,
            "noise_points": list(labels).count(-1),
            "clusters": cluster_stats,
            "points": [
                {
                    "latitude": p['latitude'],
                    "longitude": p['longitude'],
                    "cluster_id": p['cluster_id']
                }
                for p in [p for cluster in clusters.values() for p in cluster]
            ]
        }
    
    def create_heatmap(self, 
                     points: List[Dict[str, Any]], 
                     value_key: Optional[str] = None,
                     center: Optional[List[float]] = None) -> folium.Map:
        """
        Create a heatmap from points.
        
        Args:
            points: List of point dictionaries with 'latitude' and 'longitude' keys
            value_key: Optional key for intensity values
            center: Optional center coordinates [lat, lon]
            
        Returns:
            Folium map with heatmap
        """
        if not points:
            logger.warning("No points provided for heatmap")
            return folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Default to India
        
        # Determine center if not provided
        if not center:
            center = [
                sum(p['latitude'] for p in points) / len(points),
                sum(p['longitude'] for p in points) / len(points)
            ]
        
        # Create map
        m = folium.Map(location=center, zoom_start=11)
        
        # Prepare heatmap data
        if value_key and value_key in points[0]:
            # Use provided values for intensity
            heat_data = [
                [p['latitude'], p['longitude'], p[value_key]]
                for p in points
                if value_key in p
            ]
        else:
            # Default to uniform intensity
            heat_data = [[p['latitude'], p['longitude']] for p in points]
        
        # Add heatmap
        HeatMap(heat_data).add_to(m)
        
        return m
    
    def create_cluster_map(self, 
                         clusters: Dict[str, Any], 
                         warehouses: Optional[List[Dict[str, Any]]] = None) -> folium.Map:
        """
        Create a map with clustered points.
        
        Args:
            clusters: Clustering results from cluster_delivery_points
            warehouses: Optional list of warehouse dictionaries
            
        Returns:
            Folium map with clustered points
        """
        if clusters['status'] != 'success':
            logger.warning("Invalid cluster data for map")
            return folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Default to India
        
        # Determine center
        points = clusters['points']
        center = [
            sum(p['latitude'] for p in points) / len(points),
            sum(p['longitude'] for p in points) / len(points)
        ]
        
        # Create map
        m = folium.Map(location=center, zoom_start=11)
        
        # Add warehouses if provided
        if warehouses:
            for warehouse in warehouses:
                folium.Marker(
                    location=[warehouse['latitude'], warehouse['longitude']],
                    popup=warehouse['name'],
                    icon=folium.Icon(color='red', icon='industry', prefix='fa')
                ).add_to(m)
        
        # Create marker clusters for each cluster
        cluster_groups = {}
        
        for point in points:
            cluster_id = point['cluster_id']
            
            if cluster_id == -1:
                # Noise points in black
                folium.CircleMarker(
                    location=[point['latitude'], point['longitude']],
                    radius=3,
                    color='black',
                    fill=True,
                    fill_opacity=0.7
                ).add_to(m)
            else:
                # Add to appropriate cluster group
                if cluster_id not in cluster_groups:
                    cluster_groups[cluster_id] = folium.FeatureGroup(name=f"Cluster {cluster_id}")
                    m.add_child(cluster_groups[cluster_id])
                
                # Add marker to cluster group
                folium.CircleMarker(
                    location=[point['latitude'], point['longitude']],
                    radius=5,
                    color=self._get_cluster_color(cluster_id),
                    fill=True,
                    fill_opacity=0.7,
                    popup=f"Cluster {cluster_id}"
                ).add_to(cluster_groups[cluster_id])
        
        # Add cluster centroids
        for cluster in clusters['clusters']:
            folium.Marker(
                location=cluster['centroid'],
                popup=f"Cluster {cluster['cluster_id']}: {cluster['point_count']} points",
                icon=folium.Icon(color=self._get_cluster_color(cluster['cluster_id']), icon='info-sign')
            ).add_to(m)
            
            # Add circle showing radius
            folium.Circle(
                location=cluster['centroid'],
                radius=cluster['radius_km'] * 1000,  # Convert to meters
                color=self._get_cluster_color(cluster['cluster_id']),
                fill=True,
                fill_opacity=0.1
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
    
    def _get_cluster_color(self, cluster_id: int) -> str:
        """
        Get color for a cluster based on its ID.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            Color string
        """
        colors = ['blue', 'green', 'purple', 'orange', 'darkred', 
                 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                 'darkpurple', 'pink', 'lightblue', 'lightgreen']
        
        if cluster_id == -1:
            return 'black'
        
        return colors[cluster_id % len(colors)]
    
    def optimize_delivery_zones(self, 
                              warehouses: List[Dict[str, Any]], 
                              delivery_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimize delivery zones for warehouses.
        
        Args:
            warehouses: List of warehouse dictionaries
            delivery_points: List of delivery point dictionaries
            
        Returns:
            Dictionary with optimized delivery zones
        """
        if not warehouses or not delivery_points:
            return {"status": "error", "message": "Need warehouses and delivery points"}
        
        # Extract coordinates
        warehouse_coords = np.array([[w['latitude'], w['longitude']] for w in warehouses])
        delivery_coords = np.array([[p['latitude'], p['longitude']] for p in delivery_points])
        
        # Calculate distances from each delivery point to each warehouse
        distances = cdist(delivery_coords, warehouse_coords, metric='euclidean')
        
        # Assign each delivery point to nearest warehouse
        nearest_warehouse_indices = np.argmin(distances, axis=1)
        
        # Group delivery points by warehouse
        delivery_zones = defaultdict(list)
        
        for i, warehouse_idx in enumerate(nearest_warehouse_indices):
            warehouse_id = warehouses[warehouse_idx]['id']
            point = delivery_points[i].copy()
            point['assigned_warehouse_id'] = warehouse_id
            point['distance_to_warehouse'] = distances[i, warehouse_idx]
            delivery_zones[warehouse_id].append(point)
        
        # Calculate zone statistics
        zone_stats = []
        
        for warehouse_id, points in delivery_zones.items():
            warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)
            
            if not warehouse:
                continue
            
            # Calculate average and max distance
            distances = [p['distance_to_warehouse'] for p in points]
            avg_distance = sum(distances) / len(distances) if distances else 0
            max_distance = max(distances) if distances else 0
            
            zone_stats.append({
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse.get('name', 'Unknown'),
                "point_count": len(points),
                "average_distance_km": avg_distance * 111,  # Rough conversion to km
                "max_distance_km": max_distance * 111,  # Rough conversion to km
                "coverage_percentage": len(points) / len(delivery_points) * 100
            })
        
        return {
            "status": "success",
            "total_delivery_points": len(delivery_points),
            "warehouse_count": len(warehouses),
            "zones": zone_stats,
            "points": [
                {
                    "latitude": p['latitude'],
                    "longitude": p['longitude'],
                    "assigned_warehouse_id": p['assigned_warehouse_id'],
                    "distance_to_warehouse": p['distance_to_warehouse'] * 111  # Rough conversion to km
                }
                for zone_points in delivery_zones.values()
                for p in zone_points
            ]
        }
    
    def create_zone_map(self, 
                      zone_data: Dict[str, Any], 
                      warehouses: List[Dict[str, Any]]) -> folium.Map:
        """
        Create a map with delivery zones.
        
        Args:
            zone_data: Zone data from optimize_delivery_zones
            warehouses: List of warehouse dictionaries
            
        Returns:
            Folium map with delivery zones
        """
        if zone_data['status'] != 'success' or not warehouses:
            logger.warning("Invalid zone data for map")
            return folium.Map(location=[20.5937, 78.9629], zoom_start=5)  # Default to India
        
        # Create warehouse lookup
        warehouse_lookup = {w['id']: w for w in warehouses}
        
        # Determine center
        points = zone_data['points']
        center = [
            sum(p['latitude'] for p in points) / len(points),
            sum(p['longitude'] for p in points) / len(points)
        ]
        
        # Create map
        m = folium.Map(location=center, zoom_start=11)
        
        # Create feature groups for each zone
        zone_groups = {}
        
        for point in points:
            warehouse_id = point['assigned_warehouse_id']
            
            # Add to appropriate zone group
            if warehouse_id not in zone_groups:
                warehouse = warehouse_lookup.get(warehouse_id, {})
                zone_name = warehouse.get('name', f"Zone {warehouse_id}")
                zone_groups[warehouse_id] = folium.FeatureGroup(name=zone_name)
                m.add_child(zone_groups[warehouse_id])
            
            # Add marker to zone group
            folium.CircleMarker(
                location=[point['latitude'], point['longitude']],
                radius=3,
                color=self._get_cluster_color(hash(warehouse_id) % 14),  # Use hash for consistent colors
                fill=True,
                fill_opacity=0.7
            ).add_to(zone_groups[warehouse_id])
        
        # Add warehouses
        for warehouse in warehouses:
            folium.Marker(
                location=[warehouse['latitude'], warehouse['longitude']],
                popup=warehouse['name'],
                icon=folium.Icon(color='red', icon='industry', prefix='fa')
            ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
