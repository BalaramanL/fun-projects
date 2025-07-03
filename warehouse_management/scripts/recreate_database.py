#!/usr/bin/env python
"""
Database recreation script for the warehouse management system.

This script drops and recreates the database from scratch using the current ORM models.
"""
import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging
from src.models.database import Base, engine
from src.config.settings import DATABASE_URI
from sqlalchemy import text, create_engine
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory
from src.models.order import Order, OrderItem
from src.models.delivery import Delivery, DeliveryAgent
from src.models.events import PurchaseEvent, PincodeMapping, SystemMetric, SystemLog
from src.models.customer import Customer

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def recreate_database():
    """Drop all tables and recreate them from the current ORM models."""
    try:
        # Check if database file exists
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db')
        if os.path.exists(db_path):
            logger.info(f"Database file found at {db_path}. Will be recreated.")
        else:
            logger.info(f"Database file not found at {db_path}. Will be created.")
        
        # Create engine
        engine = create_engine(DATABASE_URI)
        
        # Create a connection to execute raw SQL
        with engine.connect() as conn:
            # Disable foreign key constraints
            logger.info("Disabling foreign key constraints...")
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Drop all tables
            logger.info("Dropping all tables...")
            Base.metadata.drop_all(engine)
            
            # Enable foreign key constraints
            logger.info("Enabling foreign key constraints...")
            conn.execute(text("PRAGMA foreign_keys = ON"))
            
            # Create all tables
            logger.info("Creating all tables...")
            Base.metadata.create_all(engine)
        
        logger.info("Database recreated successfully.")
        return True
    except Exception as e:
        logger.error(f"Error recreating database: {str(e)}", exc_info=True)
        return False

def main():
    """Main function to recreate the database."""
    # Default database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'warehouse.db')
    
    # Allow custom database path from command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # Check if database exists
    if os.path.exists(db_path):
        logger.info(f"Database file found at {db_path}. Will be recreated.")
    else:
        logger.info(f"Database file not found at {db_path}. Will be created.")
    
    # Recreate the database
    if recreate_database():
        logger.info("Database recreation completed successfully")
        return 0
    else:
        logger.error("Database recreation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
