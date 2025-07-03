"""
System performance reports module for the warehouse management system.

This module provides functions for generating system-wide performance reports.
"""
import logging
import datetime
import os
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

import pandas as pd
import numpy as np

from src.utils.helpers import get_db_session
from src.models.events import SystemMetric, SystemLog
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class SystemPerformanceReports:
    """Class for generating system performance-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the system performance reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def generate_system_metrics(self,
                              start_date: Optional[datetime.date] = None,
                              end_date: Optional[datetime.date] = None,
                              metric_type: Optional[str] = None,
                              output_format: str = 'json',
                              filename: Optional[str] = None) -> str:
        """
        Generate a system metrics report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            metric_type: Optional metric type to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating system metrics report")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 7 days
            start_date = end_date - datetime.timedelta(days=7)
        
        # Get system metrics
        metrics_data = self._get_system_metrics(start_date, end_date, metric_type)
        
        # Calculate summary statistics
        summary = self._calculate_metrics_summary(metrics_data)
        
        # Calculate time series data
        time_series = self._calculate_metrics_time_series(metrics_data)
        
        # Prepare report data
        report_data = {
            "title": "System Metrics Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "metric_type": metric_type
            },
            "summary": summary,
            "items": metrics_data,
            "generate_charts": True,
            "time_series_data": time_series
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="system_metrics",
            output_format=output_format,
            filename=filename
        )
    
    def generate_error_report(self,
                            start_date: Optional[datetime.date] = None,
                            end_date: Optional[datetime.date] = None,
                            log_level: Optional[str] = "ERROR",
                            output_format: str = 'json',
                            filename: Optional[str] = None) -> str:
        """
        Generate a system error report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            log_level: Log level to filter by (default: ERROR)
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info(f"Generating system error report (log_level: {log_level})")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 7 days
            start_date = end_date - datetime.timedelta(days=7)
        
        # Get system logs
        log_data = self._get_system_logs(start_date, end_date, log_level)
        
        # Calculate error summary
        error_summary = self._calculate_error_summary(log_data)
        
        # Calculate error time series
        error_time_series = self._calculate_error_time_series(log_data)
        
        # Prepare report data
        report_data = {
            "title": "System Error Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "log_level": log_level
            },
            "summary": error_summary,
            "items": log_data,
            "generate_charts": True,
            "time_series_data": error_time_series
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="system_errors",
            output_format=output_format,
            filename=filename
        )
    
    def generate_resource_usage(self,
                              output_format: str = 'json',
                              filename: Optional[str] = None) -> str:
        """
        Generate a resource usage report.
        
        Args:
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating resource usage report")
        
        # Get current resource usage
        resource_data = self._get_resource_usage()
        
        # Prepare report data
        report_data = {
            "title": "Resource Usage Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "resources": resource_data,
            "generate_charts": True,
            "pie_data": {
                "CPU Usage": resource_data.get("cpu_percent", 0),
                "Memory Usage": resource_data.get("memory_percent", 0),
                "Disk Usage": resource_data.get("disk_percent", 0)
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="resource_usage",
            output_format=output_format,
            filename=filename
        )
    
    def _get_system_metrics(self,
                          start_date: datetime.date,
                          end_date: datetime.date,
                          metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get system metrics from the database.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            metric_type: Optional metric type to filter by
            
        Returns:
            List of metric dictionaries
        """
        try:
            with get_db_session() as session:
                # Convert dates to datetime for comparison
                start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                
                # Build query
                query = session.query(SystemMetric).filter(
                    SystemMetric.timestamp >= start_datetime,
                    SystemMetric.timestamp <= end_datetime
                )
                
                # Apply metric type filter if provided
                if metric_type:
                    query = query.filter(SystemMetric.metric_type == metric_type)
                
                # Execute query
                results = query.all()
                
                # Format results
                metrics_data = []
                for metric in results:
                    metrics_data.append({
                        "id": metric.id,
                        "metric_type": metric.metric_type,
                        "metric_name": metric.metric_name,
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat()
                    })
                
                return metrics_data
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return []
    
    def _get_system_logs(self,
                       start_date: datetime.date,
                       end_date: datetime.date,
                       log_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get system logs from the database.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            log_level: Optional log level to filter by
            
        Returns:
            List of log dictionaries
        """
        try:
            with get_db_session() as session:
                # Convert dates to datetime for comparison
                start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                
                # Build query
                query = session.query(SystemLog).filter(
                    SystemLog.timestamp >= start_datetime,
                    SystemLog.timestamp <= end_datetime
                )
                
                # Apply log level filter if provided
                if log_level:
                    query = query.filter(SystemLog.level == log_level)
                
                # Execute query
                results = query.all()
                
                # Format results
                log_data = []
                for log in results:
                    log_data.append({
                        "id": log.id,
                        "level": log.level,
                        "source": log.source,
                        "message": log.message,
                        "details": log.details,
                        "timestamp": log.timestamp.isoformat()
                    })
                
                return log_data
        except Exception as e:
            logger.error(f"Error getting system logs: {str(e)}")
            return []
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current system resource usage.
        
        Returns:
            Dictionary with resource usage metrics
        """
        resource_data = {
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            # Try to get CPU usage
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                resource_data.update({
                    "cpu_percent": cpu_percent,
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "memory_used": memory.used,
                    "memory_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_used": disk.used,
                    "disk_free": disk.free,
                    "disk_percent": disk.percent
                })
            except ImportError:
                logger.warning("psutil not installed. Using fallback resource metrics.")
                
                # Fallback to basic system information
                resource_data.update({
                    "cpu_count": os.cpu_count() or 0,
                    "memory_info": "psutil not available",
                    "disk_info": "psutil not available"
                })
            
            # Get database size if possible
            try:
                with get_db_session() as session:
                    # This is SQLite specific
                    result = session.execute("PRAGMA page_count").scalar()
                    page_count = int(result) if result is not None else 0
                    
                    result = session.execute("PRAGMA page_size").scalar()
                    page_size = int(result) if result is not None else 0
                    
                    db_size = page_count * page_size
                    
                    resource_data["database_size_bytes"] = db_size
                    resource_data["database_size_mb"] = db_size / (1024 * 1024)
            except Exception as e:
                logger.warning(f"Could not get database size: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error getting resource usage: {str(e)}")
        
        return resource_data
    
    def _calculate_metrics_summary(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for metrics data.
        
        Args:
            metrics_data: List of metric dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not metrics_data:
            return {
                "total_metrics": 0,
                "metric_types": [],
                "metric_names": []
            }
        
        # Group metrics by type and name
        metrics_by_type = defaultdict(list)
        metrics_by_name = defaultdict(list)
        
        for metric in metrics_data:
            metric_type = metric["metric_type"]
            metric_name = metric["metric_name"]
            value = metric["value"]
            
            metrics_by_type[metric_type].append(value)
            metrics_by_name[metric_name].append(value)
        
        # Calculate statistics for each type
        type_stats = {}
        for metric_type, values in metrics_by_type.items():
            type_stats[metric_type] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2]
            }
        
        # Calculate statistics for each name
        name_stats = {}
        for metric_name, values in metrics_by_name.items():
            name_stats[metric_name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "median": sorted(values)[len(values) // 2]
            }
        
        return {
            "total_metrics": len(metrics_data),
            "metric_types": dict(type_stats),
            "metric_names": dict(name_stats)
        }
    
    def _calculate_metrics_time_series(self, metrics_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate time series data for metrics.
        
        Args:
            metrics_data: List of metric dictionaries
            
        Returns:
            Dictionary mapping metric names to time series data
        """
        # Group metrics by name and timestamp
        time_series = defaultdict(dict)
        
        for metric in metrics_data:
            metric_name = metric["metric_name"]
            timestamp = metric["timestamp"]
            value = metric["value"]
            
            time_series[metric_name][timestamp] = value
        
        return dict(time_series)
    
    def _calculate_error_summary(self, log_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for error logs.
        
        Args:
            log_data: List of log dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not log_data:
            return {
                "total_errors": 0,
                "sources": [],
                "error_types": []
            }
        
        # Count errors by source
        errors_by_source = defaultdict(int)
        for log in log_data:
            source = log["source"]
            errors_by_source[source] += 1
        
        # Extract error types from messages
        error_types = defaultdict(int)
        for log in log_data:
            message = log["message"]
            
            # Simple heuristic to extract error type
            if ":" in message:
                error_type = message.split(":", 1)[0].strip()
                error_types[error_type] += 1
            else:
                error_types["Unknown"] += 1
        
        return {
            "total_errors": len(log_data),
            "sources": dict(errors_by_source),
            "error_types": dict(error_types)
        }
    
    def _calculate_error_time_series(self, log_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """
        Calculate time series data for errors.
        
        Args:
            log_data: List of log dictionaries
            
        Returns:
            Dictionary with time series data
        """
        # Group errors by date
        errors_by_date = defaultdict(int)
        errors_by_source_date = defaultdict(lambda: defaultdict(int))
        
        for log in log_data:
            timestamp = datetime.datetime.fromisoformat(log["timestamp"])
            date_str = timestamp.date().isoformat()
            source = log["source"]
            
            errors_by_date[date_str] += 1
            errors_by_source_date[source][date_str] += 1
        
        return {
            "total_errors": dict(errors_by_date),
            "by_source": {source: dict(dates) for source, dates in errors_by_source_date.items()}
        }
