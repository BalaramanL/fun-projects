"""
Time series analysis module for the warehouse management system.
Provides functions for analyzing time series data and detecting anomalies.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

def get_time_series_data(purchase_data: List[Dict[str, Any]], 
                        interval: str = 'hourly') -> List[Dict[str, Any]]:
    """
    Get time series data for demand.
    
    Args:
        purchase_data: List of purchase event dictionaries
        interval: Time interval ('hourly', 'daily', 'weekly')
        
    Returns:
        List of time series data points
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'timestamp' not in df.columns:
        logger.warning("No suitable purchase data available for time series analysis")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    # Resample based on interval
    if interval == 'hourly':
        resampled = df.resample('H')['quantity'].sum().reset_index()
        time_format = '%Y-%m-%d %H:00'
    elif interval == 'daily':
        resampled = df.resample('D')['quantity'].sum().reset_index()
        time_format = '%Y-%m-%d'
    elif interval == 'weekly':
        resampled = df.resample('W')['quantity'].sum().reset_index()
        time_format = '%Y-%m-%d'
    else:
        logger.error(f"Invalid interval: {interval}")
        return []
    
    # Convert to list of dictionaries
    time_series = []
    for _, row in resampled.iterrows():
        time_series.append({
            'timestamp': row['timestamp'],
            'time_str': row['timestamp'].strftime(time_format),
            'quantity': int(row['quantity'])
        })
    
    return time_series

def detect_anomalies(purchase_data: List[Dict[str, Any]], 
                    z_threshold: float = 2.5) -> List[Dict[str, Any]]:
    """
    Detect anomalies in purchase patterns using Z-score method.
    
    Args:
        purchase_data: List of purchase event dictionaries
        z_threshold: Z-score threshold for anomaly detection
        
    Returns:
        List of detected anomalies
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'timestamp' not in df.columns:
        logger.warning("No suitable purchase data available for anomaly detection")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    # Resample to daily data
    daily_data = df.resample('D')['quantity'].sum().reset_index()
    
    # Calculate Z-scores
    if len(daily_data) < 3:
        logger.warning("Not enough data points for anomaly detection")
        return []
    
    daily_data['z_score'] = stats.zscore(daily_data['quantity'])
    
    # Detect anomalies
    anomalies = daily_data[abs(daily_data['z_score']) > z_threshold]
    
    # Convert to list of dictionaries
    anomaly_list = []
    for _, row in anomalies.iterrows():
        anomaly_type = 'spike' if row['z_score'] > 0 else 'drop'
        severity = 'extreme' if abs(row['z_score']) > 3.5 else 'significant'
        
        anomaly_list.append({
            'date': row['timestamp'].date(),
            'quantity': int(row['quantity']),
            'z_score': float(row['z_score']),
            'type': anomaly_type,
            'severity': severity
        })
    
    return anomaly_list

def detect_product_anomalies(purchase_data: List[Dict[str, Any]], 
                           z_threshold: float = 2.5) -> List[Dict[str, Any]]:
    """
    Detect anomalies in product purchase patterns.
    
    Args:
        purchase_data: List of purchase event dictionaries
        z_threshold: Z-score threshold for anomaly detection
        
    Returns:
        List of detected product anomalies
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'timestamp' not in df.columns or 'product_id' not in df.columns:
        logger.warning("No suitable purchase data available for product anomaly detection")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Add date column
    df['date'] = df['timestamp'].dt.date
    
    # Group by date and product
    daily_product_data = df.groupby(['date', 'product_id'])['quantity'].sum().reset_index()
    
    # Get product names if available
    product_names = {}
    if 'product_name' in df.columns:
        for _, row in df.drop_duplicates(subset=['product_id', 'product_name']).iterrows():
            product_names[row['product_id']] = row['product_name']
    
    # Detect anomalies for each product
    anomalies = []
    
    for product_id in daily_product_data['product_id'].unique():
        product_data = daily_product_data[daily_product_data['product_id'] == product_id]
        
        # Need at least 3 data points for Z-score
        if len(product_data) < 3:
            continue
        
        # Calculate Z-scores
        product_data['z_score'] = stats.zscore(product_data['quantity'])
        
        # Detect anomalies
        product_anomalies = product_data[abs(product_data['z_score']) > z_threshold]
        
        for _, row in product_anomalies.iterrows():
            anomaly_type = 'spike' if row['z_score'] > 0 else 'drop'
            severity = 'extreme' if abs(row['z_score']) > 3.5 else 'significant'
            
            anomalies.append({
                'date': row['date'],
                'product_id': product_id,
                'product_name': product_names.get(product_id, 'Unknown'),
                'quantity': int(row['quantity']),
                'z_score': float(row['z_score']),
                'type': anomaly_type,
                'severity': severity
            })
    
    # Sort by absolute Z-score
    anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)
    
    return anomalies

