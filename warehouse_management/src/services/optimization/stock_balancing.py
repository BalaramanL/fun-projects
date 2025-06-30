"""
Stock balancing module for the warehouse management system.
Provides functions for balancing stock levels across warehouses.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def balance_stock(warehouse_data: List[Dict[str, Any]],
                 inventory_data: List[Dict[str, Any]],
                 product_data: List[Dict[str, Any]],
                 purchase_data: List[Dict[str, Any]],
                 config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Balance stock levels across warehouses.
    
    Args:
        warehouse_data: List of warehouse dictionaries
        inventory_data: List of inventory item dictionaries
        product_data: List of product dictionaries
        purchase_data: List of purchase event dictionaries
        config: Optimization configuration
        
    Returns:
        Dictionary with stock balancing results
    """
    logger.info("Balancing stock across warehouses")
    
    # Convert to DataFrames
    warehouses_df = pd.DataFrame(warehouse_data)
    inventory_df = pd.DataFrame(inventory_data)
    products_df = pd.DataFrame(product_data)
    purchases_df = pd.DataFrame(purchase_data)
    
    # Check if DataFrames are empty
    if warehouses_df.empty or inventory_df.empty or products_df.empty:
        logger.warning("Not enough data for stock balancing")
        return {
            "status": "error",
            "message": "Not enough data for stock balancing",
            "transfers": []
        }
    
    # Create product lookup
    product_lookup = {product['id']: product for product in product_data}
    
    # Create warehouse lookup
    warehouse_lookup = {warehouse['id']: warehouse for warehouse in warehouse_data}
    
    # Calculate demand by product and warehouse
    product_warehouse_demand = calculate_product_warehouse_demand(purchases_df)
    
    # Calculate stock imbalances
    stock_imbalances = calculate_stock_imbalances(
        inventory_df=inventory_df,
        product_warehouse_demand=product_warehouse_demand,
        product_lookup=product_lookup,
        warehouse_lookup=warehouse_lookup
    )
    
    # Generate transfer recommendations
    transfer_recommendations = generate_transfer_recommendations(
        stock_imbalances=stock_imbalances,
        inventory_df=inventory_df,
        product_lookup=product_lookup,
        warehouse_lookup=warehouse_lookup,
        config=config
    )
    
    # Format recommendations
    formatted_recommendations = []
    for transfer in transfer_recommendations:
        product_id = transfer['product_id']
        product = product_lookup.get(product_id, {})
        product_name = product.get('name', 'Unknown Product')
        
        source_id = transfer['source_warehouse_id']
        source = warehouse_lookup.get(source_id, {})
        source_name = source.get('name', 'Unknown Warehouse')
        
        destination_id = transfer['destination_warehouse_id']
        destination = warehouse_lookup.get(destination_id, {})
        destination_name = destination.get('name', 'Unknown Warehouse')
        
        formatted_recommendations.append({
            'product_id': product_id,
            'product_name': product_name,
            'source_warehouse_id': source_id,
            'source_warehouse_name': source_name,
            'destination_warehouse_id': destination_id,
            'destination_warehouse_name': destination_name,
            'quantity': transfer['quantity'],
            'source_before': transfer['source_before'],
            'source_after': transfer['source_after'],
            'destination_before': transfer['destination_before'],
            'destination_after': transfer['destination_after'],
            'reason': transfer['reason'],
            'priority': transfer['priority']
        })
    
    # Sort by priority
    formatted_recommendations.sort(key=lambda x: (
        0 if x['priority'] == 'high' else (1 if x['priority'] == 'medium' else 2),
        x['product_name']
    ))
    
    return {
        "status": "success",
        "message": "Stock balancing completed",
        "transfers": formatted_recommendations,
        "summary": {
            "total_transfers": len(formatted_recommendations),
            "high_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'high'),
            "medium_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'medium'),
            "low_priority": sum(1 for rec in formatted_recommendations if rec['priority'] == 'low'),
            "total_quantity": sum(rec['quantity'] for rec in formatted_recommendations)
        }
    }

