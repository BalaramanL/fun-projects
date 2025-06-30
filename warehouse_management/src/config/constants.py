"""
Constants for the warehouse management system.
Contains configuration values that don't change during runtime.
"""
from typing import Dict, List, Any

# Geographical bounds of Bangalore
BANGALORE_BOUNDS = {
    'north': 13.1986,
    'south': 12.7343,
    'east': 77.8451,
    'west': 77.4101
}

# Warehouse locations in Bangalore
WAREHOUSE_AREAS = [
    'Whitefield', 'Koramangala', 'Indiranagar', 
    'Marathahalli', 'Jayanagar', 'Electronic City',
    'HSR Layout', 'Bannerghatta Road'
]

# Warehouse coordinates (approximate)
WAREHOUSE_COORDINATES = {
    'Whitefield': (12.9698, 77.7500),
    'Koramangala': (12.9352, 77.6245),
    'Indiranagar': (12.9784, 77.6408),
    'Marathahalli': (12.9591, 77.6974),
    'Jayanagar': (12.9250, 77.5938),
    'Electronic City': (12.8399, 77.6770),
    'HSR Layout': (12.9116, 77.6474),
    'Bannerghatta Road': (12.8933, 77.5976)
}

# Product categories and subcategories
PRODUCT_CATEGORIES = {
    'fresh': ['Vegetables', 'Fruits', 'Dairy', 'Meat & Seafood'],
    'packaged': ['Snacks', 'Beverages', 'Personal Care', 'Breakfast & Dairy', 'Instant Food'],
    'essentials': ['Household', 'Baby Care', 'Pet Care', 'Ready-to-Cook', 'Staples']
}

# Unit types for products
UNIT_TYPES = ['kg', 'g', 'l', 'ml', 'pcs', 'pack']

# Shelf life ranges (in days) by category
SHELF_LIFE_RANGES = {
    'Vegetables': (3, 10),
    'Fruits': (3, 14),
    'Dairy': (3, 30),
    'Meat & Seafood': (1, 5),
    'Snacks': (30, 180),
    'Beverages': (90, 365),
    'Personal Care': (180, 730),
    'Breakfast & Dairy': (90, 180),
    'Instant Food': (180, 365),
    'Household': (365, 730),
    'Baby Care': (180, 730),
    'Pet Care': (180, 365),
    'Ready-to-Cook': (90, 180),
    'Staples': (180, 365)
}

# Price ranges by category (in INR)
PRICE_RANGES = {
    'Vegetables': (10, 100),
    'Fruits': (20, 200),
    'Dairy': (20, 150),
    'Meat & Seafood': (100, 500),
    'Snacks': (10, 200),
    'Beverages': (10, 300),
    'Personal Care': (50, 500),
    'Breakfast & Dairy': (30, 300),
    'Instant Food': (50, 300),
    'Household': (50, 500),
    'Baby Care': (100, 1000),
    'Pet Care': (100, 1000),
    'Ready-to-Cook': (50, 300),
    'Staples': (20, 500)
}

# Demand patterns by time of day (0-23 hours)
HOURLY_DEMAND_PATTERNS = {
    'weekday': [0.2, 0.1, 0.1, 0.1, 0.2, 0.5, 1.0, 1.5, 1.2, 1.0, 0.8, 1.0, 
                1.2, 0.8, 0.6, 0.7, 0.9, 1.2, 1.5, 1.8, 1.5, 1.0, 0.5, 0.3],
    'weekend': [0.3, 0.2, 0.1, 0.1, 0.1, 0.3, 0.7, 1.0, 1.5, 1.8, 2.0, 1.8, 
                1.5, 1.3, 1.2, 1.0, 1.2, 1.5, 1.8, 2.0, 1.8, 1.5, 1.0, 0.5]
}

# Demand patterns by day of week (0-6, Monday-Sunday)
DAILY_DEMAND_PATTERNS = [1.0, 0.9, 0.9, 1.0, 1.2, 1.8, 1.5]  # Mon-Sun

# Seasonal demand multipliers by month (1-12)
MONTHLY_DEMAND_PATTERNS = [0.9, 0.9, 1.0, 1.0, 1.1, 1.0, 0.9, 0.9, 1.0, 1.2, 1.3, 1.2]

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'outputs/logs/warehouse_management.log'
}

# Database configuration
DATABASE_CONFIG = {
    'path': 'data/warehouse.db',
    'echo': False
}

# Simulation parameters
SIMULATION_CONFIG = {
    'default_duration': 60,  # minutes
    'default_events_per_minute': 10,
    'random_seed': 42
}

# Inventory thresholds
INVENTORY_THRESHOLDS = {
    'min_percent': 20,  # Minimum stock level (percentage of max capacity)
    'critical_percent': 10,  # Critical stock level (percentage of max capacity)
    'reorder_percent': 30  # Reorder level (percentage of max capacity)
}

# Optimization parameters
OPTIMIZATION_CONFIG = {
    'tsp_max_iterations': 1000,
    'tsp_temperature': 10.0,
    'tsp_cooling_rate': 0.995
}

# Reporting configuration
REPORTING_CONFIG = {
    'default_format': 'both',  # 'console', 'html', or 'both'
    'include_maps': True,
    'max_table_rows': 20,
    'html_template_dir': 'src/reports/templates'
}

# Visualization configuration
VISUALIZATION_CONFIG = {
    'default_width': 900,
    'default_height': 500,
    'color_palette': ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'],
    'map_center': [12.9716, 77.5946],  # Bangalore center
    'map_zoom': 11
}

# Sample data generation parameters
SAMPLE_DATA_CONFIG = {
    'num_products': 250,
    'num_warehouses': len(WAREHOUSE_AREAS),
    'num_pincodes': 50,
    'historical_days': 90,
    'events_per_day_range': (500, 2000)
}
