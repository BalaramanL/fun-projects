"""
Warehouse performance reports module for the warehouse management system.

This module provides functions for generating warehouse performance-related reports.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

import pandas as pd
import numpy as np

from src.utils.helpers import get_db_session
from src.models.database import Warehouse, Order, Inventory, Product
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class WarehousePerformanceReports:
    """Class for generating warehouse performance-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the warehouse performance reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def generate_warehouse_efficiency(self,
                                    start_date: Optional[datetime.date] = None,
                                    end_date: Optional[datetime.date] = None,
                                    warehouse_id: Optional[str] = None,
                                    output_format: str = 'json',
                                    filename: Optional[str] = None) -> str:
        """
        Generate a warehouse efficiency report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            warehouse_id: Optional warehouse ID to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating warehouse efficiency report")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 30 days
            start_date = end_date - datetime.timedelta(days=30)
        
        # Get warehouse data
        warehouse_data = self._get_warehouse_data(warehouse_id)
        
        # Get order data for the period
        order_data = self._get_order_data(start_date, end_date, warehouse_id)
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics(warehouse_data, order_data)
        
        # Calculate daily metrics
        daily_metrics = self._calculate_daily_metrics(order_data, start_date, end_date)
        
        # Prepare report data
        report_data = {
            "title": "Warehouse Efficiency Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "warehouse_id": warehouse_id
            },
            "warehouses": warehouse_data,
            "efficiency_metrics": efficiency_metrics,
            "daily_metrics": daily_metrics,
            "generate_charts": True,
            "time_series_data": {
                "orders_per_day": {date: metrics["order_count"] for date, metrics in daily_metrics.items()},
                "items_per_day": {date: metrics["item_count"] for date, metrics in daily_metrics.items()}
            },
            "pie_data": {
                warehouse["name"]: metrics["total_orders"]
                for warehouse, metrics in efficiency_metrics.items()
                if "total_orders" in metrics
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="warehouse_efficiency",
            output_format=output_format,
            filename=filename
        )
    
    def generate_capacity_utilization(self,
                                    warehouse_id: Optional[str] = None,
                                    output_format: str = 'json',
                                    filename: Optional[str] = None) -> str:
        """
        Generate a warehouse capacity utilization report.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating warehouse capacity utilization report")
        
        # Get warehouse data
        warehouse_data = self._get_warehouse_data(warehouse_id)
        
        # Get inventory data
        inventory_data = self._get_inventory_data(warehouse_id)
        
        # Calculate capacity metrics
        capacity_metrics = self._calculate_capacity_metrics(warehouse_data, inventory_data)
        
        # Calculate category breakdown
        category_breakdown = self._calculate_category_breakdown(inventory_data)
        
        # Prepare report data
        report_data = {
            "title": "Warehouse Capacity Utilization Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "filters": {
                "warehouse_id": warehouse_id
            },
            "warehouses": warehouse_data,
            "capacity_metrics": capacity_metrics,
            "category_breakdown": category_breakdown,
            "generate_charts": True,
            "pie_data": {
                warehouse["name"]: metrics["utilization_percent"]
                for warehouse, metrics in capacity_metrics.items()
                if "utilization_percent" in metrics
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="capacity_utilization",
            output_format=output_format,
            filename=filename
        )
    
    def _get_warehouse_data(self, warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get warehouse data from the database.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            
        Returns:
            List of warehouse dictionaries
        """
        try:
            with get_db_session() as session:
                # Build query
                query = session.query(Warehouse)
                
                # Apply filter if provided
                if warehouse_id:
                    query = query.filter(Warehouse.id == warehouse_id)
                
                # Execute query
                results = query.all()
                
                # Format results
                warehouse_data = []
                for warehouse in results:
                    warehouse_data.append({
                        "id": warehouse.id,
                        "name": warehouse.name,
                        "address": warehouse.address,
                        "city": warehouse.city,
                        "state": warehouse.state,
                        "pincode": warehouse.pincode,
                        "latitude": warehouse.latitude,
                        "longitude": warehouse.longitude,
                        "capacity": warehouse.capacity,
                        "operating_hours": warehouse.operating_hours
                    })
                
                return warehouse_data
        except Exception as e:
            logger.error(f"Error getting warehouse data: {str(e)}")
            return []
    
    def _get_order_data(self,
                      start_date: datetime.date,
                      end_date: datetime.date,
                      warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get order data from the database.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            warehouse_id: Optional warehouse ID to filter by
            
        Returns:
            List of order dictionaries
        """
        try:
            with get_db_session() as session:
                # Convert dates to datetime for comparison
                start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                
                # Build query
                query = session.query(Order, Warehouse).join(
                    Warehouse, Order.warehouse_id == Warehouse.id
                ).filter(
                    Order.order_date >= start_datetime,
                    Order.order_date <= end_datetime
                )
                
                # Apply warehouse filter if provided
                if warehouse_id:
                    query = query.filter(Order.warehouse_id == warehouse_id)
                
                # Execute query
                results = query.all()
                
                # Format results
                order_data = []
                for order, warehouse in results:
                    # Get order items count
                    item_count = session.query(
                        func.sum(OrderItem.quantity)
                    ).filter(
                        OrderItem.order_id == order.id
                    ).scalar() or 0
                    
                    # Add order to results
                    order_data.append({
                        "order_id": order.id,
                        "warehouse_id": warehouse.id,
                        "warehouse_name": warehouse.name,
                        "order_date": order.order_date.isoformat(),
                        "status": order.status,
                        "total_amount": order.total_amount,
                        "item_count": item_count
                    })
                
                return order_data
        except Exception as e:
            logger.error(f"Error getting order data: {str(e)}")
            return []
    
    def _get_inventory_data(self, warehouse_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get inventory data from the database.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            
        Returns:
            List of inventory dictionaries
        """
        try:
            with get_db_session() as session:
                # Build query
                query = session.query(
                    Inventory, Product, Warehouse
                ).join(
                    Product, Inventory.product_id == Product.id
                ).join(
                    Warehouse, Inventory.warehouse_id == Warehouse.id
                )
                
                # Apply warehouse filter if provided
                if warehouse_id:
                    query = query.filter(Warehouse.id == warehouse_id)
                
                # Execute query
                results = query.all()
                
                # Format results
                inventory_data = []
                for inv, product, warehouse in results:
                    inventory_data.append({
                        "inventory_id": inv.id,
                        "warehouse_id": warehouse.id,
                        "warehouse_name": warehouse.name,
                        "product_id": product.id,
                        "product_name": product.name,
                        "category": product.category,
                        "current_stock": inv.current_stock,
                        "min_threshold": inv.min_threshold,
                        "max_capacity": inv.max_capacity,
                        "unit_price": product.price,
                        "total_value": product.price * inv.current_stock
                    })
                
                return inventory_data
        except Exception as e:
            logger.error(f"Error getting inventory data: {str(e)}")
            return []
    
    def _calculate_efficiency_metrics(self,
                                    warehouse_data: List[Dict[str, Any]],
                                    order_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate efficiency metrics for warehouses.
        
        Args:
            warehouse_data: List of warehouse dictionaries
            order_data: List of order dictionaries
            
        Returns:
            Dictionary mapping warehouse IDs to metrics
        """
        # Initialize metrics
        efficiency_metrics = {}
        for warehouse in warehouse_data:
            efficiency_metrics[warehouse["id"]] = {
                "name": warehouse["name"],
                "total_orders": 0,
                "total_items": 0,
                "total_value": 0,
                "orders_per_day": 0,
                "items_per_order": 0
            }
        
        # Group orders by warehouse
        warehouse_orders = defaultdict(list)
        for order in order_data:
            warehouse_orders[order["warehouse_id"]].append(order)
        
        # Calculate metrics for each warehouse
        for warehouse_id, orders in warehouse_orders.items():
            if warehouse_id not in efficiency_metrics:
                continue
                
            metrics = efficiency_metrics[warehouse_id]
            
            # Basic counts
            metrics["total_orders"] = len(orders)
            metrics["total_items"] = sum(order["item_count"] for order in orders)
            metrics["total_value"] = sum(order["total_amount"] for order in orders)
            
            # Calculate orders per day
            if orders:
                # Get date range
                order_dates = [datetime.datetime.fromisoformat(order["order_date"]).date() for order in orders]
                min_date = min(order_dates)
                max_date = max(order_dates)
                date_range = (max_date - min_date).days + 1
                
                metrics["orders_per_day"] = metrics["total_orders"] / date_range if date_range > 0 else metrics["total_orders"]
            
            # Calculate items per order
            metrics["items_per_order"] = metrics["total_items"] / metrics["total_orders"] if metrics["total_orders"] > 0 else 0
        
        return efficiency_metrics
    
    def _calculate_daily_metrics(self,
                               order_data: List[Dict[str, Any]],
                               start_date: datetime.date,
                               end_date: datetime.date) -> Dict[str, Dict[str, Any]]:
        """
        Calculate order metrics by day.
        
        Args:
            order_data: List of order dictionaries
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
                "order_count": 0,
                "item_count": 0,
                "total_value": 0
            }
            current_date += datetime.timedelta(days=1)
        
        # Group orders by date
        for order in order_data:
            order_date = datetime.datetime.fromisoformat(order["order_date"]).date()
            date_str = order_date.isoformat()
            
            if date_str in daily_metrics:
                metrics = daily_metrics[date_str]
                metrics["order_count"] += 1
                metrics["item_count"] += order["item_count"]
                metrics["total_value"] += order["total_amount"]
        
        return daily_metrics
    
    def _calculate_capacity_metrics(self,
                                  warehouse_data: List[Dict[str, Any]],
                                  inventory_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate capacity metrics for warehouses.
        
        Args:
            warehouse_data: List of warehouse dictionaries
            inventory_data: List of inventory dictionaries
            
        Returns:
            Dictionary mapping warehouse IDs to metrics
        """
        # Initialize metrics
        capacity_metrics = {}
        for warehouse in warehouse_data:
            capacity_metrics[warehouse["id"]] = {
                "name": warehouse["name"],
                "total_capacity": warehouse["capacity"],
                "current_stock": 0,
                "available_capacity": warehouse["capacity"],
                "utilization_percent": 0
            }
        
        # Group inventory by warehouse
        warehouse_inventory = defaultdict(list)
        for item in inventory_data:
            warehouse_inventory[item["warehouse_id"]].append(item)
        
        # Calculate metrics for each warehouse
        for warehouse_id, inventory in warehouse_inventory.items():
            if warehouse_id not in capacity_metrics:
                continue
                
            metrics = capacity_metrics[warehouse_id]
            
            # Calculate current stock
            metrics["current_stock"] = sum(item["current_stock"] for item in inventory)
            
            # Calculate available capacity
            metrics["available_capacity"] = metrics["total_capacity"] - metrics["current_stock"]
            
            # Calculate utilization percentage
            metrics["utilization_percent"] = (metrics["current_stock"] / metrics["total_capacity"]) * 100 if metrics["total_capacity"] > 0 else 0
        
        return capacity_metrics
    
    def _calculate_category_breakdown(self, inventory_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate inventory breakdown by product category.
        
        Args:
            inventory_data: List of inventory dictionaries
            
        Returns:
            Dictionary mapping warehouses to category breakdowns
        """
        # Initialize results
        category_breakdown = defaultdict(lambda: defaultdict(int))
        
        # Group by warehouse and category
        for item in inventory_data:
            warehouse_id = item["warehouse_id"]
            category = item["category"]
            
            category_breakdown[warehouse_id][category] += item["current_stock"]
        
        return {k: dict(v) for k, v in category_breakdown.items()}
