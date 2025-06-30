"""
Database utility functions for the warehouse management system.
"""
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from src.config.settings import DATABASE_URI
from src.models.database import engine

logger = logging.getLogger(__name__)

def execute_raw_sql(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute raw SQL query and return results as a list of dictionaries.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of dictionaries with query results
    """
    try:
        # Extract database path from SQLAlchemy URI
        db_path = DATABASE_URI.replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Execute query
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = [dict(row) for row in rows]
        
        # Close connection
        conn.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing raw SQL: {e}")
        raise

def execute_spatial_query(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a spatial SQL query using SpatiaLite.
    
    Args:
        query: SQL query string with spatial functions
        params: Query parameters
        
    Returns:
        List of dictionaries with query results
    """
    try:
        # Extract database path from SQLAlchemy URI
        db_path = DATABASE_URI.replace('sqlite:///', '')
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        conn.enable_load_extension(True)
        
        # Try to load SpatiaLite extension
        try:
            conn.execute("SELECT load_extension('mod_spatialite')")
        except sqlite3.OperationalError:
            logger.warning("Could not load mod_spatialite, trying libspatialite")
            try:
                conn.execute("SELECT load_extension('libspatialite')")
            except sqlite3.OperationalError:
                logger.error("Could not load SpatiaLite extension")
                raise
        
        conn.row_factory = sqlite3.Row
        
        # Execute query
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        result = [dict(row) for row in rows]
        
        # Close connection
        conn.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Error executing spatial query: {e}")
        raise

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in kilometers
    """
    query = """
    SELECT ST_Distance(
        ST_Transform(ST_SetSRID(ST_MakePoint(:lon1, :lat1), 4326), 3857),
        ST_Transform(ST_SetSRID(ST_MakePoint(:lon2, :lat2), 4326), 3857)
    ) / 1000.0 AS distance_km
    """
    
    params = {
        'lat1': lat1,
        'lon1': lon1,
        'lat2': lat2,
        'lon2': lon2
    }
    
    try:
        result = execute_spatial_query(query, params)
        return result[0]['distance_km']
    except Exception:
        # Fallback to Python implementation if SpatiaLite fails
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        # Earth radius in kilometers
        radius = 6371.0
        
        # Calculate distance
        distance = radius * c
        
        return distance

def get_nearest_warehouses(lat: float, lon: float, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Find nearest warehouses to a given location.
    
    Args:
        lat: Latitude
        lon: Longitude
        limit: Maximum number of warehouses to return
        
    Returns:
        List of dictionaries with warehouse information and distance
    """
    query = """
    SELECT w.id, w.name, w.area, w.latitude, w.longitude,
           ST_Distance(
               ST_Transform(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326), 3857),
               ST_Transform(ST_SetSRID(ST_MakePoint(w.longitude, w.latitude), 4326), 3857)
           ) / 1000.0 AS distance_km
    FROM warehouses w
    ORDER BY distance_km
    LIMIT :limit
    """
    
    params = {
        'lat': lat,
        'lon': lon,
        'limit': limit
    }
    
    try:
        return execute_spatial_query(query, params)
    except Exception as e:
        logger.error(f"Error in spatial query, falling back to Python implementation: {e}")
        
        # Fallback to Python implementation
        from src.models.warehouse import Warehouse
        
        with Session(engine) as session:
            warehouses = session.query(Warehouse).all()
            
            # Calculate distances
            warehouse_distances = []
            for warehouse in warehouses:
                distance = calculate_distance(lat, lon, warehouse.latitude, warehouse.longitude)
                warehouse_distances.append({
                    'id': warehouse.id,
                    'name': warehouse.name,
                    'area': warehouse.area,
                    'latitude': warehouse.latitude,
                    'longitude': warehouse.longitude,
                    'distance_km': distance
                })
            
            # Sort by distance and limit results
            warehouse_distances.sort(key=lambda x: x['distance_km'])
            return warehouse_distances[:limit]

def check_database_integrity() -> Tuple[bool, List[str]]:
    """
    Check database integrity and return status and issues.
    
    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []
    
    try:
        # Extract database path from SQLAlchemy URI
        db_path = DATABASE_URI.replace('sqlite:///', '')
        
        # Check if database file exists
        if not Path(db_path).exists():
            issues.append(f"Database file does not exist: {db_path}")
            return False, issues
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        if integrity_result != "ok":
            issues.append(f"Database integrity check failed: {integrity_result}")
        
        # Check foreign keys
        cursor.execute("PRAGMA foreign_key_check")
        foreign_key_issues = cursor.fetchall()
        if foreign_key_issues:
            for issue in foreign_key_issues:
                issues.append(f"Foreign key violation: {issue}")
        
        # Close connection
        conn.close()
        
        return len(issues) == 0, issues
    
    except Exception as e:
        issues.append(f"Error checking database integrity: {e}")
        return False, issues
