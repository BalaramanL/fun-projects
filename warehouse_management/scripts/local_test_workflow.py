#!/usr/bin/env python
"""
Local Test Workflow for Warehouse Management System

This script provides a modular approach to testing different components of the
warehouse management system without having to rebuild the Docker container each time.

Usage:
    python local_test_workflow.py [--setup] [--populate] [--simulate] [--report] [--all]

Options:
    --setup      Run database setup only
    --populate   Run database population only
    --simulate   Run live event simulation only
    --report     Run report generation only
    --all        Run all steps in sequence
"""

import os
import sys
import argparse
import subprocess
import logging
import time
from pathlib import Path

# Add the project root to sys.path to ensure modules can be imported
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths
SCRIPTS_DIR = BASE_DIR / "scripts"
EXAMPLES_DIR = BASE_DIR / "src" / "examples"
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [DATA_DIR, OUTPUTS_DIR]
    for subdir in ["logs", "reports", "charts"]:
        dirs.append(OUTPUTS_DIR / subdir)
    
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def run_command(command, description, cwd=BASE_DIR):
    """Run a shell command and log the output."""
    logger.info(f"Running {description}...")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        logger.info(f"{description} completed successfully")
        logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{description} failed with error: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def setup_database():
    """Run database setup."""
    return run_command(
        ["python", str(SCRIPTS_DIR / "run_all_setup.py")],
        "Database setup"
    )

def populate_database():
    """Run database population scripts."""
    scripts = [
        "populate_products.py",
        "populate_warehouses.py",
        "populate_customers_orders.py",
        "populate_inventory.py",
        "populate_delivery_agents.py"
    ]
    
    success = True
    for script in scripts:
        script_path = SCRIPTS_DIR / script
        if script_path.exists():
            if not run_command(["python", str(script_path)], f"Running {script}"):
                success = False
        else:
            logger.warning(f"Script {script} not found at {script_path}")
    
    return success

def run_simulation(duration=60):
    """Run live event simulation for a specified duration."""
    process = subprocess.Popen(
        ["python", str(SCRIPTS_DIR / "simulate_live_events.py"), "--events-per-minute", "5"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    logger.info(f"Started live event simulation (PID: {process.pid})")
    logger.info(f"Will run for {duration} seconds...")
    
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    finally:
        process.terminate()
        logger.info("Simulation terminated")
    
    return True

def run_reports():
    """Run all report generation examples."""
    examples = [
        "reporting_demo.py",
        "simulation_demo.py",
        "integration_demo.py",
        "run_complete_workflow.py"
    ]
    
    success = True
    for example in examples:
        example_path = EXAMPLES_DIR / example
        if example_path.exists():
            if not run_command(["python", str(example_path)], f"Running {example}"):
                success = False
        else:
            logger.warning(f"Example {example} not found at {example_path}")
    
    return success

def run_specific_report(report_name):
    """Run a specific report."""
    example_path = EXAMPLES_DIR / f"{report_name}.py"
    if example_path.exists():
        return run_command(["python", str(example_path)], f"Running {report_name}")
    else:
        logger.error(f"Report script {report_name}.py not found at {example_path}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Local test workflow for warehouse management system")
    parser.add_argument("--setup", action="store_true", help="Run database setup only")
    parser.add_argument("--populate", action="store_true", help="Run database population only")
    parser.add_argument("--simulate", action="store_true", help="Run live event simulation only")
    parser.add_argument("--report", action="store_true", help="Run report generation only")
    parser.add_argument("--specific-report", type=str, help="Run a specific report (e.g., reporting_demo)")
    parser.add_argument("--all", action="store_true", help="Run all steps in sequence")
    parser.add_argument("--sim-duration", type=int, default=60, help="Simulation duration in seconds")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Ensure directories exist
    ensure_directories()
    
    # Run requested steps
    if args.all or args.setup:
        if not setup_database():
            logger.error("Database setup failed, aborting further steps")
            return
    
    if args.all or args.populate:
        if not populate_database():
            logger.warning("Some database population steps failed")
    
    if args.all or args.simulate:
        run_simulation(args.sim_duration)
    
    if args.specific_report:
        run_specific_report(args.specific_report)
    elif args.all or args.report:
        if not run_reports():
            logger.warning("Some report generation steps failed")
    
    logger.info("Local test workflow completed")

if __name__ == "__main__":
    main()
