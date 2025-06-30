"""
Order simulation module for the warehouse management system.

This module provides functions for simulating order generation and fulfillment.
"""
import logging
import datetime
import random
import uuid
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from src.utils.helpers import get_db_session
from src.models.database import Product, Warehouse, Customer

logger = logging.getLogger(__name__)

def simulate_orders(config: Dict[str, Any],
                  duration_days: int = 7,
                  start_date: Optional[datetime.date] = None) -> Dict[str, Any]:
    """
    Simulate order generation and fulfillment.
    
    Args:
        config: Simulation configuration
        duration_days: Duration of simulation in days
        start_date: Start date for simulation (defaults to today)
        
    Returns:
        Dictionary with simulation results
    """
    logger.info(f"Simulating orders for {duration_days} days")
    
    # Set start date if not provided
    if not start_date:
        start_date = datetime.date.today()
    
    # Load data
    products = _load_products()
    warehouses = _load_warehouses()
    customers = _load_customers()
    
    if not products or not warehouses or not customers:
        return {
            "status": "error",
            "message": "Failed to load required data for simulation",
            "orders": []
        }
    
    # Generate orders
    orders = []
    order_count_by_date = {}
    revenue_by_date = {}
    
    # Set simulation parameters
    daily_order_mean = config.get('daily_order_mean', 100)
    daily_order_std = config.get('daily_order_std', 20)
    weekend_multiplier = config.get('weekend_multiplier', 1.5)
    items_per_order_mean = config.get('items_per_order_mean', 3)
    items_per_order_std = config.get('items_per_order_std', 1)
    
    # Simulate each day
    for day in range(duration_days):
        current_date = start_date + datetime.timedelta(days=day)
        
        # Adjust order volume for weekends
        is_weekend = current_date.weekday() >= 5  # 5=Saturday, 6=Sunday
        day_multiplier = weekend_multiplier if is_weekend else 1.0
        
        # Generate random number of orders for this day
        daily_orders = int(np.random.normal(
            daily_order_mean * day_multiplier, 
            daily_order_std * day_multiplier
        ))
        daily_orders = max(0, daily_orders)  # Ensure non-negative
        
        # Track metrics
        order_count_by_date[current_date.isoformat()] = daily_orders
        daily_revenue = 0
        
        # Generate orders for this day
        for _ in range(daily_orders):
            order = _generate_order(
                current_date=current_date,
                products=products,
                warehouses=warehouses,
                customers=customers,
                items_per_order_mean=items_per_order_mean,
                items_per_order_std=items_per_order_std,
                config=config
            )
            
            orders.append(order)
            daily_revenue += order['total_amount']
        
        revenue_by_date[current_date.isoformat()] = daily_revenue
    
    # Calculate metrics
    total_revenue = sum(order['total_amount'] for order in orders)
    avg_order_value = total_revenue / len(orders) if orders else 0
    
    return {
        "status": "success",
        "orders": orders,
        "metrics": {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "average_order_value": avg_order_value,
            "orders_by_date": order_count_by_date,
            "revenue_by_date": revenue_by_date
        }
    }

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
                    "id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "weight": product.weight
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
                    "id": warehouse.id,
                    "name": warehouse.name,
                    "latitude": warehouse.latitude,
                    "longitude": warehouse.longitude,
                    "capacity": warehouse.capacity
                })
            return warehouses
    except Exception as e:
        logger.error(f"Error loading warehouses: {str(e)}")
        return []

def _load_customers() -> List[Dict[str, Any]]:
    """
    Load customers from database.
    
    Returns:
        List of customer dictionaries
    """
    try:
        with get_db_session() as session:
            customers = []
            for customer in session.query(Customer).all():
                customers.append({
                    "id": customer.id,
                    "name": customer.name,
                    "email": customer.email,
                    "phone": customer.phone,
                    "address": customer.address,
                    "pincode": customer.pincode,
                    "latitude": customer.latitude,
                    "longitude": customer.longitude
                })
            return customers
    except Exception as e:
        logger.error(f"Error loading customers: {str(e)}")
        return []

