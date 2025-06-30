"""
Inventory optimization module for the warehouse management system.
Provides functions for optimizing inventory levels based on historical demand.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def optimize_inventory_levels(purchase_data: List[Dict[str, Any]],
                             inventory_data: List[Dict[str, Any]],
                             product_data: List[Dict[str, Any]],
                             config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize inventory levels based on historical demand.
    
    Args:
        purchase_data: List of purchase event dictionaries
        inventory_data: List of inventory item dictionaries
        product_data: List of product dictionaries
        config: Optimization configuration
        
    Returns:
        Dictionary with optimization results
    """
    logger.info("Optimizing inventory levels")
    
    # Convert to DataFrames
    purchases_df = pd.DataFrame(purchase_data)
    inventory_df = pd.DataFrame(inventory_data)
    products_df = pd.DataFrame(product_data)
    
    # Check if DataFrames are empty
    if purchases_df.empty or inventory_df.empty or products_df.empty:
        logger.warning("Not enough data for inventory optimization")
        return {
            "status": "error",
            "message": "Not enough data for inventory optimization",
            "recommendations": []
        }
    
    # Convert timestamp to datetime if it's a string
    if 'timestamp' in purchases_df.columns and isinstance(purchases_df['timestamp'].iloc[0], str):
        purchases_df['timestamp'] = pd.to_datetime(purchases_df['timestamp'])
    
    # Add date and extract time components
    purchases_df['date'] = purchases_df['timestamp'].dt.date
    purchases_df['day_of_week'] = purchases_df['timestamp'].dt.dayofweek
    purchases_df['hour'] = purchases_df['timestamp'].dt.hour
    
    # Create product lookup dictionary
    product_lookup = {product['id']: product for product in product_data}
    
    # Calculate demand statistics by product and warehouse
    demand_stats = calculate_demand_statistics(purchases_df)
    
    # Calculate safety stock levels
    safety_stocks = calculate_safety_stock(
        demand_stats=demand_stats,
        products_df=products_df,
        config=config
    )
    
    # Calculate reorder points and optimal order quantities
    inventory_recommendations = calculate_inventory_recommendations(
        demand_stats=demand_stats,
        safety_stocks=safety_stocks,
        inventory_df=inventory_df,
        products_df=products_df,
        config=config
    )
    
    # Format recommendations
    formatted_recommendations = []
    for rec in inventory_recommendations:
        product_id = rec['product_id']
        product = product_lookup.get(product_id, {})
        product_name = product.get('name', 'Unknown Product')
        
        formatted_recommendations.append({
            'warehouse_id': rec['warehouse_id'],
            'product_id': product_id,
            'product_name': product_name,
            'current_stock': rec['current_stock'],
            'min_threshold': rec['min_threshold'],
            'max_capacity': rec['max_capacity'],
            'recommended_min': rec['recommended_min'],
            'recommended_max': rec['recommended_max'],
            'safety_stock': rec['safety_stock'],
            'reorder_point': rec['reorder_point'],
            'optimal_order_qty': rec['optimal_order_qty'],
            'avg_daily_demand': rec['avg_daily_demand'],
            'demand_variability': rec['demand_variability'],
            'shelf_life_days': rec.get('shelf_life_days', 0),
            'priority': rec['priority']
        })
    
    # Sort by priority
    formatted_recommendations.sort(key=lambda x: (
        0 if x['priority'] == 'high' else (1 if x['priority'] == 'medium' else 2),
        x['warehouse_id'],
        x['product_name']
    ))
    
    return {
        "status": "success",
        "message": "Inventory optimization completed",
        "recommendations": formatted_recommendations,
        "summary": {
            "total_items": len(formatted_recommendations),
            "high_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'high'),
            "medium_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'medium'),
            "low_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'low')
        }
    }

def calculate_demand_statistics(purchases_df: pd.DataFrame) -> Dict[Tuple[str, str], Dict[str, float]]:
    """
    Calculate demand statistics by product and warehouse.
    
    Args:
        purchases_df: DataFrame of purchase events
        
    Returns:
        Dictionary with demand statistics
    """
    # Group by date, warehouse, and product
    daily_demand = purchases_df.groupby(['date', 'warehouse_fulfilled', 'product_id'])['quantity'].sum().reset_index()
    
    # Calculate statistics by warehouse and product
    demand_stats = {}
    
    for (warehouse_id, product_id), group in daily_demand.groupby(['warehouse_fulfilled', 'product_id']):
        # Calculate statistics
        avg_daily_demand = group['quantity'].mean()
        std_daily_demand = group['quantity'].std()
        max_daily_demand = group['quantity'].max()
        
        # Handle case where std is NaN (only one data point)
        if pd.isna(std_daily_demand):
            std_daily_demand = avg_daily_demand * 0.5  # Assume 50% variability
        
        # Calculate coefficient of variation
        cv = std_daily_demand / avg_daily_demand if avg_daily_demand > 0 else 0
        
        # Store statistics
        demand_stats[(warehouse_id, product_id)] = {
            'avg_daily_demand': avg_daily_demand,
            'std_daily_demand': std_daily_demand,
            'max_daily_demand': max_daily_demand,
            'coefficient_of_variation': cv,
            'num_data_points': len(group)
        }
    
    return demand_stats

