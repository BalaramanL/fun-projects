"""
Inventory simulation module for the warehouse management system.

This module provides functions for simulating inventory changes based on orders and restocking.
"""
import logging
import datetime
import random
import uuid
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

from src.utils.helpers import get_db_session
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory

logger = logging.getLogger(__name__)

def simulate_inventory(config: Dict[str, Any],
                     order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Simulate inventory changes based on orders and restocking.
    
    Args:
        config: Simulation configuration
        order_data: Optional order data from order simulation
        
    Returns:
        Dictionary with simulation results
    """
    logger.info("Simulating inventory changes")
    
    # Load initial inventory data
    inventory_data = _load_inventory()
    products = _load_products()
    warehouses = _load_warehouses()
    
    if not inventory_data or not products or not warehouses:
        return {
            "status": "error",
            "message": "Failed to load required data for simulation",
            "inventory_changes": []
        }
    
    # Create product and warehouse lookups
    product_lookup = {p['id']: p for p in products}
    warehouse_lookup = {w['id']: w for w in warehouses}
    
    # Create inventory lookup by warehouse and product
    inventory_lookup = {}
    for inv in inventory_data:
        warehouse_id = inv['warehouse_id']
        product_id = inv['product_id']
        
        if warehouse_id not in inventory_lookup:
            inventory_lookup[warehouse_id] = {}
        
        inventory_lookup[warehouse_id][product_id] = inv
    
    # Initialize tracking variables
    inventory_changes = []
    stockouts = []
    restocks = []
    
    # Process orders if provided
    if order_data:
        for order in order_data:
            # Skip non-fulfilled orders
            if order['status'] in ['cancelled', 'returned']:
                continue
            
            warehouse_id = order['warehouse_fulfilled']
            order_id = order['id']
            order_time = datetime.datetime.fromisoformat(order['timestamp'])
            
            # Process each item in order
            for item in order['items']:
                product_id = item['product_id']
                quantity = item['quantity']
                
                # Check if we have this product in this warehouse
                if (warehouse_id in inventory_lookup and 
                    product_id in inventory_lookup[warehouse_id]):
                    
                    inv = inventory_lookup[warehouse_id][product_id]
                    current_stock = inv['current_stock']
                    
                    # Check if we have enough stock
                    if current_stock >= quantity:
                        # Update inventory
                        new_stock = current_stock - quantity
                        inv['current_stock'] = new_stock
                        
                        # Record change
                        inventory_changes.append({
                            "id": str(uuid.uuid4()),
                            "warehouse_id": warehouse_id,
                            "product_id": product_id,
                            "order_id": order_id,
                            "change_type": "order_fulfillment",
                            "quantity_change": -quantity,
                            "previous_stock": current_stock,
                            "new_stock": new_stock,
                            "timestamp": order_time.isoformat()
                        })
                        
                        # Check if we need to restock
                        if new_stock <= inv['min_threshold']:
                            # Generate restock event
                            restock_quantity = _calculate_restock_quantity(
                                current_stock=new_stock,
                                min_threshold=inv['min_threshold'],
                                max_capacity=inv['max_capacity'],
                                config=config
                            )
                            
                            # Apply restock delay
                            restock_delay_days = random.uniform(
                                config.get('min_restock_delay_days', 1),
                                config.get('max_restock_delay_days', 3)
                            )
                            restock_time = order_time + datetime.timedelta(days=restock_delay_days)
                            
                            # Update inventory
                            restock_new_stock = new_stock + restock_quantity
                            inv['current_stock'] = restock_new_stock
                            
                            # Record restock
                            restocks.append({
                                "id": str(uuid.uuid4()),
                                "warehouse_id": warehouse_id,
                                "product_id": product_id,
                                "quantity": restock_quantity,
                                "previous_stock": new_stock,
                                "new_stock": restock_new_stock,
                                "timestamp": restock_time.isoformat(),
                                "reason": "below_threshold"
                            })
                            
                            # Record change
                            inventory_changes.append({
                                "id": str(uuid.uuid4()),
                                "warehouse_id": warehouse_id,
                                "product_id": product_id,
                                "order_id": None,
                                "change_type": "restock",
                                "quantity_change": restock_quantity,
                                "previous_stock": new_stock,
                                "new_stock": restock_new_stock,
                                "timestamp": restock_time.isoformat()
                            })
                    else:
                        # Stockout occurred
                        stockouts.append({
                            "warehouse_id": warehouse_id,
                            "product_id": product_id,
                            "order_id": order_id,
                            "requested_quantity": quantity,
                            "available_quantity": current_stock,
                            "timestamp": order_time.isoformat()
                        })
    
    # Apply random inventory adjustments
    if config.get('simulate_random_adjustments', True):
        inventory_adjustments = _simulate_random_adjustments(
            inventory_lookup=inventory_lookup,
            config=config
        )
        inventory_changes.extend(inventory_adjustments)
    
    # Calculate final inventory state
    final_inventory = []
    for warehouse_id, products in inventory_lookup.items():
        for product_id, inv in products.items():
            final_inventory.append({
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_lookup.get(warehouse_id, {}).get('name', 'Unknown'),
                "product_id": product_id,
                "product_name": product_lookup.get(product_id, {}).get('name', 'Unknown'),
                "current_stock": inv['current_stock'],
                "min_threshold": inv['min_threshold'],
                "max_capacity": inv['max_capacity']
            })
    
    # Calculate metrics
    total_stock = sum(inv['current_stock'] for inv in final_inventory)
    total_capacity = sum(inv['max_capacity'] for inv in final_inventory)
    capacity_utilization = total_stock / total_capacity if total_capacity > 0 else 0
    
    stockout_rate = len(stockouts) / len(order_data) if order_data else 0
    
    return {
        "status": "success",
        "inventory_changes": inventory_changes,
        "stockouts": stockouts,
        "restocks": restocks,
        "final_inventory": final_inventory,
        "summary": {
            "total_changes": len(inventory_changes),
            "total_stockouts": len(stockouts),
            "total_restocks": len(restocks),
            "total_stock": total_stock,
            "total_capacity": total_capacity,
            "capacity_utilization": capacity_utilization,
            "stockout_rate": stockout_rate
        }
    }

def _load_inventory() -> List[Dict[str, Any]]:
    """
    Load inventory data from database.
    
    Returns:
        List of inventory dictionaries
    """
    try:
        with get_db_session() as session:
            inventory = []
            for item in session.query(Inventory).all():
                # Skip None items
                if item is None:
                    logger.warning("Skipping None inventory item")
                    continue
                    
                # Verify all required attributes exist
                try:
                    inventory.append({
                        "id": item.inventory_id,  # Always use inventory_id as the primary key
                        "warehouse_id": item.warehouse_id,
                        "product_id": item.product_id,
                        "current_stock": item.current_stock,
                        "min_threshold": item.min_threshold,
                        "max_capacity": item.max_capacity
                    })
                except AttributeError as ae:
                    logger.error(f"Inventory item missing required attribute: {str(ae)}")
                    continue
            return inventory
    except Exception as e:
        logger.error(f"Error loading inventory: {str(e)}")
        return []

def _load_products() -> List[Dict[str, Any]]:
    """
    Load products from database.
    
    Returns:
        List of product dictionaries
    """
    try:
        with get_db_session() as session:
            products = []
            for product in session.query(Product).all():
                products.append({
                    "id": product.product_id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "weight_grams": product.weight_grams  # Use weight_grams instead of weight
                })
            return products
    except Exception as e:
        logger.error(f"Error loading products: {str(e)}")
        return []

def _load_warehouses() -> List[Dict[str, Any]]:
    """
    Load warehouses from database.
    
    Returns:
        List of warehouse dictionaries
    """
    try:
        with get_db_session() as session:
            warehouses = []
            for warehouse in session.query(Warehouse).all():
                warehouses.append({
                    "id": warehouse.warehouse_id,
                    "name": warehouse.name,
                    "latitude": warehouse.latitude,
                    "longitude": warehouse.longitude,
                    "capacity": warehouse.capacity_sqm,  # Keep capacity_sqm but map to capacity in dict
                    "capacity_sqm": warehouse.capacity_sqm  # Also include the original field name
                })
            return warehouses
    except Exception as e:
        logger.error(f"Error loading warehouses: {str(e)}")
        return []

def _calculate_restock_quantity(current_stock: int,
                              min_threshold: int,
                              max_capacity: int,
                              config: Dict[str, Any]) -> int:
    """
    Calculate quantity to restock.
    
    Args:
        current_stock: Current stock level
        min_threshold: Minimum threshold
        max_capacity: Maximum capacity
        config: Simulation configuration
        
    Returns:
        Quantity to restock
    """
    # Default to restocking to 80% of capacity
    target_fill_percentage = config.get('restock_target_fill_percentage', 80)
    target_stock = int(max_capacity * target_fill_percentage / 100)
    
    # Calculate restock quantity
    restock_quantity = target_stock - current_stock
    
    # Ensure we don't exceed capacity
    restock_quantity = min(restock_quantity, max_capacity - current_stock)
    
    # Ensure we restock at least a minimum amount
    min_restock = config.get('min_restock_quantity', 10)
    restock_quantity = max(restock_quantity, min_restock)
    
    # Final check to not exceed capacity
    restock_quantity = min(restock_quantity, max_capacity - current_stock)
    
    return max(0, restock_quantity)

def _simulate_random_adjustments(inventory_lookup: Dict[str, Dict[str, Dict[str, Any]]],
                               config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Simulate random inventory adjustments (e.g., damages, theft, counting errors).
    
    Args:
        inventory_lookup: Inventory lookup by warehouse and product
        config: Simulation configuration
        
    Returns:
        List of inventory change dictionaries
    """
    adjustments = []
    
    # Get adjustment parameters
    adjustment_probability = config.get('adjustment_probability', 0.05)
    max_adjustment_percentage = config.get('max_adjustment_percentage', 5)
    
    # Set simulation timeframe
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    end_date = datetime.datetime.now()
    
    # Process each inventory item
    for warehouse_id, products in inventory_lookup.items():
        for product_id, inv in products.items():
            # Randomly decide if this item gets an adjustment
            if random.random() < adjustment_probability:
                # Generate random adjustment (both positive and negative)
                max_adjustment = int(inv['current_stock'] * max_adjustment_percentage / 100)
                adjustment = random.randint(-max_adjustment, max_adjustment)
                
                # Skip if adjustment is zero
                if adjustment == 0:
                    continue
                
                # Generate random timestamp
                random_time = start_date + datetime.timedelta(
                    seconds=random.randint(0, int((end_date - start_date).total_seconds()))
                )
                
                # Apply adjustment
                previous_stock = inv['current_stock']
                new_stock = previous_stock + adjustment
                
                # Ensure stock doesn't go negative or exceed capacity
                new_stock = max(0, min(new_stock, inv['max_capacity']))
                
                # Recalculate actual adjustment
                actual_adjustment = new_stock - previous_stock
                
                # Skip if no actual change
                if actual_adjustment == 0:
                    continue
                
                # Update inventory
                inv['current_stock'] = new_stock
                
                # Determine reason
                if actual_adjustment < 0:
                    reason = random.choice(['damage', 'theft', 'counting_error', 'expiry'])
                else:
                    reason = random.choice(['counting_error', 'found_items', 'return'])
                
                # Record adjustment
                adjustments.append({
                    "id": str(uuid.uuid4()),
                    "warehouse_id": warehouse_id,
                    "product_id": product_id,
                    "order_id": None,
                    "change_type": "adjustment",
                    "quantity_change": actual_adjustment,
                    "previous_stock": previous_stock,
                    "new_stock": new_stock,
                    "timestamp": random_time.isoformat(),
                    "reason": reason
                })
    
    return adjustments


class InventorySimulation:
    """
    Class for simulating inventory changes and management.
    
    This class provides methods to simulate inventory changes based on orders,
    restocking, and other events.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the inventory simulation with optional configuration.
        
        Args:
            config: Configuration dictionary for the simulation
        """
        self.config = config or {
            'restock_target_fill_percentage': 80,
            'min_restock_quantity': 10,
            'adjustment_probability': 0.05,
            'max_adjustment_percentage': 5
        }
    
    def simulate(self, order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run the inventory simulation with optional order data.
        
        Args:
            order_data: Optional order data from order simulation
            
        Returns:
            Dictionary with simulation results
        """
        return simulate_inventory(self.config, order_data)
    
    def create_and_run_custom_scenario(self, scenario_config: Dict[str, Any], 
                                      order_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create and run a custom inventory scenario.
        
        Args:
            scenario_config: Configuration for the custom scenario
            order_data: Optional order data from order simulation
            
        Returns:
            Dictionary with scenario results
        """
        # Extract inventory configuration from scenario
        inventory_config = scenario_config.get('inventory_config', {})
        
        # Merge with default config
        config = {**self.config, **inventory_config}
        
        # Run simulation with merged config
        return simulate_inventory(config, order_data)
