#!/usr/bin/env python3
"""
Script to clean up the outputs directory.
"""
import os
import sys
import shutil
import logging
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cleanup')

def clean_outputs_directory():
    """Clean up the outputs directory."""
    outputs_dir = os.path.join(project_root, 'outputs')
    logger.info(f"Cleaning outputs directory: {outputs_dir}")
    
    if os.path.exists(outputs_dir):
        # List all files before deletion
        files = list(Path(outputs_dir).rglob('*'))
        logger.info(f"Found {len(files)} files/directories to remove")
        
        # Remove all files and subdirectories
        shutil.rmtree(outputs_dir)
        logger.info("Outputs directory removed")
    
    # Recreate the outputs directory and subdirectories
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(os.path.join(outputs_dir, 'charts'), exist_ok=True)
    os.makedirs(os.path.join(outputs_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(outputs_dir, 'reports'), exist_ok=True)
    logger.info("Outputs directory and subdirectories recreated")
    
    return outputs_dir

def main():
    """Main function to run the cleanup process."""
    logger.info("=== Starting Cleanup Process ===")
    
    # Clean outputs directory
    clean_outputs_directory()
    
    logger.info("=== Cleanup Process Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
