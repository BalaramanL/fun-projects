#!/usr/bin/env python3
"""
Script to verify all output reports exist and have content.
"""
import os
import sys
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
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'verification.log'))
    ]
)
logger = logging.getLogger('verification')

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
    
    # Verify outputs
    if not verify_outputs():
        logger.warning("Output verification found issues")
        return 1
    
    logger.info("=== Verification Process Completed Successfully ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
