#!/usr/bin/env python
"""
Database setup and initialization script for the warehouse management system.

This script:
1. Creates the SQLite database with SpatiaLite extension
2. Creates all necessary tables
3. Sets up indexes and constraints
"""
import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Database schema definitions
SCHEMA_DEFINITIONS = [
    # Products table
    """
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        subcategory TEXT,
        brand TEXT,
        price REAL NOT NULL,
        weight_grams INTEGER,
        volume_ml INTEGER,
        shelf_life_days INTEGER,
        requires_refrigeration INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Warehouses table
    """
    CREATE TABLE IF NOT EXISTS warehouses (
        warehouse_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        pincode TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        capacity_sqm REAL NOT NULL,
        refrigerated_capacity_sqm REAL,
        operational_hours TEXT,
        manager_name TEXT,
        contact_number TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Inventory table
    """
    CREATE TABLE IF NOT EXISTS inventory (
        inventory_id TEXT PRIMARY KEY,
        warehouse_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        current_stock INTEGER NOT NULL,
        min_threshold INTEGER NOT NULL,
        max_capacity INTEGER NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id),
        UNIQUE (warehouse_id, product_id)
    )
    """,
    
    # Orders table
    """
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        warehouse_id TEXT NOT NULL,
        order_date TIMESTAMP NOT NULL,
        shipping_address TEXT NOT NULL,
        shipping_pincode TEXT NOT NULL,
        delivery_address TEXT,
        delivery_latitude REAL,
        delivery_longitude REAL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
    )
    """,
    
    # Order items table
    """
    CREATE TABLE IF NOT EXISTS order_items (
        item_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        total_price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """,
    
    # Deliveries table
    """
    CREATE TABLE IF NOT EXISTS deliveries (
        delivery_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        agent_id TEXT NOT NULL,
        status TEXT NOT NULL,
        assigned_at TIMESTAMP,
        picked_up_at TIMESTAMP,
        delivered_at TIMESTAMP,
        delivery_time_minutes INTEGER,
        distance_km REAL,
        feedback_rating INTEGER,
        feedback_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    """,
    
    # Delivery agents table
    """
    CREATE TABLE IF NOT EXISTS delivery_agents (
        agent_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        contact_number TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        status TEXT NOT NULL,
        current_latitude REAL,
        current_longitude REAL,
        warehouse_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
    )
    """,
    
    # Inventory changes table
    """
    CREATE TABLE IF NOT EXISTS inventory_changes (
        change_id INTEGER PRIMARY KEY AUTOINCREMENT,
        warehouse_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        change_type TEXT NOT NULL,
        quantity_change INTEGER NOT NULL,
        reason TEXT,
        reference_id TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """,
    
    # System metrics table
    """
    CREATE TABLE IF NOT EXISTS system_metrics (
        metric_id TEXT PRIMARY KEY,
        metric_name TEXT NOT NULL,
        metric_value REAL NOT NULL,
        metric_unit TEXT NOT NULL,
        component TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # System logs table
    """
    CREATE TABLE IF NOT EXISTS system_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        level TEXT NOT NULL,
        source TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Customers table
    """
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT NOT NULL,
        address TEXT,
        pincode TEXT,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Pincode mapping table
    """
    CREATE TABLE IF NOT EXISTS pincode_mapping (
        pincode TEXT PRIMARY KEY,
        area_name TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

# Indexes for performance optimization
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
    "CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id)",
    "CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_orders_warehouse ON orders(warehouse_id)",
    "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
    "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_order ON deliveries(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_agent ON deliveries(agent_id)",
    "CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status)",
    "CREATE INDEX IF NOT EXISTS idx_inventory_changes_product ON inventory_changes(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_inventory_changes_warehouse ON inventory_changes(warehouse_id)",
    "CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics(metric_name)",
    "CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component)",
    "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level)",
    "CREATE INDEX IF NOT EXISTS idx_system_logs_source ON system_logs(source)",
    "CREATE INDEX IF NOT EXISTS idx_customers_pincode ON customers(pincode)"
]

def setup_database(db_path):
    """Set up the SQLite database with all required tables and indexes."""
    logger.info(f"Setting up database at {db_path}")
    
    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Delete the existing database file if it exists
    if os.path.exists(db_path):
        logger.info(f"Removing existing database file at {db_path}")
        os.remove(db_path)
    
    # Connect to the database (this will create a new file)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        for schema in SCHEMA_DEFINITIONS:
            cursor.execute(schema)
            
        # Create indexes
        for index in INDEXES:
            cursor.execute(index)
            
        # Commit changes
        conn.commit()
        logger.info("Database setup completed successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database setup failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Main function to set up the database."""
    # Default database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db')
    
    # Allow custom database path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    try:
        setup_database(db_path)
        return 0
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
