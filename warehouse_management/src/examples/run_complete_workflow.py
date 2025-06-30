"""
Complete Warehouse Management System Workflow

This script demonstrates the complete end-to-end workflow of the warehouse
management system, including simulation, reporting, and analytics.
"""
import os
import sys
import logging
import datetime
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.helpers import setup_logging
from src.examples.simulation_demo import main as run_simulation
from src.examples.reporting_demo import main as run_reporting
from src.examples.integration_demo import main as run_integration

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run the complete warehouse management system workflow'
    )
    parser.add_argument(
        '--mode',
        choices=['all', 'simulation', 'reporting', 'integration'],
        default='all',
        help='Which part of the workflow to run'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./outputs',
        help='Directory to store output files'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to simulate'
    )
    return parser.parse_args()

def main():
    """Run the complete warehouse management system workflow."""
    args = parse_arguments()
    
    logger.info("Starting complete warehouse management system workflow")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Simulation days: {args.days}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Set environment variables for the other scripts
    os.environ['SIMULATION_DAYS'] = str(args.days)
    os.environ['OUTPUT_DIR'] = str(output_dir)
    
    try:
        if args.mode in ['all', 'simulation']:
            logger.info("Running simulation workflow")
            run_simulation()
        
        if args.mode in ['all', 'reporting']:
            logger.info("Running reporting workflow")
            run_reporting()
        
        if args.mode in ['all', 'integration']:
            logger.info("Running integration workflow")
            run_integration()
        
        logger.info("Complete workflow finished successfully")
        
        # Print summary of generated files
        logger.info("\nSummary of generated files:")
        
        # Count files by type
        file_counts = {
            'data': 0,
            'reports': 0,
            'plots': 0
        }
        
        for subdir in ['simulation_data', 'integration_data']:
            data_dir = output_dir / subdir
            if data_dir.exists():
                files = list(data_dir.glob('*.*'))
                file_counts['data'] += len(files)
                logger.info(f"- {len(files)} data files in {subdir}")
        
        for subdir in ['reports', 'integration_reports']:
            reports_dir = output_dir / subdir
            if reports_dir.exists():
                files = list(reports_dir.glob('*.*'))
                file_counts['reports'] += len(files)
                logger.info(f"- {len(files)} report files in {subdir}")
        
        plots_dir = output_dir / 'plots'
        if plots_dir.exists():
            files = list(plots_dir.glob('*.*'))
            file_counts['plots'] += len(files)
            logger.info(f"- {len(files)} plot files in plots")
        
        logger.info(f"\nTotal files generated: {sum(file_counts.values())}")
        logger.info(f"- Data files: {file_counts['data']}")
        logger.info(f"- Report files: {file_counts['reports']}")
        logger.info(f"- Plot files: {file_counts['plots']}")
        
        logger.info("\nNext steps:")
        logger.info(f"1. View the HTML reports in {output_dir}/reports")
        logger.info(f"2. Analyze the data files in {output_dir}/simulation_data")
        logger.info(f"3. Examine the visualizations in {output_dir}/plots")
        
    except Exception as e:
        logger.error(f"Error running workflow: {str(e)}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