def calculate_product_warehouse_demand(purchases_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Calculate demand by product and warehouse.
    
    Args:
        purchases_df: DataFrame of purchase events
        
    Returns:
        Dictionary with demand by product and warehouse
    """
    # Group by product and warehouse
    product_warehouse_demand = defaultdict(lambda: defaultdict(float))
    
    # Check if DataFrame has required columns
    if not all(col in purchases_df.columns for col in ['product_id', 'warehouse_fulfilled', 'quantity']):
        logger.warning("Purchase data missing required columns for demand calculation")
        return {}
    
    # Calculate demand
    for _, row in purchases_df.iterrows():
        product_id = row['product_id']
        warehouse_id = row['warehouse_fulfilled']
        quantity = row['quantity']
        
        product_warehouse_demand[product_id][warehouse_id] += quantity
    
    return product_warehouse_demand

def calculate_stock_imbalances(inventory_df: pd.DataFrame,
                             product_warehouse_demand: Dict[str, Dict[str, float]],
                             product_lookup: Dict[str, Dict[str, Any]],
                             warehouse_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate stock imbalances across warehouses.
    
    Args:
        inventory_df: DataFrame of inventory items
        product_warehouse_demand: Dictionary with demand by product and warehouse
        product_lookup: Dictionary with product information
        warehouse_lookup: Dictionary with warehouse information
        
    Returns:
        Dictionary with stock imbalances by product
    """
    # Group inventory by product and warehouse
    inventory_by_product_warehouse = {}
    
    for _, row in inventory_df.iterrows():
        product_id = row['product_id']
        warehouse_id = row['warehouse_id']
        
        if product_id not in inventory_by_product_warehouse:
            inventory_by_product_warehouse[product_id] = {}
        
        inventory_by_product_warehouse[product_id][warehouse_id] = {
            'current_stock': row['current_stock'],
            'min_threshold': row['min_threshold'],
            'max_capacity': row['max_capacity']
        }
    
    # Calculate imbalances
    stock_imbalances = {}
    
    for product_id, warehouse_inventory in inventory_by_product_warehouse.items():
        # Skip if product is only in one warehouse
        if len(warehouse_inventory) <= 1:
            continue
        
        # Calculate total stock and demand
        total_stock = sum(inv['current_stock'] for inv in warehouse_inventory.values())
        
        # Get demand by warehouse
        warehouse_demand = product_warehouse_demand.get(product_id, {})
        total_demand = sum(warehouse_demand.values())
        
        # Skip if no demand
        if total_demand == 0:
            continue
        
        # Calculate ideal stock distribution based on demand
        ideal_distribution = {}
        for warehouse_id, demand in warehouse_demand.items():
            demand_ratio = demand / total_demand if total_demand > 0 else 0
            ideal_stock = total_stock * demand_ratio
            
            if warehouse_id in warehouse_inventory:
                current_stock = warehouse_inventory[warehouse_id]['current_stock']
                max_capacity = warehouse_inventory[warehouse_id]['max_capacity']
                
                # Calculate imbalance
                imbalance = current_stock - ideal_stock
                
                # Only consider significant imbalances (>10%)
                if abs(imbalance) > max(10, 0.1 * ideal_stock):
                    if product_id not in stock_imbalances:
                        stock_imbalances[product_id] = []
                    
                    stock_imbalances[product_id].append({
                        'warehouse_id': warehouse_id,
                        'current_stock': current_stock,
                        'ideal_stock': ideal_stock,
                        'imbalance': imbalance,
                        'max_capacity': max_capacity,
                        'demand': demand
                    })
    
    return stock_imbalances

def generate_transfer_recommendations(stock_imbalances: Dict[str, List[Dict[str, Any]]],
                                    inventory_df: pd.DataFrame,
                                    product_lookup: Dict[str, Dict[str, Any]],
                                    warehouse_lookup: Dict[str, Dict[str, Any]],
                                    config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate transfer recommendations based on stock imbalances.
    
    Args:
        stock_imbalances: Dictionary with stock imbalances by product
        inventory_df: DataFrame of inventory items
        product_lookup: Dictionary with product information
        warehouse_lookup: Dictionary with warehouse information
        config: Optimization configuration
        
    Returns:
        List of transfer recommendations
    """
    # Initialize transfer recommendations
    transfer_recommendations = []
    
    # Process each product
    for product_id, imbalances in stock_imbalances.items():
        # Skip if not enough warehouses with imbalances
        if len(imbalances) < 2:
            continue
        
        # Sort warehouses by imbalance (descending)
        sorted_imbalances = sorted(imbalances, key=lambda x: x['imbalance'], reverse=True)
        
        # Find warehouses with excess stock (positive imbalance)
        excess_warehouses = [w for w in sorted_imbalances if w['imbalance'] > 0]
        
        # Find warehouses with deficit stock (negative imbalance)
        deficit_warehouses = [w for w in sorted_imbalances if w['imbalance'] < 0]
        
        # Skip if no excess or deficit warehouses
        if not excess_warehouses or not deficit_warehouses:
            continue
        
        # Generate transfers
        for excess in excess_warehouses:
            excess_remaining = excess['imbalance']
            
            for deficit in deficit_warehouses:
                deficit_remaining = abs(deficit['imbalance'])
                
                if excess_remaining <= 0 or deficit_remaining <= 0:
                    continue
                
                # Calculate transfer quantity
                transfer_qty = min(excess_remaining, deficit_remaining)
                
                # Ensure transfer is significant
                min_transfer = config.get('min_transfer_quantity', 10)
                if transfer_qty < min_transfer:
                    continue
                
                # Round to integer
                transfer_qty = int(transfer_qty)
                
                # Check if destination has capacity
                destination_capacity = deficit['max_capacity']
                destination_current = deficit['current_stock']
                
                if destination_current + transfer_qty > destination_capacity:
                    # Adjust transfer quantity to fit capacity
                    transfer_qty = max(0, destination_capacity - destination_current)
                
                if transfer_qty <= 0:
                    continue
                
                # Calculate new stock levels
                source_before = excess['current_stock']
                source_after = source_before - transfer_qty
                
                destination_before = deficit['current_stock']
                destination_after = destination_before + transfer_qty
                
                # Determine priority
                if destination_before < deficit['ideal_stock'] * 0.5:
                    priority = 'high'
                    reason = 'Critical shortage at destination'
                elif source_after < excess['ideal_stock'] * 0.5:
                    priority = 'medium'
                    reason = 'Balancing stock levels'
                else:
                    priority = 'low'
                    reason = 'Optimizing inventory distribution'
                
                # Add transfer recommendation
                transfer_recommendations.append({
                    'product_id': product_id,
                    'source_warehouse_id': excess['warehouse_id'],
                    'destination_warehouse_id': deficit['warehouse_id'],
                    'quantity': transfer_qty,
                    'source_before': source_before,
                    'source_after': source_after,
                    'destination_before': destination_before,
                    'destination_after': destination_after,
                    'reason': reason,
                    'priority': priority
                })
                
                # Update remaining imbalances
                excess_remaining -= transfer_qty
                deficit_remaining -= transfer_qty
                
                # Update current stock for next iteration
                excess['current_stock'] = source_after
                deficit['current_stock'] = destination_after
    
    return transfer_recommendations
