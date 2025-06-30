"""
Warehouse allocation optimization module for the warehouse management system.
Provides functions for optimizing product allocation across warehouses.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)

def optimize_allocation(warehouse_data: List[Dict[str, Any]],
                       purchase_data: List[Dict[str, Any]],
                       pincode_data: List[Dict[str, Any]],
                       config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize product allocation across warehouses.
    
    Args:
        warehouse_data: List of warehouse dictionaries
        purchase_data: List of purchase event dictionaries
        pincode_data: List of pincode mapping dictionaries
        config: Optimization configuration
        
    Returns:
        Dictionary with optimization results
    """
    logger.info("Optimizing warehouse allocation")
    
    # Convert to DataFrames
    warehouses_df = pd.DataFrame(warehouse_data)
    purchases_df = pd.DataFrame(purchase_data)
    pincodes_df = pd.DataFrame(pincode_data)
    
    # Check if DataFrames are empty
    if warehouses_df.empty or purchases_df.empty or pincodes_df.empty:
        logger.warning("Not enough data for warehouse allocation optimization")
        return {
            "status": "error",
            "message": "Not enough data for warehouse allocation optimization",
            "recommendations": []
        }
    
    # Convert timestamp to datetime if it's a string
    if 'timestamp' in purchases_df.columns and isinstance(purchases_df['timestamp'].iloc[0], str):
        purchases_df['timestamp'] = pd.to_datetime(purchases_df['timestamp'])
    
    # Create pincode lookup for coordinates
    pincode_coords = {}
    for _, row in pincodes_df.iterrows():
        pincode_coords[row['pincode']] = (row['latitude'], row['longitude'])
    
    # Create warehouse lookup for coordinates and capacity
    warehouse_info = {}
    for _, row in warehouses_df.iterrows():
        warehouse_info[row['id']] = {
            'name': row['name'],
            'coords': (row['latitude'], row['longitude']),
            'capacity': row['capacity'],
            'available_capacity': row['capacity']  # Will be updated later
        }
    
    # Calculate demand by product and pincode
    product_pincode_demand = calculate_product_pincode_demand(purchases_df)
    
    # Calculate warehouse distances to pincodes
    warehouse_pincode_distances = calculate_warehouse_pincode_distances(
        warehouses_df=warehouses_df,
        pincodes_df=pincodes_df
    )
    
    # Calculate optimal warehouse allocation
    allocation_recommendations = calculate_optimal_allocation(
        product_pincode_demand=product_pincode_demand,
        warehouse_pincode_distances=warehouse_pincode_distances,
        warehouse_info=warehouse_info,
        config=config
    )
    
    # Format recommendations
    formatted_recommendations = []
    for product_id, allocations in allocation_recommendations.items():
        for allocation in allocations:
            formatted_recommendations.append({
                'product_id': product_id,
                'warehouse_id': allocation['warehouse_id'],
                'warehouse_name': warehouse_info[allocation['warehouse_id']]['name'],
                'allocation_percentage': allocation['allocation_percentage'],
                'estimated_demand': allocation['estimated_demand'],
                'primary_area': allocation['primary_area'],
                'distance_score': allocation['distance_score']
            })
    
    # Sort by product_id and allocation_percentage
    formatted_recommendations.sort(key=lambda x: (x['product_id'], -x['allocation_percentage']))
    
    return {
        "status": "success",
        "message": "Warehouse allocation optimization completed",
        "recommendations": formatted_recommendations,
        "summary": {
            "total_products": len(allocation_recommendations),
            "total_allocations": len(formatted_recommendations),
            "warehouses_used": len(set(rec['warehouse_id'] for rec in formatted_recommendations))
        }
    }

