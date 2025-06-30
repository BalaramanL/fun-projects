#!/usr/bin/env python
"""
Run all setup and population scripts in sequence.

This script orchestrates the complete setup process for the warehouse management system:
1. Setup the database schema
2. Populate products
3. Populate warehouses
4. Populate inventory
5. Populate customers and orders

It can be used as an entrypoint in the Dockerfile to ensure all data is ready
before running demo scenarios.
"""
import os
import sys
import logging
import subprocess
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def run_script(script_name):
    """Run a Python script and return True if successful."""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running {script_name}...")
    
    try:
        result = subprocess.run([sys.executable, script_path], check=True)
        if result.returncode == 0:
            logger.info(f"Successfully completed {script_name}")
            return True
        else:
            logger.error(f"Failed to run {script_name}, return code: {result.returncode}")
            return False
    except subprocess.SubprocessError as e:
        logger.error(f"Error running {script_name}: {str(e)}")
        return False

def main():
    """Run all setup and population scripts in sequence."""
    logger.info("Starting complete database setup and population")
    
    # Define the scripts to run in order
    scripts = [
        "setup_database.py",
        "populate_products.py",
        "populate_warehouses.py",
        "populate_inventory.py",
        "populate_customers_orders.py"
    ]
    
    # Run each script in sequence
    for script in scripts:
        if not run_script(script):
            logger.error(f"Setup failed at {script}")
            return 1
        # Small delay between scripts
        time.sleep(1)
    
    logger.info("All setup and population scripts completed successfully")
    logger.info("The database is now ready for demo scenarios")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