def _generate_order(current_date: datetime.date,
                  products: List[Dict[str, Any]],
                  warehouses: List[Dict[str, Any]],
                  customers: List[Dict[str, Any]],
                  items_per_order_mean: float,
                  items_per_order_std: float,
                  config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a single order.
    
    Args:
        current_date: Date for the order
        products: List of product dictionaries
        warehouses: List of warehouse dictionaries
        customers: List of customer dictionaries
        items_per_order_mean: Mean number of items per order
        items_per_order_std: Standard deviation of items per order
        config: Simulation configuration
        
    Returns:
        Order dictionary
    """
    # Select random customer
    customer = random.choice(customers)
    
    # Generate random time
    hour = np.random.normal(14, 4)  # Peak around 2 PM
    hour = max(0, min(23, int(hour)))  # Clamp to valid hours
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    
    order_time = datetime.datetime.combine(
        current_date,
        datetime.time(hour, minute, second)
    )
    
    # Generate random number of items
    num_items = int(np.random.normal(items_per_order_mean, items_per_order_std))
    num_items = max(1, num_items)  # At least 1 item
    
    # Select random products
    selected_products = random.sample(products, min(num_items, len(products)))
    
    # Generate order items
    items = []
    total_amount = 0
    
    for product in selected_products:
        quantity = random.randint(1, 3)  # Random quantity between 1 and 3
        item_price = product['price']
        item_total = item_price * quantity
        
        items.append({
            "product_id": product['id'],
            "product_name": product['name'],
            "quantity": quantity,
            "unit_price": item_price,
            "total_price": item_total
        })
        
        total_amount += item_total
    
    # Select warehouse for fulfillment
    # In a real system, this would be based on proximity and inventory
    warehouse = random.choice(warehouses)
    
    # Generate order status
    # For simplicity, most orders are completed
    status_options = ["placed", "processing", "shipped", "delivered", "cancelled"]
    status_weights = [0.05, 0.1, 0.15, 0.65, 0.05]
    status = random.choices(status_options, weights=status_weights)[0]
    
    # Create order
    order = {
        "id": str(uuid.uuid4()),
        "customer_id": customer['id'],
        "customer_name": customer['name'],
        "customer_pincode": customer['pincode'],
        "customer_latitude": customer['latitude'],
        "customer_longitude": customer['longitude'],
        "timestamp": order_time.isoformat(),
        "items": items,
        "total_amount": total_amount,
        "status": status,
        "warehouse_fulfilled": warehouse['id'],
        "warehouse_name": warehouse['name']
    }
    
    return order

def generate_hourly_order_pattern(config: Dict[str, Any]) -> Dict[int, float]:
    """
    Generate hourly order distribution pattern.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Dictionary with hour (0-23) to weight mapping
    """
    # Default pattern with peak at lunch and evening
    default_pattern = {
        0: 0.01, 1: 0.005, 2: 0.005, 3: 0.005, 4: 0.01, 5: 0.02,
        6: 0.03, 7: 0.04, 8: 0.05, 9: 0.06, 10: 0.07, 11: 0.08,
        12: 0.09, 13: 0.08, 14: 0.07, 15: 0.06, 16: 0.05, 17: 0.06,
        18: 0.08, 19: 0.09, 20: 0.08, 21: 0.06, 22: 0.04, 23: 0.02
    }
    
    # Use config pattern if provided
    pattern = config.get('hourly_pattern', default_pattern)
    
    # Normalize to ensure sum is 1.0
    total = sum(pattern.values())
    return {hour: weight / total for hour, weight in pattern.items()}

def generate_weekly_order_pattern(config: Dict[str, Any]) -> Dict[int, float]:
    """
    Generate weekly order distribution pattern.
    
    Args:
        config: Simulation configuration
        
    Returns:
        Dictionary with day (0=Monday to 6=Sunday) to weight mapping
    """
    # Default pattern with peak on weekends
    default_pattern = {
        0: 0.12,  # Monday
        1: 0.11,  # Tuesday
        2: 0.12,  # Wednesday
        3: 0.13,  # Thursday
        4: 0.15,  # Friday
        5: 0.19,  # Saturday
        6: 0.18   # Sunday
    }
    
    # Use config pattern if provided
    pattern = config.get('weekly_pattern', default_pattern)
    
    # Normalize to ensure sum is 1.0
    total = sum(pattern.values())
    return {day: weight / total for day, weight in pattern.items()}
