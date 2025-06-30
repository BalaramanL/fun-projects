"""
Settings module for the warehouse management system.
Loads environment variables and provides configuration settings.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database settings
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/warehouse.db')
DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, DATABASE_PATH)}"

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'outputs/logs/warehouse_management.log')
LOG_PATH = os.path.join(BASE_DIR, LOG_FILE)

# Simulation settings
SIMULATION_DURATION = int(os.getenv('DEFAULT_SIMULATION_DURATION', '60'))
EVENTS_PER_MINUTE = int(os.getenv('DEFAULT_EVENTS_PER_MINUTE', '10'))

# Reporting settings
OUTPUT_FORMAT = os.getenv('DEFAULT_OUTPUT_FORMAT', 'both')
INCLUDE_MAPS = os.getenv('INCLUDE_MAPS', 'true').lower() == 'true'

# Warehouse settings
MIN_STOCK_THRESHOLD = int(os.getenv('MIN_STOCK_THRESHOLD_PERCENT', '20'))
CRITICAL_STOCK_THRESHOLD = int(os.getenv('CRITICAL_STOCK_THRESHOLD_PERCENT', '10'))

# Ensure directories exist
os.makedirs(os.path.dirname(os.path.join(BASE_DIR, DATABASE_PATH)), exist_ok=True)
os.makedirs(os.path.dirname(os.path.join(BASE_DIR, LOG_FILE)), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'outputs', 'reports'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'outputs', 'plots'), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'data', 'exports'), exist_ok=True)

# Configure logging
def setup_logging() -> None:
    """
    Configure the logging system based on environment settings.
    """
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(LOG_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_PATH),
            logging.StreamHandler()
        ]
    )
    
    # Log startup information
    logging.info(f"Warehouse Management System starting up")
    logging.info(f"Database path: {DATABASE_PATH}")
    logging.info(f"Log level: {LOG_LEVEL}")
    logging.info(f"Log file: {LOG_PATH}")

# Export settings as a dictionary
def get_settings() -> Dict[str, Any]:
    """
    Return all settings as a dictionary.
    
    Returns:
        Dict[str, Any]: Dictionary containing all settings
    """
    return {
        'DATABASE_URI': DATABASE_URI,
        'LOG_LEVEL': LOG_LEVEL,
        'LOG_FILE': LOG_PATH,
        'SIMULATION_DURATION': SIMULATION_DURATION,
        'EVENTS_PER_MINUTE': EVENTS_PER_MINUTE,
        'OUTPUT_FORMAT': OUTPUT_FORMAT,
        'INCLUDE_MAPS': INCLUDE_MAPS,
        'MIN_STOCK_THRESHOLD': MIN_STOCK_THRESHOLD,
        'CRITICAL_STOCK_THRESHOLD': CRITICAL_STOCK_THRESHOLD,
    }
