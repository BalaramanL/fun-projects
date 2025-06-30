"""
Pattern analysis module for the warehouse management system.
Provides functions for analyzing spatial and temporal patterns in purchase data.
"""
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

import pandas as pd
from sqlalchemy.orm import Session

from src.models.events import PincodeMapping

logger = logging.getLogger(__name__)

def analyze_area_demand(purchase_data: List[Dict[str, Any]], db: Session) -> Dict[str, Any]:
    """
    Analyze demand patterns by geographical area.
    
    Args:
        purchase_data: List of purchase event dictionaries
        db: Database session
        
    Returns:
        Dictionary with area demand analysis
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty:
        logger.warning("No purchase data available for area demand analysis")
        return {
            'area_distribution': {},
            'high_demand_areas': [],
            'low_demand_areas': []
        }
    
    # Get pincode mappings
    pincode_mappings = db.query(PincodeMapping).all()
    pincode_to_area = {mapping.pincode: mapping.area_name for mapping in pincode_mappings}
    
    # Add area to purchase data
    df['area'] = df['customer_pincode'].map(pincode_to_area)
    
    # Remove rows with unknown areas
    df = df.dropna(subset=['area'])
    
    # Group by area and sum quantities
    area_demand = df.groupby('area')['quantity'].sum().reset_index()
    area_demand['percentage'] = (area_demand['quantity'] / area_demand['quantity'].sum()) * 100
    
    # Find high and low demand areas (top and bottom 30%)
    high_threshold = area_demand['quantity'].quantile(0.7)
    low_threshold = area_demand['quantity'].quantile(0.3)
    
    high_demand_areas = area_demand[area_demand['quantity'] >= high_threshold]['area'].tolist()
    low_demand_areas = area_demand[area_demand['quantity'] <= low_threshold]['area'].tolist()
    
    # Convert area distribution to dictionary
    area_distribution = {row['area']: {
        'quantity': int(row['quantity']),
        'percentage': float(row['percentage'])
    } for _, row in area_demand.iterrows()}
    
    return {
        'area_distribution': area_distribution,
        'high_demand_areas': high_demand_areas,
        'low_demand_areas': low_demand_areas
    }

def get_area_insights(purchase_data: List[Dict[str, Any]], db: Session) -> List[Dict[str, Any]]:
    """
    Get detailed insights about demand by area.
    
    Args:
        purchase_data: List of purchase event dictionaries
        db: Database session
        
    Returns:
        List of area insights
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty:
        logger.warning("No purchase data available for area insights")
        return []
    
    # Get pincode mappings
    pincode_mappings = db.query(PincodeMapping).all()
    pincode_to_area = {mapping.pincode: mapping.area_name for mapping in pincode_mappings}
    pincode_to_location = {mapping.pincode: (mapping.latitude, mapping.longitude) for mapping in pincode_mappings}
    
    # Add area to purchase data
    df['area'] = df['customer_pincode'].map(pincode_to_area)
    
    # Remove rows with unknown areas
    df = df.dropna(subset=['area'])
    
    # Convert timestamp to datetime if it's a string
    if 'timestamp' in df.columns and isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
    
    # Group by area
    area_insights = []
    
    for area, area_df in df.groupby('area'):
        # Basic metrics
        total_quantity = int(area_df['quantity'].sum())
        avg_quantity = float(area_df['quantity'].mean())
        order_count = len(area_df)
        
        # Get unique pincodes in this area
        pincodes = area_df['customer_pincode'].unique().tolist()
        
        # Get center location (average of all pincodes in the area)
        locations = [pincode_to_location.get(pincode) for pincode in pincodes if pincode in pincode_to_location]
        if locations:
            latitude = sum(loc[0] for loc in locations) / len(locations)
            longitude = sum(loc[1] for loc in locations) / len(locations)
        else:
            latitude = None
            longitude = None
        
        # Time patterns if timestamp is available
        time_patterns = {}
        if 'hour' in area_df.columns:
            # Hourly distribution
            hourly = area_df.groupby('hour')['quantity'].sum()
            peak_hour = int(hourly.idxmax()) if not hourly.empty else None
            
            # Daily distribution
            if 'day_of_week' in area_df.columns:
                daily = area_df.groupby('day_of_week')['quantity'].sum()
                peak_day = int(daily.idxmax()) if not daily.empty else None
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                peak_day_name = day_names[peak_day] if peak_day is not None else None
                
                time_patterns = {
                    'peak_hour': peak_hour,
                    'peak_day': peak_day,
                    'peak_day_name': peak_day_name
                }
        
        # Product preferences
        if 'product_id' in area_df.columns and 'product_name' in area_df.columns:
            product_demand = area_df.groupby(['product_id', 'product_name'])['quantity'].sum().reset_index()
            top_products = product_demand.nlargest(5, 'quantity')
            
            top_products_list = [{
                'product_id': row['product_id'],
                'product_name': row['product_name'],
                'quantity': int(row['quantity'])
            } for _, row in top_products.iterrows()]
        else:
            top_products_list = []
        
        # Delivery time analysis if available
        delivery_time_stats = {}
        if 'delivery_time' in area_df.columns:
            delivery_times = area_df['delivery_time'].dropna()
            if not delivery_times.empty:
                delivery_time_stats = {
                    'avg_delivery_time': float(delivery_times.mean()),
                    'min_delivery_time': float(delivery_times.min()),
                    'max_delivery_time': float(delivery_times.max())
                }
        
        # Add to insights
        area_insights.append({
            'area': area,
            'pincodes': pincodes,
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'metrics': {
                'total_quantity': total_quantity,
                'avg_quantity': avg_quantity,
                'order_count': order_count
            },
            'time_patterns': time_patterns,
            'top_products': top_products_list,
            'delivery_time_stats': delivery_time_stats
        })
    
    # Sort by total quantity
    area_insights.sort(key=lambda x: x['metrics']['total_quantity'], reverse=True)
    
    return area_insights

