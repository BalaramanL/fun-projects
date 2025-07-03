#!/usr/bin/env python
"""
Database migration script for the warehouse management system.

This script migrates the existing database schema to match the ORM models.
It handles schema changes for inventory, product, warehouse, and customer tables.
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

def migrate_inventory_table(conn):
    """
    Migrate the inventory table to match the ORM model.
    
    Changes:
    - Rename 'quantity' to 'current_stock'
    - Rename 'max_threshold' to 'max_capacity'
    - Make warehouse_id and product_id the primary key
    - Remove inventory_id column
    - Add last_updated column
    """
    cursor = conn.cursor()
    
    try:
        # Check if the inventory table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
        if not cursor.fetchone():
            logger.warning("Inventory table does not exist. Nothing to migrate.")
            return True
        
        # Check if the table needs migration
        cursor.execute("PRAGMA table_info(inventory)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        # If the current_stock column already exists, no need to migrate
        if 'current_stock' in columns:
            logger.info("Inventory table already has current_stock column. No migration needed.")
            return True
        
        logger.info("Starting inventory table migration")
        
        # Create a new table with the correct schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory_new (
            warehouse_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            current_stock INTEGER NOT NULL,
            min_threshold INTEGER NOT NULL,
            max_capacity INTEGER NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id),
            PRIMARY KEY (warehouse_id, product_id)
        )
        """)
        
        # Copy data from the old table to the new table
        cursor.execute("""
        INSERT INTO inventory_new (warehouse_id, product_id, current_stock, min_threshold, max_capacity, last_updated)
        SELECT warehouse_id, product_id, quantity, min_threshold, max_threshold, 
               COALESCE(last_restock_date, CURRENT_TIMESTAMP) 
        FROM inventory
        """)
        
        # Drop the old table
        cursor.execute("DROP TABLE inventory")
        
        # Rename the new table to the original name
        cursor.execute("ALTER TABLE inventory_new RENAME TO inventory")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_warehouse ON inventory(warehouse_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id)")
        
        conn.commit()
        logger.info("Inventory table migration completed successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error migrating inventory table: {e}")
        conn.rollback()
        return False


def check_product_table(conn):
    """
    Check if the products table exists and log its schema.
    """
    cursor = conn.cursor()
    
    try:
        # Check if the products table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        if not cursor.fetchone():
            logger.warning("Products table does not exist.")
            return True
        
        # Log the table schema for debugging
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        logger.info(f"Products table schema: {columns}")
        
        # Drop any views we might have created earlier
        cursor.execute("DROP VIEW IF EXISTS products_view")
        
        conn.commit()
        logger.info("Products table check completed successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error checking products table: {e}")
        conn.rollback()
        return False


def check_warehouse_table(conn):
    """
    Check if the warehouses table exists and log its schema.
    """
    cursor = conn.cursor()
    
    try:
        # Check if the warehouses table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='warehouses'")
        if not cursor.fetchone():
            logger.warning("Warehouses table does not exist.")
            return True
        
        # Log the table schema for debugging
        cursor.execute("PRAGMA table_info(warehouses)")
        columns = cursor.fetchall()
        logger.info(f"Warehouses table schema: {columns}")
        
        # Drop any views we might have created earlier
        cursor.execute("DROP VIEW IF EXISTS warehouses_view")
        
        conn.commit()
        logger.info("Warehouses table check completed successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error checking warehouses table: {e}")
        conn.rollback()
        return False


def check_customer_table(conn):
    """
    Check if the customers table exists and log its schema.
    """
    cursor = conn.cursor()
    
    try:
        # Check if the customers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
        if not cursor.fetchone():
            logger.warning("Customers table does not exist.")
            return True
        
        # Log the table schema for debugging
        cursor.execute("PRAGMA table_info(customers)")
        columns = cursor.fetchall()
        logger.info(f"Customers table schema: {columns}")
        
        # Drop any views we might have created earlier
        cursor.execute("DROP VIEW IF EXISTS customers_view")
        
        conn.commit()
        logger.info("Customers table check completed successfully")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Error checking customers table: {e}")
        conn.rollback()
        return False

def main():
    """Main function to migrate the database."""
    # Default database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db')
    
    # Allow custom database path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}. Please run setup_database.py first.")
        return 1
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    try:
        # Migrate inventory table and check other tables
        inventory_success = migrate_inventory_table(conn)
        product_success = check_product_table(conn)
        warehouse_success = check_warehouse_table(conn)
        customer_success = check_customer_table(conn)
        
        if inventory_success and product_success and warehouse_success and customer_success:
            logger.info("Database migration completed successfully")
            return 0
        else:
            logger.error("Database migration failed for one or more tables")
            return 1
    except Exception as e:
        logger.error(f"Error migrating database: {str(e)}", exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
