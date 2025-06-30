"""
Analytics package for the warehouse management system.
"""

from . import demand_forecasting
from . import pattern_analysis
from . import product_analytics
from . import time_series_analysis

__all__ = [
    'demand_forecasting',
    'pattern_analysis',
    'product_analytics',
    'time_series_analysis'
]
