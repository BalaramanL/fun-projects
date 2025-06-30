#!/usr/bin/env python
"""
Populate the database with sample warehouse data.

This script adds sample warehouses to the database for demonstration purposes,
focusing on Bangalore locations.
"""
import os
import sys
import logging
import sqlite3
import random
import uuid
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Sample data for warehouses in Bangalore
BANGALORE_AREAS = [
    {"name": "Indiranagar", "pincode": "560038", "lat": 12.9784, "lng": 77.6408},
    {"name": "Koramangala", "pincode": "560034", "lat": 12.9279, "lng": 77.6271},
    {"name": "Whitefield", "pincode": "560066", "lat": 12.9698, "lng": 77.7499},
    {"name": "Electronic City", "pincode": "560100", "lat": 12.8399, "lng": 77.6770},
    {"name": "Marathahalli", "pincode": "560037", "lat": 12.9591, "lng": 77.6974},
    {"name": "Jayanagar", "pincode": "560041", "lat": 12.9299, "lng": 77.5933},
    {"name": "HSR Layout", "pincode": "560102", "lat": 12.9116, "lng": 77.6474},
    {"name": "BTM Layout", "pincode": "560076", "lat": 12.9166, "lng": 77.6101},
    {"name": "JP Nagar", "pincode": "560078", "lat": 12.9063, "lng": 77.5857},
    {"name": "Bannerghatta Road", "pincode": "560076", "lat": 12.8933, "lng": 77.5978}
]

def generate_manager_name():
    """Generate a random manager name."""
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Neha", "Raj", "Ananya", "Sanjay", "Meera"]
    last_names = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Joshi", "Reddy", "Nair", "Iyer", "Menon"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_phone_number():
    """Generate a random Indian phone number."""
    return f"+91 {random.randint(7000000000, 9999999999)}"

def generate_operational_hours():
    """Generate random operational hours."""
    start_hour = random.randint(6, 9)
    end_hour = random.randint(19, 23)
    return f"{start_hour:02d}:00-{end_hour:02d}:00"

def populate_warehouses(conn, num_warehouses=10):
    """Populate the warehouses table with sample data."""
    logger.info(f"Populating warehouses table with {num_warehouses} warehouses")
    
    cursor = conn.cursor()
    warehouses = []
    
    # Use all areas from BANGALORE_AREAS, and if more warehouses are needed, reuse areas
    areas = BANGALORE_AREAS.copy()
    if num_warehouses > len(areas):
        # Add variations of existing areas for additional warehouses
        for i in range(num_warehouses - len(areas)):
            base_area = random.choice(BANGALORE_AREAS)
            variation = {
                "name": f"{base_area['name']} {['North', 'South', 'East', 'West'][i % 4]}",
                "pincode": base_area['pincode'],
                # Slightly adjust lat/lng
                "lat": base_area['lat'] + random.uniform(-0.01, 0.01),
                "lng": base_area['lng'] + random.uniform(-0.01, 0.01)
            }
            areas.append(variation)
    
    # Shuffle areas to randomize selection if num_warehouses < len(areas)
    random.shuffle(areas)
    selected_areas = areas[:num_warehouses]
    
    for area in selected_areas:
        warehouse = {
            "warehouse_id": str(uuid.uuid4()),
            "name": f"BlinkIt {area['name']} Warehouse",
            "address": f"{random.randint(1, 100)}, {area['name']} Main Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": area['pincode'],
            "latitude": area['lat'],
            "longitude": area['lng'],
            "capacity_sqm": random.randint(500, 5000),
            "refrigerated_capacity_sqm": random.randint(50, 500),
            "operational_hours": generate_operational_hours(),
            "manager_name": generate_manager_name(),
            "contact_number": generate_phone_number()
        }
        
        warehouses.append(warehouse)
    
    # Insert warehouses into the database
    for warehouse in warehouses:
        try:
            cursor.execute("""
                INSERT INTO warehouses (
                    warehouse_id, name, address, city, state, pincode, 
                    latitude, longitude, capacity_sqm, refrigerated_capacity_sqm,
                    operational_hours, manager_name, contact_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                warehouse["warehouse_id"], warehouse["name"], warehouse["address"],
                warehouse["city"], warehouse["state"], warehouse["pincode"],
                warehouse["latitude"], warehouse["longitude"], warehouse["capacity_sqm"],
                warehouse["refrigerated_capacity_sqm"], warehouse["operational_hours"],
                warehouse["manager_name"], warehouse["contact_number"]
            ))
        except sqlite3.Error as e:
            logger.error(f"Error inserting warehouse {warehouse['name']}: {e}")
    
    conn.commit()
    logger.info(f"Successfully populated {len(warehouses)} warehouses")
    return warehouses

def main():
    """Main function to populate warehouses."""
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
        # Populate warehouses
        populate_warehouses(conn)
        logger.info("Warehouse population completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Error populating warehouses: {str(e)}", exc_info=True)
        return 1
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
