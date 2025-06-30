"""
Demand forecasting module for the warehouse management system.
Provides functions for analyzing and forecasting demand patterns.
"""
import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

def analyze_hourly_patterns(purchase_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze hourly demand patterns.
    
    Args:
        purchase_data: List of purchase event dictionaries
        
    Returns:
        Dictionary with hourly pattern analysis
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty:
        logger.warning("No purchase data available for hourly pattern analysis")
        return {
            'peak_hours': [],
            'low_hours': [],
            'hourly_distribution': {},
            'weekday_patterns': {},
            'weekend_patterns': {}
        }
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract hour and day of week
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0-6 for Monday-Sunday
    df['is_weekend'] = df['day_of_week'].apply(lambda x: x >= 5)  # 5-6 for Saturday-Sunday
    
    # Group by hour and sum quantities
    hourly_demand = df.groupby('hour')['quantity'].sum().reset_index()
    hourly_demand['percentage'] = (hourly_demand['quantity'] / hourly_demand['quantity'].sum()) * 100
    
    # Find peak and low hours (top and bottom 20%)
    peak_threshold = hourly_demand['quantity'].quantile(0.8)
    low_threshold = hourly_demand['quantity'].quantile(0.2)
    
    peak_hours = hourly_demand[hourly_demand['quantity'] >= peak_threshold]['hour'].tolist()
    low_hours = hourly_demand[hourly_demand['quantity'] <= low_threshold]['hour'].tolist()
    
    # Separate weekday and weekend patterns
    weekday_demand = df[~df['is_weekend']].groupby('hour')['quantity'].sum().reset_index()
    weekend_demand = df[df['is_weekend']].groupby('hour')['quantity'].sum().reset_index()
    
    # Normalize to percentages
    weekday_total = weekday_demand['quantity'].sum()
    weekend_total = weekend_demand['quantity'].sum()
    
    weekday_patterns = {}
    weekend_patterns = {}
    
    if weekday_total > 0:
        weekday_demand['percentage'] = (weekday_demand['quantity'] / weekday_total) * 100
        weekday_patterns = {row['hour']: row['percentage'] for _, row in weekday_demand.iterrows()}
    
    if weekend_total > 0:
        weekend_demand['percentage'] = (weekend_demand['quantity'] / weekend_total) * 100
        weekend_patterns = {row['hour']: row['percentage'] for _, row in weekend_demand.iterrows()}
    
    # Convert hourly distribution to dictionary
    hourly_distribution = {row['hour']: row['percentage'] for _, row in hourly_demand.iterrows()}
    
    return {
        'peak_hours': peak_hours,
        'low_hours': low_hours,
        'hourly_distribution': hourly_distribution,
        'weekday_patterns': weekday_patterns,
        'weekend_patterns': weekend_patterns
    }

def analyze_daily_patterns(purchase_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze daily demand patterns.
    
    Args:
        purchase_data: List of purchase event dictionaries
        
    Returns:
        Dictionary with daily pattern analysis
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty:
        logger.warning("No purchase data available for daily pattern analysis")
        return {
            'peak_days': [],
            'low_days': [],
            'daily_distribution': {},
            'day_names': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract day of week
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0-6 for Monday-Sunday
    
    # Group by day of week and sum quantities
    daily_demand = df.groupby('day_of_week')['quantity'].sum().reset_index()
    daily_demand['percentage'] = (daily_demand['quantity'] / daily_demand['quantity'].sum()) * 100
    
    # Find peak and low days (top and bottom 30%)
    peak_threshold = daily_demand['quantity'].quantile(0.7)
    low_threshold = daily_demand['quantity'].quantile(0.3)
    
    peak_days = daily_demand[daily_demand['quantity'] >= peak_threshold]['day_of_week'].tolist()
    low_days = daily_demand[daily_demand['quantity'] <= low_threshold]['day_of_week'].tolist()
    
    # Convert daily distribution to dictionary
    daily_distribution = {int(row['day_of_week']): row['percentage'] for _, row in daily_demand.iterrows()}
    
    # Map day numbers to names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return {
        'peak_days': peak_days,
        'low_days': low_days,
        'daily_distribution': daily_distribution,
        'day_names': day_names
    }

def forecast_demand(purchase_data: List[Dict[str, Any]], days: int = 7) -> List[Dict[str, Any]]:
    """
    Forecast demand for the next few days.
    
    Args:
        purchase_data: List of purchase event dictionaries
        days: Number of days to forecast
        
    Returns:
        List of daily demand forecasts
    """
    # Convert to DataFrame
    df = pd.DataFrame(purchase_data)
    
    # Check if DataFrame is empty
    if df.empty:
        logger.warning("No purchase data available for demand forecasting")
        return []
    
    # Convert timestamp to datetime if it's a string
    if isinstance(df['timestamp'].iloc[0], str):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract date
    df['date'] = df['timestamp'].dt.date
    
    # Group by date and sum quantities
    daily_demand = df.groupby('date')['quantity'].sum().reset_index()
    
    # Sort by date
    daily_demand = daily_demand.sort_values('date')
    
    # Check if we have enough data points for forecasting
    if len(daily_demand) < 7:
        logger.warning("Not enough data points for reliable forecasting")
        # Use average if not enough data
        avg_demand = daily_demand['quantity'].mean()
        
        # Generate forecast using average
        forecast = []
        last_date = max(daily_demand['date'])
        
        for i in range(1, days + 1):
            forecast_date = last_date + timedelta(days=i)
            forecast.append({
                'date': forecast_date,
                'day_of_week': forecast_date.weekday(),
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][forecast_date.weekday()],
                'forecast_quantity': int(avg_demand),
                'confidence_interval': (int(avg_demand * 0.7), int(avg_demand * 1.3)),
                'method': 'average'
            })
        
        return forecast
    
    # Use time series decomposition for forecasting
    try:
        # Convert to time series
        ts = pd.Series(daily_demand['quantity'].values, index=pd.DatetimeIndex(daily_demand['date']))
        
        # Calculate moving average for trend
        trend = ts.rolling(window=7, min_periods=1).mean()
        
        # Extract day of week for seasonality
        day_of_week = pd.Series(pd.DatetimeIndex(ts.index).dayofweek)
        
        # Calculate average by day of week for seasonality
        seasonality = {}
        for day in range(7):
            day_values = ts[day_of_week == day]
            if len(day_values) > 0:
                seasonality[day] = day_values.mean() / trend[day_values.index].mean() if trend[day_values.index].mean() > 0 else 1
            else:
                seasonality[day] = 1
        
        # Generate forecast
        forecast = []
        last_date = max(daily_demand['date'])
        last_value = daily_demand[daily_demand['date'] == last_date]['quantity'].iloc[0]
        
        # Use last 7 days for trend calculation
        recent_trend = daily_demand.tail(7)['quantity'].mean()
        
        for i in range(1, days + 1):
            forecast_date = last_date + timedelta(days=i)
            day_of_week = forecast_date.weekday()
            
            # Apply seasonality factor
            season_factor = seasonality.get(day_of_week, 1)
            
            # Calculate forecast
            forecast_value = recent_trend * season_factor
            
            # Add some randomness for realism
            noise = np.random.normal(0, forecast_value * 0.1)
            forecast_value = max(0, forecast_value + noise)
            
            # Calculate confidence interval (±20%)
            confidence_interval = (int(forecast_value * 0.8), int(forecast_value * 1.2))
            
            forecast.append({
                'date': forecast_date,
                'day_of_week': day_of_week,
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week],
                'forecast_quantity': int(forecast_value),
                'confidence_interval': confidence_interval,
                'method': 'time_series_decomposition'
            })
        
        return forecast
    
    except Exception as e:
        logger.error(f"Error in demand forecasting: {e}")
        # Fallback to simple average
        avg_demand = daily_demand['quantity'].mean()
        
        # Generate forecast using average
        forecast = []
        last_date = max(daily_demand['date'])
        
        for i in range(1, days + 1):
            forecast_date = last_date + timedelta(days=i)
            forecast.append({
                'date': forecast_date,
                'day_of_week': forecast_date.weekday(),
                'day_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][forecast_date.weekday()],
                'forecast_quantity': int(avg_demand),
                'confidence_interval': (int(avg_demand * 0.7), int(avg_demand * 1.3)),
                'method': 'average_fallback'
            })
        
        return forecast
