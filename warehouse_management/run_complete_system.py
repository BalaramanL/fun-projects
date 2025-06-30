#!/usr/bin/env python
"""
Run the complete warehouse management system workflow.

This script provides a single entry point to run the entire warehouse management system,
including database setup, population, and all demo scenarios.

Usage:
    python run_complete_system.py [--skip-setup] [--skip-simulation] [--events-per-minute RATE]

Options:
    --skip-setup         Skip database setup and population
    --skip-simulation    Skip live event simulation
    --events-per-minute  Number of events to generate per minute (default: 10)
"""
import os
import sys
import time
import argparse
import logging
import subprocess
import threading
import signal

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global flag to control the simulation
running = True
simulation_process = None

def run_script(script_path, args=None, wait=True):
    """Run a Python script and return True if successful."""
    if not os.path.exists(script_path):
        logger.error(f"Script not found: {script_path}")
        return False
    
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running {os.path.basename(script_path)}...")
    
    try:
        if wait:
            result = subprocess.run(cmd, check=True)
            success = result.returncode == 0
        else:
            # Start process without waiting
            global simulation_process
            simulation_process = subprocess.Popen(cmd)
            success = simulation_process.poll() is None  # None means still running
        
        if success:
            logger.info(f"Successfully started {os.path.basename(script_path)}")
        else:
            logger.error(f"Failed to run {os.path.basename(script_path)}")
        
        return success
    except subprocess.SubprocessError as e:
        logger.error(f"Error running {os.path.basename(script_path)}: {str(e)}")
        return False

def signal_handler(sig, frame):
    """Handle interrupt signals to gracefully stop the simulation."""
    global running
    logger.info("Stopping simulation (Ctrl+C pressed)...")
    running = False
    
    # Terminate the simulation process if it exists
    if simulation_process and simulation_process.poll() is None:
        simulation_process.terminate()
        logger.info("Terminated simulation process")

def setup_database():
    """Run all database setup and population scripts."""
    logger.info("Setting up and populating the database...")
    
    # Run the combined setup script
    setup_script = os.path.join("scripts", "run_all_setup.py")
    if not run_script(setup_script):
        logger.error("Database setup failed")
        return False
    
    logger.info("Database setup and population completed successfully")
    return True

def run_simulation(events_per_minute):
    """Run the live event simulation in the background."""
    logger.info(f"Starting live event simulation with {events_per_minute} events per minute...")
    
    # Run the simulation script without waiting
    simulation_script = os.path.join("scripts", "simulate_live_events.py")
    return run_script(simulation_script, ["--events-per-minute", str(events_per_minute)], wait=False)

def run_demos():
    """Run all demo scripts in sequence."""
    logger.info("Running demo scenarios...")
    
    # Define the demo scripts to run in order
    demo_scripts = [
        os.path.join("src", "examples", "reporting_demo.py"),
        os.path.join("src", "examples", "simulation_demo.py"),
        os.path.join("src", "examples", "integration_demo.py"),
        os.path.join("src", "examples", "run_complete_workflow.py")
    ]
    
    # Run each demo script in sequence
    for script in demo_scripts:
        if not run_script(script):
            logger.warning(f"Demo script {os.path.basename(script)} failed")
        
        # Small delay between scripts
        time.sleep(1)
    
    logger.info("All demo scenarios completed")
    return True

def main():
    """Main function to run the complete warehouse management system."""
    global running
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the complete warehouse management system')
    parser.add_argument('--skip-setup', action='store_true', help='Skip database setup and population')
    parser.add_argument('--skip-simulation', action='store_true', help='Skip live event simulation')
    parser.add_argument('--events-per-minute', type=int, default=10, help='Number of events to generate per minute')
    args = parser.parse_args()
    
    try:
        # Step 1: Setup and populate the database
        if not args.skip_setup:
            if not setup_database():
                return 1
        else:
            logger.info("Skipping database setup as requested")
        
        # Step 2: Start the live event simulation
        if not args.skip_simulation:
            if not run_simulation(args.events_per_minute):
                logger.error("Failed to start simulation")
                return 1
        else:
            logger.info("Skipping live event simulation as requested")
        
        # Step 3: Run all demo scenarios
        if not run_demos():
            logger.warning("Some demo scenarios failed")
        
        # Keep the main thread alive if simulation is running
        if not args.skip_simulation:
            logger.info("All demos completed. Live simulation is still running.")
            logger.info("Press Ctrl+C to stop the simulation and exit.")
            
            while running and simulation_process and simulation_process.poll() is None:
                time.sleep(1)
        
        logger.info("Warehouse management system workflow completed")
        return 0
        
    except Exception as e:
        logger.error(f"Error running warehouse management system: {str(e)}", exc_info=True)
        return 1
    finally:
        # Ensure simulation process is terminated
        if simulation_process and simulation_process.poll() is None:
            simulation_process.terminate()
            logger.info("Terminated simulation process")

if __name__ == "__main__":
    sys.exit(main())
