#!/usr/bin/env python3
"""
Script to clean up the outputs directory and run a complete workflow to verify all output reports.
"""
import os
import sys
import shutil
import logging
import subprocess
import time
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'verification.log'))
    ]
)
logger = logging.getLogger('verification')

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
    
    # Recreate the outputs directory
    os.makedirs(outputs_dir, exist_ok=True)
    logger.info("Outputs directory recreated")
    
    return outputs_dir

def run_workflow():
    """Run the complete workflow."""
    logger.info("Starting complete workflow")
    
    # Step 1: Setup database
    logger.info("Step 1: Setting up database")
    setup_script = os.path.join(project_root, 'scripts', 'setup_database.py')
    result = subprocess.run(['python', setup_script], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Database setup failed: {result.stderr}")
        return False
    logger.info("Database setup completed successfully")
    
    # Step 2: Populate database
    logger.info("Step 2: Populating database")
    populate_scripts = [
        'populate_warehouses.py',
        'populate_products.py',
        'populate_inventory.py',
        'populate_customers_orders.py',
        'populate_delivery_agents.py'
    ]
    
    for script in populate_scripts:
        script_path = os.path.join(project_root, 'scripts', script)
        if os.path.exists(script_path):
            logger.info(f"Running {script}")
            result = subprocess.run(['python', script_path], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"{script} failed: {result.stderr}")
                return False
            logger.info(f"{script} completed successfully")
        else:
            logger.warning(f"Script {script} not found, skipping")
    
    # Step 3: Run simulation
    logger.info("Step 3: Running simulation")
    simulation_script = os.path.join(project_root, 'examples', 'simulation_demo.py')
    result = subprocess.run(['python', simulation_script], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Simulation failed: {result.stderr}")
        return False
    logger.info("Simulation completed successfully")
    
    # Step 4: Generate reports
    logger.info("Step 4: Generating reports")
    reporting_script = os.path.join(project_root, 'examples', 'reporting_demo.py')
    result = subprocess.run(['python', reporting_script], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Report generation failed: {result.stderr}")
        return False
    logger.info("Report generation completed successfully")
    
    # Step 5: Run integration demo
    logger.info("Step 5: Running integration demo")
    integration_script = os.path.join(project_root, 'examples', 'integration_demo.py')
    result = subprocess.run(['python', integration_script], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Integration demo failed: {result.stderr}")
        return False
    logger.info("Integration demo completed successfully")
    
    return True

def verify_outputs():
    """Verify all expected output reports exist and have content."""
    outputs_dir = os.path.join(project_root, 'outputs')
    logger.info(f"Verifying outputs in: {outputs_dir}")
    
    # Expected report types
    expected_report_types = [
        'order_summary',
        'sales_report',
        'inventory_status',
        'delivery_performance',
        'warehouse_efficiency',
        'system_performance'
    ]
    
    # Expected formats
    expected_formats = ['html', 'json', 'csv']
    
    # Check for each expected report
    all_files = list(Path(outputs_dir).rglob('*'))
    logger.info(f"Found {len(all_files)} files in outputs directory")
    
    # Count reports by type
    report_counts = {report_type: 0 for report_type in expected_report_types}
    chart_count = 0
    
    for file_path in all_files:
        if file_path.is_file():
            # Check file size
            size = os.path.getsize(file_path)
            if size == 0:
                logger.warning(f"Empty file: {file_path}")
                continue
            
            # Check if it's a report
            for report_type in expected_report_types:
                if report_type in file_path.name:
                    report_counts[report_type] += 1
                    logger.info(f"Found {report_type} report: {file_path.name} ({size} bytes)")
            
            # Check if it's a chart
            if 'charts' in str(file_path) and file_path.suffix in ['.png', '.jpg', '.jpeg']:
                chart_count += 1
                logger.info(f"Found chart: {file_path.name} ({size} bytes)")
    
    # Log summary
    logger.info("=== Report Verification Summary ===")
    for report_type, count in report_counts.items():
        status = "✓" if count > 0 else "✗"
        logger.info(f"{status} {report_type}: {count} files")
    
    logger.info(f"Charts: {chart_count} files")
    
    # Check if all expected report types are present
    missing_reports = [report_type for report_type, count in report_counts.items() if count == 0]
    if missing_reports:
        logger.warning(f"Missing report types: {', '.join(missing_reports)}")
        return False
    
    return True

def main():
    """Main function to run the verification process."""
    logger.info("=== Starting Verification Process ===")
    
    # Step 1: Clean outputs directory
    clean_outputs_directory()
    
    # Step 2: Run complete workflow
    if not run_workflow():
        logger.error("Workflow execution failed")
        return 1
    
    # Step 3: Verify outputs
    if not verify_outputs():
        logger.warning("Output verification found issues")
        return 1
    
    logger.info("=== Verification Process Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
