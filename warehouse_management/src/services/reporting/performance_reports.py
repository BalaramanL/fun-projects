"""
Performance reports module for the warehouse management system.

This module serves as an entry point for all performance-related reports.
"""
import logging
from typing import Optional

from src.services.reporting.warehouse_performance import WarehousePerformanceReports
from src.services.reporting.system_performance import SystemPerformanceReports
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class PerformanceReports:
    """Class for generating performance-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the performance reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
        self.warehouse_reports = WarehousePerformanceReports(self.report_generator)
        self.system_reports = SystemPerformanceReports(self.report_generator)
    
    # Warehouse performance reports
    def generate_warehouse_efficiency(self, *args, **kwargs):
        """Generate a warehouse efficiency report."""
        return self.warehouse_reports.generate_warehouse_efficiency(*args, **kwargs)
    
    def generate_capacity_utilization(self, *args, **kwargs):
        """Generate a warehouse capacity utilization report."""
        return self.warehouse_reports.generate_capacity_utilization(*args, **kwargs)
    
    # System performance reports
    def generate_system_metrics(self, *args, **kwargs):
        """Generate a system metrics report."""
        return self.system_reports.generate_system_metrics(*args, **kwargs)
    
    def generate_error_report(self, *args, **kwargs):
        """Generate a system error report."""
        return self.system_reports.generate_error_report(*args, **kwargs)
    
    def generate_resource_usage(self, *args, **kwargs):
        """Generate a resource usage report."""
        return self.system_reports.generate_resource_usage(*args, **kwargs)