def calculate_safety_stock(demand_stats: Dict[Tuple[str, str], Dict[str, float]],
                          products_df: pd.DataFrame,
                          config: Dict[str, Any]) -> Dict[Tuple[str, str], float]:
    """
    Calculate safety stock levels based on demand variability.
    
    Args:
        demand_stats: Dictionary with demand statistics
        products_df: DataFrame of products
        config: Optimization configuration
        
    Returns:
        Dictionary with safety stock levels
    """
    # Get service level factor (z-score)
    service_level = config.get('service_level', 0.95)
    z_score = {
        0.90: 1.28,
        0.95: 1.65,
        0.98: 2.05,
        0.99: 2.33
    }.get(service_level, 1.65)
    
    # Create product lookup for shelf life
    product_shelf_life = {}
    if 'id' in products_df.columns and 'shelf_life_days' in products_df.columns:
        for _, row in products_df.iterrows():
            product_shelf_life[row['id']] = row['shelf_life_days']
    
    # Calculate safety stock for each product-warehouse pair
    safety_stocks = {}
    
    for (warehouse_id, product_id), stats in demand_stats.items():
        # Get lead time (days to replenish)
        lead_time = config.get('lead_time_days', 2)
        
        # Calculate safety stock
        # Safety Stock = Z × σ × √(Lead Time)
        safety_stock = z_score * stats['std_daily_demand'] * np.sqrt(lead_time)
        
        # Adjust for shelf life if available
        shelf_life = product_shelf_life.get(product_id, 30)  # Default to 30 days
        
        # Cap safety stock at a reasonable level based on shelf life
        max_safety_stock = stats['avg_daily_demand'] * min(shelf_life / 2, 14)  # Cap at 14 days or half shelf life
        safety_stock = min(safety_stock, max_safety_stock)
        
        # Ensure minimum safety stock
        min_safety_stock = stats['avg_daily_demand'] * config.get('min_safety_days', 1)
        safety_stock = max(safety_stock, min_safety_stock)
        
        # Store safety stock
        safety_stocks[(warehouse_id, product_id)] = safety_stock
    
    return safety_stocks

def calculate_inventory_recommendations(demand_stats: Dict[Tuple[str, str], Dict[str, float]],
                                      safety_stocks: Dict[Tuple[str, str], float],
                                      inventory_df: pd.DataFrame,
                                      products_df: pd.DataFrame,
                                      config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculate inventory recommendations.
    
    Args:
        demand_stats: Dictionary with demand statistics
        safety_stocks: Dictionary with safety stock levels
        inventory_df: DataFrame of inventory items
        products_df: DataFrame of products
        config: Optimization configuration
        
    Returns:
        List of inventory recommendations
    """
    # Create product lookup
    product_lookup = {}
    if 'id' in products_df.columns:
        for _, row in products_df.iterrows():
            product_info = {col: row[col] for col in products_df.columns}
            product_lookup[row['id']] = product_info
    
    # Create inventory lookup
    inventory_lookup = {}
    for _, row in inventory_df.iterrows():
        key = (row['warehouse_id'], row['product_id'])
        inventory_lookup[key] = {
            'current_stock': row['current_stock'],
            'min_threshold': row['min_threshold'],
            'max_capacity': row['max_capacity']
        }
    
    # Calculate recommendations
    recommendations = []
    
    for (warehouse_id, product_id), stats in demand_stats.items():
        # Get inventory data
        inventory = inventory_lookup.get((warehouse_id, product_id), {
            'current_stock': 0,
            'min_threshold': 0,
            'max_capacity': 1000  # Default capacity
        })
        
        # Get product data
        product = product_lookup.get(product_id, {})
        
        # Get safety stock
        safety_stock = safety_stocks.get((warehouse_id, product_id), 0)
        
        # Get lead time
        lead_time = config.get('lead_time_days', 2)
        
        # Calculate reorder point
        # Reorder Point = Average Daily Demand × Lead Time + Safety Stock
        reorder_point = (stats['avg_daily_demand'] * lead_time) + safety_stock
        
        # Calculate Economic Order Quantity (EOQ)
        # Simple approximation: 7-14 days of average demand
        order_days = config.get('order_days', 10)
        optimal_order_qty = stats['avg_daily_demand'] * order_days
        
        # Adjust for max capacity
        max_capacity = inventory['max_capacity']
        optimal_order_qty = min(optimal_order_qty, max_capacity - reorder_point)
        
        # Calculate recommended min and max
        recommended_min = reorder_point
        recommended_max = reorder_point + optimal_order_qty
        
        # Ensure recommended values are within capacity
        recommended_min = min(recommended_min, max_capacity * 0.8)
        recommended_max = min(recommended_max, max_capacity)
        
        # Determine priority
        current_stock = inventory['current_stock']
        days_of_supply = current_stock / stats['avg_daily_demand'] if stats['avg_daily_demand'] > 0 else 30
        
        if days_of_supply < lead_time:
            priority = 'high'
        elif days_of_supply < lead_time + 3:
            priority = 'medium'
        else:
            priority = 'low'
        
        # Create recommendation
        recommendation = {
            'warehouse_id': warehouse_id,
            'product_id': product_id,
            'current_stock': inventory['current_stock'],
            'min_threshold': inventory['min_threshold'],
            'max_capacity': inventory['max_capacity'],
            'recommended_min': int(recommended_min),
            'recommended_max': int(recommended_max),
            'safety_stock': int(safety_stock),
            'reorder_point': int(reorder_point),
            'optimal_order_qty': int(optimal_order_qty),
            'avg_daily_demand': round(stats['avg_daily_demand'], 2),
            'demand_variability': round(stats['coefficient_of_variation'], 2),
            'priority': priority
        }
        
        # Add shelf life if available
        if 'shelf_life_days' in product:
            recommendation['shelf_life_days'] = product['shelf_life_days']
        
        recommendations.append(recommendation)
    
    return recommendations
