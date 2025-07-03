"""
Order reports module for the warehouse management system.

This module provides functions for generating order-related reports.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict

import pandas as pd
import numpy as np

from src.utils.helpers import get_db_session
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.customer import Customer
from src.models.order import Order, OrderItem
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class OrderReports:
    """Class for generating order-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the order reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def generate_order_summary(self,
                             start_date: Optional[datetime.date] = None,
                             end_date: Optional[datetime.date] = None,
                             warehouse_id: Optional[str] = None,
                             output_format: str = 'json',
                             filename: Optional[str] = None) -> str:
        """
        Generate a summary report of orders.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            warehouse_id: Optional warehouse ID to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating order summary report")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 30 days
            start_date = end_date - datetime.timedelta(days=30)
        
        # Get order data
        order_data = self._get_order_data(start_date, end_date, warehouse_id)
        
        # Calculate summary statistics
        summary = self._calculate_order_summary(order_data)
        
        # Calculate daily order counts
        daily_orders = self._calculate_daily_orders(order_data, start_date, end_date)
        
        # Prepare report data
        report_data = {
            "title": "Order Summary Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "warehouse_id": warehouse_id
            },
            "summary": summary,
            "items": order_data,
            "generate_charts": True,
            "time_series_data": {
                "daily_orders": daily_orders
            },
            "pie_data": {
                status: sum(1 for order in order_data if order["status"] == status)
                for status in set(order["status"] for order in order_data)
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="order_summary",
            output_format=output_format,
            filename=filename
        )
    
    def generate_sales_report(self,
                            start_date: Optional[datetime.date] = None,
                            end_date: Optional[datetime.date] = None,
                            group_by: str = 'day',
                            output_format: str = 'json',
                            filename: Optional[str] = None) -> str:
        """
        Generate a sales report.
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            group_by: Grouping period ('day', 'week', 'month')
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info(f"Generating sales report (group_by: {group_by})")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.date.today()
        
        if not start_date:
            # Default to last 30 days for daily, 90 for weekly, 365 for monthly
            if group_by == 'day':
                start_date = end_date - datetime.timedelta(days=30)
            elif group_by == 'week':
                start_date = end_date - datetime.timedelta(days=90)
            else:  # month
                start_date = end_date - datetime.timedelta(days=365)
        
        # Get order data
        order_data = self._get_order_data(start_date, end_date)
        
        # Group sales by period
        sales_by_period = self._group_sales_by_period(order_data, group_by)
        
        # Calculate product category breakdown
        category_sales = self._calculate_category_sales(order_data)
        
        # Prepare report data
        report_data = {
            "title": "Sales Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by
            },
            "summary": {
                "total_sales": sum(order["total_amount"] for order in order_data),
                "total_orders": len(order_data),
                "average_order_value": sum(order["total_amount"] for order in order_data) / len(order_data) if order_data else 0
            },
            "sales_by_period": sales_by_period,
            "category_sales": category_sales,
            "generate_charts": True,
            "time_series_data": {
                "sales": {period: data["total_sales"] for period, data in sales_by_period.items()},
                "orders": {period: data["order_count"] for period, data in sales_by_period.items()}
            },
            "pie_data": {
                category: amount for category, amount in category_sales.items()
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="sales",
            output_format=output_format,
            filename=filename
        )
    
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
            # Return empty list if dates are None
            if not start_date or not end_date:
                logger.warning("Missing start_date or end_date, returning empty order data")
                return []
            with get_db_session() as session:
                # Convert dates to datetime for comparison
                start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
                
                # Build query
                query = session.query(
                    Order, Customer, Warehouse
                ).join(
                    Customer, Order.customer_id == Customer.customer_id
                ).join(
                    Warehouse, Order.warehouse_id == Warehouse.warehouse_id
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
                for order, customer, warehouse in results:
                    # Get order items
                    order_items = session.query(
                        OrderItem, Product
                    ).join(
                        Product, OrderItem.product_id == Product.product_id
                    ).filter(
                        OrderItem.order_id == order.order_id
                    ).all()
                    
                    # Format order items
                    items = []
                    for item, product in order_items:
                        # Skip None items or products
                        if item is None or product is None:
                            logger.warning("Skipping None order item or product")
                            continue
                            
                        try:
                            items.append({
                                "product_id": product.product_id,
                                "product_name": product.name,
                                "category": product.category,
                                "quantity": item.quantity,
                                "unit_price": item.unit_price,
                                "total_price": item.total_price
                            })
                        except Exception as e:
                            logger.warning(f"Error processing order item: {str(e)}")
                    
                    # Add order to results
                    order_data.append({
                        "order_id": order.order_id,
                        "customer_id": customer.customer_id,
                        "customer_name": customer.name,
                        "warehouse_id": warehouse.warehouse_id,
                        "warehouse_name": warehouse.name,
                        "order_date": order.order_date.isoformat(),
                        "status": order.status,
                        "total_amount": order.total_amount,
                        "items": items
                    })
                
                return order_data
        except Exception as e:
            logger.error(f"Error getting order data: {str(e)}")
            return []
    
    def _calculate_order_summary(self, order_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for order data.
        
        Args:
            order_data: List of order dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not order_data:
            return {
                "total_orders": 0,
                "total_sales": 0,
                "average_order_value": 0,
                "status_counts": {}
            }
        
        # Calculate basic metrics
        total_orders = len(order_data)
        total_sales = sum(order["total_amount"] for order in order_data)
        average_order_value = total_sales / total_orders
        
        # Count orders by status
        status_counts = defaultdict(int)
        for order in order_data:
            status_counts[order["status"]] += 1
        
        return {
            "total_orders": total_orders,
            "total_sales": total_sales,
            "average_order_value": average_order_value,
            "status_counts": dict(status_counts)
        }
    
    def _calculate_daily_orders(self,
                              order_data: List[Dict[str, Any]],
                              start_date: datetime.date,
                              end_date: datetime.date) -> Dict[str, int]:
        """
        Calculate daily order counts.
        
        Args:
            order_data: List of order dictionaries
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping dates to order counts
        """
        # Initialize counts for all days in range
        daily_counts = {}
        current_date = start_date
        while current_date <= end_date:
            daily_counts[current_date.isoformat()] = 0
            current_date += datetime.timedelta(days=1)
        
        # Count orders by date
        for order in order_data:
            order_date = datetime.datetime.fromisoformat(order["order_date"]).date()
            date_str = order_date.isoformat()
            if date_str in daily_counts:
                daily_counts[date_str] += 1
        
        return daily_counts
    
    def _group_sales_by_period(self,
                             order_data: List[Dict[str, Any]],
                             group_by: str) -> Dict[str, Dict[str, Any]]:
        """
        Group sales data by time period.
        
        Args:
            order_data: List of order dictionaries
            group_by: Grouping period ('day', 'week', 'month')
            
        Returns:
            Dictionary mapping periods to sales data
        """
        # Initialize results
        sales_by_period = {}
        
        # Group orders
        for order in order_data:
            order_datetime = datetime.datetime.fromisoformat(order["order_date"])
            
            # Determine period key
            if group_by == 'day':
                period_key = order_datetime.date().isoformat()
            elif group_by == 'week':
                # Use ISO week format (YYYY-WNN)
                year, week, _ = order_datetime.isocalendar()
                period_key = f"{year}-W{week:02d}"
            else:  # month
                period_key = f"{order_datetime.year}-{order_datetime.month:02d}"
            
            # Initialize period data if needed
            if period_key not in sales_by_period:
                sales_by_period[period_key] = {
                    "order_count": 0,
                    "total_sales": 0,
                    "items_sold": 0
                }
            
            # Update period data
            period_data = sales_by_period[period_key]
            period_data["order_count"] += 1
            period_data["total_sales"] += order["total_amount"]
            
            # Add defensive check for items
            try:
                # Sum quantities, skipping any items that don't have a quantity attribute
                items_sold = 0
                for item in order["items"]:
                    if item and "quantity" in item:
                        items_sold += item["quantity"]
                    else:
                        logger.warning(f"Skipping item without quantity in order {order.get('order_id', 'unknown')}")
                period_data["items_sold"] += items_sold
            except Exception as e:
                logger.warning(f"Error calculating items_sold: {str(e)}")
                # Default to 0 if calculation fails
                period_data["items_sold"] += 0
        
        # Sort by period key
        return dict(sorted(sales_by_period.items()))
    
    def _calculate_category_sales(self, order_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate sales by product category.
        
        Args:
            order_data: List of order dictionaries
            
        Returns:
            Dictionary mapping categories to sales amounts
        """
        category_sales = defaultdict(float)
        
        for order in order_data:
            for item in order["items"]:
                # Skip None items
                if not item:
                    logger.warning(f"Skipping None item in order {order.get('order_id', 'unknown')}")
                    continue
                    
                try:
                    category = item.get("category", "Unknown")
                    # Use get with default value to handle missing total_price
                    total_price = item.get("total_price", 0)
                    category_sales[category] += total_price
                except Exception as e:
                    logger.warning(f"Error processing category sales: {str(e)}")
                    continue
        
        return dict(category_sales)
