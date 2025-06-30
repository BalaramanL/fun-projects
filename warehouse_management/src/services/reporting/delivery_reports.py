"""
Delivery reports module for the warehouse management system.

This module provides functions for generating delivery-related reports.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

import pandas as pd
import numpy as np

from src.utils.helpers import get_db_session
from src.models.database import Order, Delivery, DeliveryAgent, Customer, Warehouse
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class DeliveryReports:
    """Class for generating delivery-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the delivery reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def generate_delivery_performance(self,
                                    start_date: Optional[datetime.date] = None,
                                    end_date: Optional[datetime.date] = None,
                                    warehouse_id: Optional[str] = None,
                                    output_format: str = 'json',
                                    filename: Optional[str] = None) -> str:
        """
        Generate a delivery performance report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            warehouse_id: Optional warehouse ID to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating delivery performance report")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 30 days
            start_date = end_date - datetime.timedelta(days=30)
        
        # Get delivery data
        delivery_data = self._get_delivery_data(start_date, end_date, warehouse_id)
        
        # Calculate performance metrics
        performance = self._calculate_delivery_performance(delivery_data)
        
        # Calculate daily delivery metrics
        daily_metrics = self._calculate_daily_delivery_metrics(delivery_data, start_date, end_date)
        
        # Prepare report data
        report_data = {
            "title": "Delivery Performance Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "warehouse_id": warehouse_id
            },
            "performance": performance,
            "daily_metrics": daily_metrics,
            "items": delivery_data,
            "generate_charts": True,
            "time_series_data": {
                "on_time_rate": {date: metrics["on_time_rate"] for date, metrics in daily_metrics.items()},
                "average_delivery_time": {date: metrics["average_delivery_time"] for date, metrics in daily_metrics.items()}
            },
            "pie_data": {
                status: sum(1 for delivery in delivery_data if delivery["status"] == status)
                for status in set(delivery["status"] for delivery in delivery_data)
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="delivery_performance",
            output_format=output_format,
            filename=filename
        )
    
    def generate_agent_performance(self,
                                 start_date: Optional[datetime.date] = None,
                                 end_date: Optional[datetime.date] = None,
                                 output_format: str = 'json',
                                 filename: Optional[str] = None) -> str:
        """
        Generate a delivery agent performance report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating delivery agent performance report")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 30 days
            start_date = end_date - datetime.timedelta(days=30)
        
        # Get delivery data
        delivery_data = self._get_delivery_data(start_date, end_date)
        
        # Calculate agent performance metrics
        agent_performance = self._calculate_agent_performance(delivery_data)
        
        # Prepare report data
        report_data = {
            "title": "Delivery Agent Performance Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_agents": len(agent_performance),
                "total_deliveries": len(delivery_data),
                "average_on_time_rate": sum(agent["on_time_rate"] for agent in agent_performance.values()) / len(agent_performance) if agent_performance else 0
            },
            "agent_performance": agent_performance,
            "generate_charts": True,
            "distribution_data": {
                "on_time_rates": [agent["on_time_rate"] for agent in agent_performance.values()],
                "delivery_times": [agent["average_delivery_time"] for agent in agent_performance.values()]
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="agent_performance",
            output_format=output_format,
            filename=filename
        )
    
    def _get_delivery_data(self,
                         start_date: datetime.date,
                         end_date: datetime.date,
                         warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get delivery data from the database.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            warehouse_id: Optional warehouse ID to filter by
            
        Returns:
            List of delivery dictionaries
        """
        try:
            with get_db_session() as session:
                # Convert dates to datetime for comparison
                start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                
                # Build query
                query = session.query(
                    Delivery, Order, DeliveryAgent, Customer, Warehouse
                ).join(
                    Order, Delivery.order_id == Order.id
                ).join(
                    DeliveryAgent, Delivery.agent_id == DeliveryAgent.id
                ).join(
                    Customer, Order.customer_id == Customer.id
                ).join(
                    Warehouse, Order.warehouse_id == Warehouse.id
                ).filter(
                    Delivery.dispatch_time >= start_datetime,
                    Delivery.dispatch_time <= end_datetime
                )
                
                # Apply warehouse filter if provided
                if warehouse_id:
                    query = query.filter(Order.warehouse_id == warehouse_id)
                
                # Execute query
                results = query.all()
                
                # Format results
                delivery_data = []
                for delivery, order, agent, customer, warehouse in results:
                    # Calculate delivery time in minutes
                    if delivery.actual_delivery_time and delivery.dispatch_time:
                        delivery_time = (delivery.actual_delivery_time - delivery.dispatch_time).total_seconds() / 60
                    else:
                        delivery_time = None
                    
                    # Check if delivery was on time
                    if delivery.actual_delivery_time and delivery.estimated_delivery_time:
                        # Allow 5 minute buffer
                        on_time = delivery.actual_delivery_time <= (delivery.estimated_delivery_time + datetime.timedelta(minutes=5))
                    else:
                        on_time = None
                    
                    # Add delivery to results
                    delivery_data.append({
                        "delivery_id": delivery.id,
                        "order_id": order.id,
                        "agent_id": agent.id,
                        "agent_name": agent.name,
                        "customer_id": customer.id,
                        "customer_name": customer.name,
                        "warehouse_id": warehouse.id,
                        "warehouse_name": warehouse.name,
                        "dispatch_time": delivery.dispatch_time.isoformat() if delivery.dispatch_time else None,
                        "estimated_delivery_time": delivery.estimated_delivery_time.isoformat() if delivery.estimated_delivery_time else None,
                        "actual_delivery_time": delivery.actual_delivery_time.isoformat() if delivery.actual_delivery_time else None,
                        "status": delivery.status,
                        "distance_km": delivery.distance_km,
                        "delivery_time_minutes": delivery_time,
                        "on_time": on_time
                    })
                
                return delivery_data
        except Exception as e:
            logger.error(f"Error getting delivery data: {str(e)}")
            return []
    
    def _calculate_delivery_performance(self, delivery_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate delivery performance metrics.
        
        Args:
            delivery_data: List of delivery dictionaries
            
        Returns:
            Dictionary with performance metrics
        """
        if not delivery_data:
            return {
                "total_deliveries": 0,
                "completed_deliveries": 0,
                "on_time_rate": 0,
                "average_delivery_time": 0,
                "average_distance": 0
            }
        
        # Filter completed deliveries
        completed_deliveries = [d for d in delivery_data if d["status"] == "delivered"]
        
        # Calculate metrics
        total_deliveries = len(delivery_data)
        completed_count = len(completed_deliveries)
        
        # On-time metrics (only for completed deliveries with timing data)
        timed_deliveries = [d for d in completed_deliveries if d["on_time"] is not None]
        on_time_count = sum(1 for d in timed_deliveries if d["on_time"])
        on_time_rate = on_time_count / len(timed_deliveries) if timed_deliveries else 0
        
        # Time and distance metrics
        delivery_times = [d["delivery_time_minutes"] for d in completed_deliveries if d["delivery_time_minutes"] is not None]
        average_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        distances = [d["distance_km"] for d in completed_deliveries if d["distance_km"] is not None]
        average_distance = sum(distances) / len(distances) if distances else 0
        
        return {
            "total_deliveries": total_deliveries,
            "completed_deliveries": completed_count,
            "completion_rate": completed_count / total_deliveries if total_deliveries > 0 else 0,
            "on_time_rate": on_time_rate,
            "average_delivery_time": average_delivery_time,
            "average_distance": average_distance
        }
    
    def _calculate_daily_delivery_metrics(self,
                                        delivery_data: List[Dict[str, Any]],
                                        start_date: datetime.date,
                                        end_date: datetime.date) -> Dict[str, Dict[str, Any]]:
        """
        Calculate delivery metrics by day.
        
        Args:
            delivery_data: List of delivery dictionaries
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping dates to metrics
        """
        # Initialize metrics for all days in range
        daily_metrics = {}
        current_date = start_date
        while current_date <= end_date:
            daily_metrics[current_date.isoformat()] = {
                "total_deliveries": 0,
                "completed_deliveries": 0,
                "on_time_deliveries": 0,
                "total_delivery_time": 0,
                "total_distance": 0,
                "on_time_rate": 0,
                "average_delivery_time": 0,
                "average_distance": 0
            }
            current_date += datetime.timedelta(days=1)
        
        # Group deliveries by date
        for delivery in delivery_data:
            if not delivery.get("dispatch_time"):
                continue
                
            delivery_date = datetime.datetime.fromisoformat(delivery["dispatch_time"]).date()
            date_str = delivery_date.isoformat()
            
            if date_str in daily_metrics:
                metrics = daily_metrics[date_str]
                metrics["total_deliveries"] += 1
                
                if delivery["status"] == "delivered":
                    metrics["completed_deliveries"] += 1
                    
                    if delivery["on_time"] is True:
                        metrics["on_time_deliveries"] += 1
                    
                    if delivery["delivery_time_minutes"] is not None:
                        metrics["total_delivery_time"] += delivery["delivery_time_minutes"]
                    
                    if delivery["distance_km"] is not None:
                        metrics["total_distance"] += delivery["distance_km"]
        
        # Calculate derived metrics
        for date, metrics in daily_metrics.items():
            if metrics["completed_deliveries"] > 0:
                metrics["on_time_rate"] = metrics["on_time_deliveries"] / metrics["completed_deliveries"]
                metrics["average_delivery_time"] = metrics["total_delivery_time"] / metrics["completed_deliveries"]
                metrics["average_distance"] = metrics["total_distance"] / metrics["completed_deliveries"]
        
        return daily_metrics
    
    def _calculate_agent_performance(self, delivery_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate performance metrics by delivery agent.
        
        Args:
            delivery_data: List of delivery dictionaries
            
        Returns:
            Dictionary mapping agent IDs to performance metrics
        """
        # Initialize agent performance data
        agent_performance = {}
        
        # Group deliveries by agent
        for delivery in delivery_data:
            agent_id = delivery["agent_id"]
            
            if agent_id not in agent_performance:
                agent_performance[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": delivery["agent_name"],
                    "total_deliveries": 0,
                    "completed_deliveries": 0,
                    "on_time_deliveries": 0,
                    "total_delivery_time": 0,
                    "total_distance": 0
                }
            
            performance = agent_performance[agent_id]
            performance["total_deliveries"] += 1
            
            if delivery["status"] == "delivered":
                performance["completed_deliveries"] += 1
                
                if delivery["on_time"] is True:
                    performance["on_time_deliveries"] += 1
                
                if delivery["delivery_time_minutes"] is not None:
                    performance["total_delivery_time"] += delivery["delivery_time_minutes"]
                
                if delivery["distance_km"] is not None:
                    performance["total_distance"] += delivery["distance_km"]
        
        # Calculate derived metrics
        for agent_id, performance in agent_performance.items():
            if performance["completed_deliveries"] > 0:
                performance["completion_rate"] = performance["completed_deliveries"] / performance["total_deliveries"]
                performance["on_time_rate"] = performance["on_time_deliveries"] / performance["completed_deliveries"]
                performance["average_delivery_time"] = performance["total_delivery_time"] / performance["completed_deliveries"]
                performance["average_distance"] = performance["total_distance"] / performance["completed_deliveries"]
            else:
                performance["completion_rate"] = 0
                performance["on_time_rate"] = 0
                performance["average_delivery_time"] = 0
                performance["average_distance"] = 0
        
        return agent_performance
