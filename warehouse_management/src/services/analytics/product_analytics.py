"""
Product analytics module for the warehouse management system.
Provides functions for analyzing product performance and trends.
"""
import logging
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from src.models.product import Product

logger = logging.getLogger(__name__)

def analyze_product_demand(purchase_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze demand patterns by product.
    
    Args:
        purchase_data: List of purchase event dictionaries
        
    Returns:
        Dictionary with product demand analysis
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'product_id' not in df.columns:
        logger.warning("No suitable purchase data available for product demand analysis")
        return {
            'top_products': [],
            'category_distribution': {},
            'subcategory_distribution': {}
        }
    
    # Group by product and sum quantities
    product_demand = df.groupby('product_id')['quantity'].sum().reset_index()
    product_demand = product_demand.sort_values('quantity', ascending=False)
    
    # Get top products
    top_products = []
    for _, row in product_demand.head(10).iterrows():
        product_id = row['product_id']
        product_info = {
            'product_id': product_id,
            'quantity': int(row['quantity'])
        }
        
        # Add product name if available
        if 'product_name' in df.columns:
            product_names = df[df['product_id'] == product_id]['product_name'].unique()
            if len(product_names) > 0:
                product_info['product_name'] = product_names[0]
        
        top_products.append(product_info)
    
    # Category distribution if available
    category_distribution = {}
    subcategory_distribution = {}
    
    if 'product_category' in df.columns:
        category_demand = df.groupby('product_category')['quantity'].sum().reset_index()
        category_demand['percentage'] = (category_demand['quantity'] / category_demand['quantity'].sum()) * 100
        
        category_distribution = {
            row['product_category']: float(row['percentage']) 
            for _, row in category_demand.iterrows()
        }
        
        # Subcategory distribution if available
        if 'product_subcategory' in df.columns:
            subcategory_demand = df.groupby(['product_category', 'product_subcategory'])['quantity'].sum().reset_index()
            total_quantity = subcategory_demand['quantity'].sum()
            subcategory_demand['percentage'] = (subcategory_demand['quantity'] / total_quantity) * 100
            
            subcategory_distribution = {}
            for _, row in subcategory_demand.iterrows():
                category = row['product_category']
                subcategory = row['product_subcategory']
                
                if category not in subcategory_distribution:
                    subcategory_distribution[category] = {}
                
                subcategory_distribution[category][subcategory] = float(row['percentage'])
    
    return {
        'top_products': top_products,
        'category_distribution': category_distribution,
        'subcategory_distribution': subcategory_distribution
    }

def get_product_insights(purchase_data: List[Dict[str, Any]], 
                         db: Session, 
                         top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get insights about top and bottom performing products.
    
    Args:
        purchase_data: List of purchase event dictionaries
        db: Database session
        top_n: Number of top/bottom products to return
        
    Returns:
        Dictionary with top and bottom products
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'product_id' not in df.columns:
        logger.warning("No suitable purchase data available for product insights")
        return {
            'top_products': [],
            'bottom_products': []
        }
    
    # Group by product and sum quantities
    product_demand = df.groupby('product_id')['quantity'].sum().reset_index()
    
    # Get all product IDs from the database
    all_products = db.query(Product).all()
    all_product_ids = {product.id for product in all_products}
    
    # Find products with no demand
    products_with_demand = set(product_demand['product_id'].unique())
    products_without_demand = all_product_ids - products_with_demand
    
    # Create entries for products without demand
    for product_id in products_without_demand:
        product_demand = pd.concat([
            product_demand, 
            pd.DataFrame([{'product_id': product_id, 'quantity': 0}])
        ])
    
    # Sort by quantity
    product_demand = product_demand.sort_values('quantity', ascending=False)
    
    # Get product details
    product_map = {product.id: product for product in all_products}
    
    # Get top products
    top_products = []
    for _, row in product_demand.head(top_n).iterrows():
        product_id = row['product_id']
        product = product_map.get(product_id)
        
        if product:
            top_products.append({
                'product_id': product_id,
                'product_name': product.name,
                'product_category': product.category,
                'product_subcategory': product.subcategory,
                'quantity': int(row['quantity']),
                'price': float(product.price)
            })
    
    # Get bottom products (excluding those with zero demand)
    bottom_products = []
    for _, row in product_demand[product_demand['quantity'] > 0].tail(top_n).iterrows():
        product_id = row['product_id']
        product = product_map.get(product_id)
        
        if product:
            bottom_products.append({
                'product_id': product_id,
                'product_name': product.name,
                'product_category': product.category,
                'product_subcategory': product.subcategory,
                'quantity': int(row['quantity']),
                'price': float(product.price)
            })
    
    # Get zero demand products
    zero_demand_products = []
    for product_id in products_without_demand:
        product = product_map.get(product_id)
        
        if product:
            zero_demand_products.append({
                'product_id': product_id,
                'product_name': product.name,
                'product_category': product.category,
                'product_subcategory': product.subcategory,
                'quantity': 0,
                'price': float(product.price)
            })
    
    # Limit zero demand products to top_n
    zero_demand_products = zero_demand_products[:top_n]
    
    return {
        'top_products': top_products,
        'bottom_products': bottom_products,
        'zero_demand_products': zero_demand_products
    }

def analyze_product_trends(purchase_data: List[Dict[str, Any]], 
                          days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Analyze trends in product demand over time.
    
    Args:
        purchase_data: List of purchase event dictionaries
        days_back: Number of days to analyze
        
    Returns:
        List of product trend data
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'product_id' not in df.columns or 'timestamp' not in df.columns:
        logger.warning("No suitable purchase data available for product trend analysis")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add date column
    df['date'] = df['timestamp'].dt.date
    
    # Calculate date ranges
    end_date = df['date'].max()
    mid_date = end_date - timedelta(days=days_back//2)
    start_date = end_date - timedelta(days=days_back)
    
    # Split data into two periods
    recent_period = df[df['date'] > mid_date]
    previous_period = df[(df['date'] <= mid_date) & (df['date'] >= start_date)]
    
    # Group by product and sum quantities for each period
    recent_demand = recent_period.groupby('product_id')['quantity'].sum()
    previous_demand = previous_period.groupby('product_id')['quantity'].sum()
    
    # Combine data
    product_trends = []
    
    # Get all product IDs
    all_product_ids = set(recent_demand.index) | set(previous_demand.index)
    
    for product_id in all_product_ids:
        recent_qty = recent_demand.get(product_id, 0)
        previous_qty = previous_demand.get(product_id, 0)
        
        # Calculate trend
        if previous_qty > 0:
            change_percent = ((recent_qty - previous_qty) / previous_qty) * 100
        elif recent_qty > 0:
            change_percent = 100  # New product
        else:
            change_percent = 0  # No demand in either period
        
        # Determine trend direction
        if change_percent > 15:
            trend = 'rising'
        elif change_percent < -15:
            trend = 'falling'
        else:
            trend = 'stable'
        
        # Get product name if available
        product_name = 'Unknown'
        if 'product_name' in df.columns:
            product_names = df[df['product_id'] == product_id]['product_name'].unique()
            if len(product_names) > 0:
                product_name = product_names[0]
        
        # Get category if available
        product_category = None
        if 'product_category' in df.columns:
            categories = df[df['product_id'] == product_id]['product_category'].unique()
            if len(categories) > 0:
                product_category = categories[0]
        
        product_trends.append({
            'product_id': product_id,
            'product_name': product_name,
            'product_category': product_category,
            'recent_quantity': int(recent_qty),
            'previous_quantity': int(previous_qty),
            'change_percent': float(change_percent),
            'trend': trend
        })
    
    # Sort by absolute change percentage
    product_trends.sort(key=lambda x: abs(x['change_percent']), reverse=True)
    
    return product_trends
