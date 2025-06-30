"""
Reporting system demonstration for the warehouse management system.

This script demonstrates how to use the reporting modules to generate
various reports in different formats.
"""
import os
import logging
import datetime
from pathlib import Path

from src.services.reporting.report_generator import ReportGenerator
from src.services.reporting.inventory_reports import InventoryReports
from src.services.reporting.order_reports import OrderReports
from src.services.reporting.delivery_reports import DeliveryReports
from src.services.reporting.performance_reports import PerformanceReports
from src.utils.helpers import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Run the reporting system demonstration."""
    logger.info("Starting reporting system demonstration")
    
    # Create output directory for reports
    output_dir = Path("./outputs/reports")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Initialize report generator with custom templates directory
    report_generator = ReportGenerator(
        templates_dir=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    )
    
    # Initialize report modules
    inventory_reports = InventoryReports(report_generator)
    order_reports = OrderReports(report_generator)
    delivery_reports = DeliveryReports(report_generator)
    performance_reports = PerformanceReports(report_generator)
    
    # Set date range for reports
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    
    # Generate inventory reports
    logger.info("Generating inventory reports")
    inventory_snapshot_path = inventory_reports.generate_inventory_snapshot(
        output_format='html',
        filename=os.path.join(output_dir, "inventory_snapshot.html")
    )
    logger.info(f"Inventory snapshot report generated: {inventory_snapshot_path}")
    
    low_stock_path = inventory_reports.generate_low_stock_report(
        threshold_percent=20,
        output_format='html',
        filename=os.path.join(output_dir, "low_stock_report.html")
    )
    logger.info(f"Low stock report generated: {low_stock_path}")
    
    # Generate order reports
    logger.info("Generating order reports")
    order_summary_path = order_reports.generate_order_summary(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "order_summary.html")
    )
    logger.info(f"Order summary report generated: {order_summary_path}")
    
    sales_report_path = order_reports.generate_sales_report(
        start_date=start_date,
        end_date=end_date,
        group_by='day',
        output_format='html',
        filename=os.path.join(output_dir, "sales_report.html")
    )
    logger.info(f"Sales report generated: {sales_report_path}")
    
    # Generate delivery reports
    logger.info("Generating delivery reports")
    delivery_performance_path = delivery_reports.generate_delivery_performance(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "delivery_performance.html")
    )
    logger.info(f"Delivery performance report generated: {delivery_performance_path}")
    
    agent_performance_path = delivery_reports.generate_agent_performance(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "agent_performance.html")
    )
    logger.info(f"Agent performance report generated: {agent_performance_path}")
    
    # Generate performance reports
    logger.info("Generating performance reports")
    warehouse_efficiency_path = performance_reports.generate_warehouse_efficiency(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "warehouse_efficiency.html")
    )
    logger.info(f"Warehouse efficiency report generated: {warehouse_efficiency_path}")
    
    capacity_utilization_path = performance_reports.generate_capacity_utilization(
        output_format='html',
        filename=os.path.join(output_dir, "capacity_utilization.html")
    )
    logger.info(f"Capacity utilization report generated: {capacity_utilization_path}")
    
    system_metrics_path = performance_reports.generate_system_metrics(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "system_metrics.html")
    )
    logger.info(f"System metrics report generated: {system_metrics_path}")
    
    error_report_path = performance_reports.generate_error_report(
        start_date=start_date,
        end_date=end_date,
        output_format='html',
        filename=os.path.join(output_dir, "error_report.html")
    )
    logger.info(f"Error report generated: {error_report_path}")
    
    resource_usage_path = performance_reports.generate_resource_usage(
        output_format='html',
        filename=os.path.join(output_dir, "resource_usage.html")
    )
    logger.info(f"Resource usage report generated: {resource_usage_path}")
    
    # Generate reports in different formats
    logger.info("Generating reports in different formats")
    formats = ['json', 'csv', 'pdf']
    for fmt in formats:
        try:
            path = inventory_reports.generate_inventory_snapshot(
                output_format=fmt,
                filename=os.path.join(output_dir, f"inventory_snapshot.{fmt}")
            )
            logger.info(f"Inventory snapshot report generated in {fmt} format: {path}")
        except Exception as e:
            logger.error(f"Failed to generate {fmt} report: {str(e)}")
    
    logger.info("Reporting system demonstration completed")

if __name__ == "__main__":
    main()