def analyze_purchase_correlations(purchase_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze correlations between products in purchase data.
    
    Args:
        purchase_data: List of purchase event dictionaries
        
    Returns:
        List of product correlation data
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty or doesn't have required columns
    if df.empty or 'product_id' not in df.columns or 'timestamp' not in df.columns:
        logger.warning("No suitable purchase data available for correlation analysis")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add date column
    df['date'] = df['timestamp'].dt.date
    
    # Group purchases by date and product
    daily_product_purchases = df.groupby(['date', 'product_id'])['quantity'].sum().unstack(fill_value=0)
    
    # Calculate correlation matrix
    try:
        corr_matrix = daily_product_purchases.corr()
        
        # Convert to list of correlations
        correlations = []
        
        # Get product names if available
        product_names = {}
        if 'product_name' in df.columns:
            for _, row in df.drop_duplicates(subset=['product_id', 'product_name']).iterrows():
                product_names[row['product_id']] = row['product_name']
        
        # Extract correlations
        for product1 in corr_matrix.index:
            for product2 in corr_matrix.columns:
                if product1 != product2 and not pd.isna(corr_matrix.loc[product1, product2]):
                    correlation = corr_matrix.loc[product1, product2]
                    
                    # Only include significant correlations
                    if abs(correlation) >= 0.3:
                        correlations.append({
                            'product1_id': product1,
                            'product1_name': product_names.get(product1, 'Unknown'),
                            'product2_id': product2,
                            'product2_name': product_names.get(product2, 'Unknown'),
                            'correlation': float(correlation),
                            'strength': 'strong' if abs(correlation) >= 0.7 else 'moderate',
                            'type': 'positive' if correlation > 0 else 'negative'
                        })
        
        # Sort by absolute correlation value
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return correlations[:50]  # Return top 50 correlations
    
    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}")
        return []
