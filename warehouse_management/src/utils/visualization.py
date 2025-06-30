"""
Visualization utility for the warehouse management system.
Provides functions to generate plots and visualizations.
"""
import os
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap

from src.config.constants import (
    VISUALIZATION_CONFIG, WAREHOUSE_COORDINATES, BANGALORE_BOUNDS
)

logger = logging.getLogger(__name__)

def create_inventory_heatmap(inventory_data: List[Dict[str, Any]], 
                            output_path: str = "outputs/plots/inventory_heatmap.html") -> str:
    """
    Create a heatmap of inventory levels across warehouses.
    
    Args:
        inventory_data: List of inventory dictionaries with warehouse and product details
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(inventory_data)
        
        # Calculate stock percentage
        df['stock_percentage'] = (df['current_stock'] / df['max_capacity']) * 100
        
        # Pivot data for heatmap
        pivot_df = df.pivot_table(
            values='stock_percentage', 
            index='warehouse_name', 
            columns='product_name', 
            aggfunc='mean'
        )
        
        # Fill NaN values
        pivot_df = pivot_df.fillna(0)
        
        # Create heatmap using plotly
        fig = px.imshow(
            pivot_df,
            labels=dict(x="Product", y="Warehouse", color="Stock %"),
            x=pivot_df.columns,
            y=pivot_df.index,
            color_continuous_scale="RdYlGn",  # Red (low) to Yellow to Green (high)
            title="Inventory Levels Across Warehouses (%)",
            width=VISUALIZATION_CONFIG['default_width'],
            height=VISUALIZATION_CONFIG['default_height']
        )
        
        # Update layout
        fig.update_layout(
            xaxis=dict(tickangle=45),
            margin=dict(l=50, r=50, t=80, b=100)
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        fig.write_html(output_path)
        logger.info(f"Inventory heatmap saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating inventory heatmap: {e}")
        return ""

def create_demand_time_series(purchase_data: List[Dict[str, Any]], 
                             output_path: str = "outputs/plots/demand_time_series.html") -> str:
    """
    Create a time series plot of demand.
    
    Args:
        purchase_data: List of purchase event dictionaries
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(purchase_data)
        
        # Convert timestamp to datetime if it's a string
        if isinstance(df['timestamp'].iloc[0], str):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Extract date and hour
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        
        # Group by date and hour, sum quantities
        hourly_demand = df.groupby(['date', 'hour'])['quantity'].sum().reset_index()
        
        # Create datetime from date and hour for proper plotting
        hourly_demand['datetime'] = hourly_demand.apply(
            lambda row: pd.Timestamp(row['date']).replace(hour=row['hour']), 
            axis=1
        )
        
        # Create time series plot
        fig = px.line(
            hourly_demand, 
            x='datetime', 
            y='quantity',
            title='Hourly Demand Over Time',
            labels={'datetime': 'Date & Hour', 'quantity': 'Total Quantity Ordered'},
            width=VISUALIZATION_CONFIG['default_width'],
            height=VISUALIZATION_CONFIG['default_height']
        )
        
        # Add moving average
        ma_window = 24  # 24-hour moving average
        hourly_demand['moving_avg'] = hourly_demand['quantity'].rolling(window=ma_window).mean()
        
        fig.add_scatter(
            x=hourly_demand['datetime'], 
            y=hourly_demand['moving_avg'],
            mode='lines',
            name=f'{ma_window}-Hour Moving Average',
            line=dict(color='red', width=2)
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title='Date & Hour',
            yaxis_title='Total Quantity Ordered',
            legend_title='Series',
            hovermode='x unified'
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        fig.write_html(output_path)
        logger.info(f"Demand time series saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating demand time series: {e}")
        return ""

def create_warehouse_map(warehouse_data: List[Dict[str, Any]], 
                        demand_data: Optional[List[Dict[str, Any]]] = None,
                        output_path: str = "outputs/plots/warehouse_map.html") -> str:
    """
    Create a map of warehouses with optional demand heatmap.
    
    Args:
        warehouse_data: List of warehouse dictionaries
        demand_data: Optional list of demand data with coordinates
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Create map centered on Bangalore
        m = folium.Map(
            location=VISUALIZATION_CONFIG['map_center'],
            zoom_start=VISUALIZATION_CONFIG['map_zoom'],
            tiles='CartoDB positron'
        )
        
        # Add warehouses as markers
        for warehouse in warehouse_data:
            folium.Marker(
                location=[warehouse['latitude'], warehouse['longitude']],
                popup=f"<strong>{warehouse['name']}</strong><br>"
                      f"Area: {warehouse['area']}<br>"
                      f"Capacity: {warehouse['capacity']} m³<br>"
                      f"Staff: {warehouse['current_staff']}",
                icon=folium.Icon(color='blue', icon='industry', prefix='fa')
            ).add_to(m)
        
        # Add demand heatmap if provided
        if demand_data:
            # Extract coordinates and weights for heatmap
            heat_data = [
                [point['latitude'], point['longitude'], point['quantity']]
                for point in demand_data
            ]
            
            # Add heatmap layer
            HeatMap(heat_data, radius=15, blur=10, max_zoom=13).add_to(m)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        m.save(output_path)
        logger.info(f"Warehouse map saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating warehouse map: {e}")
        return ""

def create_category_distribution(product_data: List[Dict[str, Any]], 
                               output_path: str = "outputs/plots/category_distribution.html") -> str:
    """
    Create a pie chart of product category distribution.
    
    Args:
        product_data: List of product dictionaries
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(product_data)
        
        # Count products by category
        category_counts = df['category'].value_counts().reset_index()
        category_counts.columns = ['category', 'count']
        
        # Create pie chart
        fig = px.pie(
            category_counts, 
            values='count', 
            names='category',
            title='Product Distribution by Category',
            color_discrete_sequence=px.colors.qualitative.Plotly,
            width=VISUALIZATION_CONFIG['default_width'],
            height=VISUALIZATION_CONFIG['default_height']
        )
        
        # Update layout
        fig.update_layout(
            legend_title='Category',
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        fig.write_html(output_path)
        logger.info(f"Category distribution saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating category distribution: {e}")
        return ""

def create_stock_alerts_chart(inventory_alerts: List[Dict[str, Any]], 
                             output_path: str = "outputs/plots/stock_alerts.html") -> str:
    """
    Create a bar chart of stock alerts by warehouse.
    
    Args:
        inventory_alerts: List of inventory alert dictionaries
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(inventory_alerts)
        
        # Count alerts by warehouse and level
        alert_counts = df.groupby(['warehouse_name', 'alert_level']).size().reset_index()
        alert_counts.columns = ['warehouse_name', 'alert_level', 'count']
        
        # Create bar chart
        fig = px.bar(
            alert_counts, 
            x='warehouse_name', 
            y='count',
            color='alert_level',
            title='Stock Alerts by Warehouse',
            labels={'warehouse_name': 'Warehouse', 'count': 'Number of Alerts', 'alert_level': 'Alert Level'},
            color_discrete_map={
                'critical': 'red',
                'low': 'orange',
                'normal': 'green',
                'overstocked': 'blue'
            },
            width=VISUALIZATION_CONFIG['default_width'],
            height=VISUALIZATION_CONFIG['default_height']
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title='Warehouse',
            yaxis_title='Number of Alerts',
            legend_title='Alert Level',
            xaxis=dict(tickangle=45)
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        fig.write_html(output_path)
        logger.info(f"Stock alerts chart saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating stock alerts chart: {e}")
        return ""

def create_delivery_time_histogram(purchase_data: List[Dict[str, Any]], 
                                 output_path: str = "outputs/plots/delivery_time_histogram.html") -> str:
    """
    Create a histogram of delivery times.
    
    Args:
        purchase_data: List of purchase event dictionaries
        output_path: Path to save the output HTML file
        
    Returns:
        Path to the saved HTML file
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(purchase_data)
        
        # Filter out entries with no delivery time
        df = df[df['delivery_time'].notna()]
        
        # Create histogram
        fig = px.histogram(
            df, 
            x='delivery_time',
            nbins=20,
            title='Distribution of Delivery Times',
            labels={'delivery_time': 'Delivery Time (minutes)'},
            color_discrete_sequence=['#636EFA'],
            width=VISUALIZATION_CONFIG['default_width'],
            height=VISUALIZATION_CONFIG['default_height']
        )
        
        # Add vertical line for mean
        mean_delivery_time = df['delivery_time'].mean()
        fig.add_vline(
            x=mean_delivery_time,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Mean: {mean_delivery_time:.1f} min",
            annotation_position="top right"
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title='Delivery Time (minutes)',
            yaxis_title='Count',
            bargap=0.1
        )
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as HTML
        fig.write_html(output_path)
        logger.info(f"Delivery time histogram saved to {output_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating delivery time histogram: {e}")
        return ""