def detect_seasonal_patterns(purchase_data: List[Dict[str, Any]], 
                           min_days: int = 14) -> Dict[str, Any]:
    """
    Detect seasonal patterns in purchase data.
    
    Args:
        purchase_data: List of purchase event dictionaries
        min_days: Minimum number of days required for analysis
        
    Returns:
        Dictionary with detected seasonal patterns
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty or 'timestamp' not in df.columns:
        logger.warning("No suitable purchase data available for seasonal pattern detection")
        return {
            'daily_pattern': None,
            'weekly_pattern': None,
            'hourly_pattern': None
        }
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract time components
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['date'] = df['timestamp'].dt.date
    
    # Check if we have enough days
    unique_days = df['date'].nunique()
    if unique_days < min_days:
        logger.warning(f"Not enough days for reliable seasonal analysis: {unique_days} < {min_days}")
        return {
            'daily_pattern': None,
            'weekly_pattern': None,
            'hourly_pattern': None
        }
    
    # Analyze hourly pattern
    hourly_pattern = df.groupby('hour')['quantity'].sum()
    hourly_pattern = hourly_pattern / hourly_pattern.sum()
    
    # Analyze daily pattern
    daily_pattern = df.groupby('day_of_week')['quantity'].sum()
    daily_pattern = daily_pattern / daily_pattern.sum()
    
    # Analyze weekly pattern by grouping dates into weeks
    df['week'] = df['timestamp'].dt.isocalendar().week
    weekly_totals = df.groupby(['week'])['quantity'].sum()
    
    # Check if we have enough weeks
    if len(weekly_totals) < 2:
        weekly_pattern = None
    else:
        # Normalize weekly pattern
        weekly_pattern = (weekly_totals - weekly_totals.mean()) / weekly_totals.std()
        weekly_pattern = weekly_pattern.to_dict()
    
    # Convert to dictionaries
    hourly_pattern_dict = hourly_pattern.to_dict()
    daily_pattern_dict = daily_pattern.to_dict()
    
    # Map day numbers to names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_pattern_named = {day_names[day]: value for day, value in daily_pattern_dict.items()}
    
    return {
        'hourly_pattern': hourly_pattern_dict,
        'daily_pattern': daily_pattern_named,
        'weekly_pattern': weekly_pattern
    }

def forecast_with_arima(time_series_data: List[Dict[str, Any]], 
                       forecast_periods: int = 7) -> List[Dict[str, Any]]:
    """
    Forecast future values using ARIMA model.
    
    Args:
        time_series_data: List of time series data points
        forecast_periods: Number of periods to forecast
        
    Returns:
        List of forecasted values
    """
    try:
        # Try to import statsmodels
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        logger.error("statsmodels package not available for ARIMA forecasting")
        return []
    
    # Convert to DataFrame
    df = pd.DataFrame(time_series_data)
    
    # Check if DataFrame is empty
    if df.empty or 'timestamp' not in df.columns or 'quantity' not in df.columns:
        logger.warning("No suitable time series data available for ARIMA forecasting")
        return []
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    try:
        # Fit ARIMA model
        model = ARIMA(df['quantity'], order=(1, 1, 1))
        model_fit = model.fit()
        
        # Forecast
        forecast = model_fit.forecast(steps=forecast_periods)
        
        # Generate forecast dates
        last_date = df.index[-1]
        forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_periods)]
        
        # Create forecast data
        forecast_data = []
        for i, (date, value) in enumerate(zip(forecast_dates, forecast)):
            forecast_data.append({
                'timestamp': date,
                'time_str': date.strftime('%Y-%m-%d'),
                'quantity': max(0, int(round(value))),
                'is_forecast': True,
                'forecast_period': i + 1
            })
        
        return forecast_data
    
    except Exception as e:
        logger.error(f"Error in ARIMA forecasting: {e}")
        return []