def calculate_product_pincode_demand(purchases_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate demand by product and pincode.
    
    Args:
        purchases_df: DataFrame of purchase events
        
    Returns:
        Dictionary with demand by product and pincode
    """
    # Group by product and pincode
    product_pincode_demand = defaultdict(lambda: defaultdict(float))
    
    # Check if DataFrame has required columns
    if not all(col in purchases_df.columns for col in ['product_id', 'customer_pincode', 'quantity']):
        logger.warning("Purchase data missing required columns for demand calculation")
        return {}
    
    # Calculate demand
    for _, row in purchases_df.iterrows():
        product_id = row['product_id']
        pincode = row['customer_pincode']
        quantity = row['quantity']
        
        product_pincode_demand[product_id][pincode] += quantity
    
    return product_pincode_demand

def calculate_warehouse_pincode_distances(warehouses_df: pd.DataFrame,
                                        pincodes_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate distances between warehouses and pincodes.
    
    Args:
        warehouses_df: DataFrame of warehouses
        pincodes_df: DataFrame of pincode mappings
        
    Returns:
        Dictionary with distances between warehouses and pincodes
    """
    # Create distance matrix
    warehouse_coords = warehouses_df[['latitude', 'longitude']].values
    pincode_coords = pincodes_df[['latitude', 'longitude']].values
    
    # Calculate Euclidean distances (this is a simplification, in reality we'd use Haversine)
    distances = cdist(warehouse_coords, pincode_coords, metric='euclidean')
    
    # Convert to dictionary
    warehouse_pincode_distances = {}
    
    for i, warehouse_id in enumerate(warehouses_df['id']):
        warehouse_pincode_distances[warehouse_id] = {}
        
        for j, pincode in enumerate(pincodes_df['pincode']):
            warehouse_pincode_distances[warehouse_id][pincode] = distances[i, j]
    
    return warehouse_pincode_distances

def calculate_optimal_allocation(product_pincode_demand: Dict[str, Dict[str, float]],
                               warehouse_pincode_distances: Dict[str, Dict[str, float]],
                               warehouse_info: Dict[str, Dict[str, Any]],
                               config: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate optimal warehouse allocation.
    
    Args:
        product_pincode_demand: Dictionary with demand by product and pincode
        warehouse_pincode_distances: Dictionary with distances between warehouses and pincodes
        warehouse_info: Dictionary with warehouse information
        config: Optimization configuration
        
    Returns:
        Dictionary with optimal warehouse allocation
    """
    # Initialize allocation recommendations
    allocation_recommendations = {}
    
    # Process each product
    for product_id, pincode_demand in product_pincode_demand.items():
        # Calculate total demand for this product
        total_demand = sum(pincode_demand.values())
        
        if total_demand == 0:
            continue
        
        # Calculate warehouse scores based on distance to demand
        warehouse_scores = {}
        warehouse_demand_areas = {}
        
        for warehouse_id, distances in warehouse_pincode_distances.items():
            # Calculate weighted score based on demand and distance
            score = 0
            demand_by_area = defaultdict(float)
            
            for pincode, demand in pincode_demand.items():
                if pincode in distances:
                    # Convert distance to a score (closer is better)
                    distance = distances[pincode]
                    distance_score = 1 / (1 + distance)
                    
                    # Weight by demand
                    score += demand * distance_score
                    
                    # Track demand by area
                    area = pincode[:3]  # Simplified: first 3 digits of pincode as area
                    demand_by_area[area] += demand
            
            # Normalize score by total demand
            if total_demand > 0:
                score /= total_demand
            
            # Find primary area (area with highest demand)
            primary_area = max(demand_by_area.items(), key=lambda x: x[1])[0] if demand_by_area else None
            
            warehouse_scores[warehouse_id] = score
            warehouse_demand_areas[warehouse_id] = primary_area
        
        # Sort warehouses by score
        sorted_warehouses = sorted(warehouse_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate to top warehouses
        max_warehouses = config.get('max_warehouses_per_product', 3)
        allocations = []
        
        remaining_demand = total_demand
        for i, (warehouse_id, score) in enumerate(sorted_warehouses[:max_warehouses]):
            # Calculate allocation percentage
            if i == max_warehouses - 1 or i == len(sorted_warehouses) - 1:
                # Last warehouse gets remaining demand
                allocation_pct = 100 * (remaining_demand / total_demand)
                estimated_demand = remaining_demand
            else:
                # Allocate based on score ratio
                total_score = sum(s for _, s in sorted_warehouses[:max_warehouses])
                if total_score > 0:
                    allocation_pct = 100 * (score / total_score)
                    estimated_demand = total_demand * (score / total_score)
                else:
                    allocation_pct = 100 / max_warehouses
                    estimated_demand = total_demand / max_warehouses
                
                remaining_demand -= estimated_demand
            
            # Add allocation
            allocations.append({
                'warehouse_id': warehouse_id,
                'allocation_percentage': round(allocation_pct, 2),
                'estimated_demand': round(estimated_demand, 2),
                'primary_area': warehouse_demand_areas[warehouse_id],
                'distance_score': round(score, 4)
            })
        
        allocation_recommendations[product_id] = allocations
    
    return allocation_recommendations
