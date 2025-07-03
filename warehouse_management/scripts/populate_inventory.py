#!/usr/bin/env python
"""
Populate the database with sample inventory data.

This script adds sample inventory records to the database for demonstration purposes.
It requires products and warehouses to be populated first.
"""
import os
import sys
import logging
import sqlite3
import random
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def get_products_and_warehouses(conn):
    """Get all products and warehouses from the database."""
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT product_id FROM products")
    products = [row[0] for row in cursor.fetchall()]
    
    # Get all warehouses
    cursor.execute("SELECT warehouse_id FROM warehouses")
    warehouses = [row[0] for row in cursor.fetchall()]
    
    return products, warehouses

def populate_inventory(conn):
    """Populate the inventory table with sample data."""
    logger.info("Populating inventory table")
    
    cursor = conn.cursor()
    products, warehouses = get_products_and_warehouses(conn)
    
    if not products:
        logger.error("No products found in the database. Please run populate_products.py first.")
        return False
    
    if not warehouses:
        logger.error("No warehouses found in the database. Please run populate_warehouses.py first.")
        return False
    
    # For each warehouse, add inventory for a random subset of products
    inventory_records = []
    
    for warehouse_id in warehouses:
        # Select a random subset of products (60-90% of all products)
        num_products = int(len(products) * random.uniform(0.6, 0.9))
        warehouse_products = random.sample(products, num_products)
        
        for product_id in warehouse_products:
            # Generate random inventory data
            current_stock = random.randint(10, 1000)
            min_threshold = int(current_stock * random.uniform(0.1, 0.3))
            max_capacity = int(current_stock * random.uniform(1.2, 2.0))
            
            # Random last restock date within the last 30 days
            days_ago = random.randint(1, 30)
            last_restock_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            # 10% chance of having a stockout in the last 90 days
            last_stockout_date = None
            if random.random() < 0.1:
                stockout_days_ago = random.randint(1, 90)
                last_stockout_date = (datetime.now() - timedelta(days=stockout_days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            inventory_record = {
                "warehouse_id": warehouse_id,
                "product_id": product_id,
                "current_stock": current_stock,
                "min_threshold": min_threshold,
                "max_capacity": max_capacity,
                "last_updated": last_restock_date
            }
            
            inventory_records.append(inventory_record)
    
    # Check existing inventory records to avoid unique constraint violations
    cursor.execute("SELECT warehouse_id, product_id FROM inventory")
    existing_records = set()
    for row in cursor.fetchall():
        existing_records.add((row[0], row[1]))
    
    # Insert or update inventory records
    inserted_count = 0
    updated_count = 0
    
    for record in inventory_records:
        try:
            # Check if this warehouse-product combination already exists
            if (record["warehouse_id"], record["product_id"]) in existing_records:
                # Update existing record
                cursor.execute("""
                    UPDATE inventory SET 
                        current_stock = ?, 
                        min_threshold = ?, 
                        max_capacity = ?,
                        last_updated = ?
                    WHERE warehouse_id = ? AND product_id = ?
                """, (
                    record["current_stock"],
                    record["min_threshold"],
                    record["max_capacity"],
                    record["last_updated"],
                    record["warehouse_id"], 
                    record["product_id"]
                ))
                updated_count += 1
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO inventory (
                        warehouse_id, product_id, current_stock, min_threshold, max_capacity,
                        last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record["warehouse_id"], record["product_id"], record["current_stock"],
                    record["min_threshold"], record["max_capacity"],
                    record["last_updated"]
                ))
                inserted_count += 1
                existing_records.add((record["warehouse_id"], record["product_id"]))
        except sqlite3.Error as e:
            logger.error(f"Error managing inventory record: {e}")
    
    conn.commit()
    logger.info(f"Successfully processed {len(inventory_records)} inventory records (inserted: {inserted_count}, updated: {updated_count})")
    return True

def main():
    """Main function to populate inventory."""
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
        # Populate inventory
        success = populate_inventory(conn)
        if success:
            logger.info("Inventory population completed successfully")
            return 0
        else:
            logger.error("Inventory population failed")
            return 1
    except Exception as e:
        logger.error(f"Error populating inventory: {str(e)}", exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
