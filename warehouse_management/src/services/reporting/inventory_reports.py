"""
Inventory reports module for the warehouse management system.

This module provides functions for generating inventory-related reports.
"""
import logging
import datetime
from typing import Dict, List, Any, Optional, Union

import pandas as pd
import numpy as np

from src.utils.helpers import get_db_session
from src.models.inventory import Inventory
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.services.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class InventoryReports:
    """Class for generating inventory-related reports."""
    
    def __init__(self, report_generator: Optional[ReportGenerator] = None):
        """
        Initialize the inventory reports generator.
        
        Args:
            report_generator: Report generator instance
        """
        self.report_generator = report_generator or ReportGenerator()
    
    def generate_inventory_snapshot(self, 
                                  warehouse_id: Optional[str] = None,
                                  category: Optional[str] = None,
                                  output_format: str = 'json',
                                  filename: Optional[str] = None) -> str:
        """
        Generate a snapshot report of current inventory levels.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            category: Optional product category to filter by
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info("Generating inventory snapshot report")
        
        # Get inventory data
        inventory_data = self._get_inventory_data(warehouse_id, category)
        
        # Calculate summary statistics
        summary = self._calculate_inventory_summary(inventory_data)
        
        # Prepare report data
        report_data = {
            "title": "Inventory Snapshot Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "filters": {
                "warehouse_id": warehouse_id,
                "category": category
            },
            "summary": summary,
            "items": inventory_data,
            "generate_charts": True,
            "pie_data": {
                category: sum(item["current_stock"] for item in inventory_data 
                             if item["category"] == category)
                for category in set(item["category"] for item in inventory_data)
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="inventory_snapshot",
            output_format=output_format,
            filename=filename
        )
    
    def generate_low_stock_report(self,
                                threshold_percent: float = 20.0,
                                output_format: str = 'json',
                                filename: Optional[str] = None) -> str:
        """
        Generate a report of products with low stock levels.
        
        Args:
            threshold_percent: Threshold percentage below which stock is considered low
            output_format: Output format ('json', 'csv', 'html', 'pdf')
            filename: Optional filename
            
        Returns:
            Path to the generated report file
        """
        logger.info(f"Generating low stock report (threshold: {threshold_percent}%)")
        
        # Get inventory data
        inventory_data = self._get_inventory_data()
        
        # Filter low stock items
        low_stock_items = []
        for item in inventory_data:
            stock_percent = (item["current_stock"] / item["max_capacity"]) * 100
            if stock_percent <= threshold_percent:
                item["stock_percent"] = stock_percent
                low_stock_items.append(item)
        
        # Sort by stock percentage
        low_stock_items.sort(key=lambda x: x["stock_percent"])
        
        # Calculate summary
        summary = {
            "total_low_stock_items": len(low_stock_items),
            "average_stock_percent": sum(item["stock_percent"] for item in low_stock_items) / len(low_stock_items) if low_stock_items else 0,
            "threshold_percent": threshold_percent
        }
        
        # Prepare report data
        report_data = {
            "title": "Low Stock Report",
            "generated_at": datetime.datetime.now().isoformat(),
            "summary": summary,
            "items": low_stock_items,
            "generate_charts": True,
            "pie_data": {
                "Low Stock Items": len(low_stock_items),
                "Normal Stock Items": len(inventory_data) - len(low_stock_items)
            }
        }
        
        # Generate report
        return self.report_generator.generate_report(
            data=report_data,
            report_type="low_stock",
            output_format=output_format,
            filename=filename
        )
    
    def _get_inventory_data(self, 
                          warehouse_id: Optional[str] = None,
                          category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get inventory data from the database.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            category: Optional product category to filter by
            
        Returns:
            List of inventory dictionaries
        """
        try:
            with get_db_session() as session:
                # Build query
                query = session.query(
                    Inventory, Product, Warehouse
                ).join(
                    Product, Inventory.product_id == Product.product_id
                ).join(
                    Warehouse, Inventory.warehouse_id == Warehouse.warehouse_id
                )
                
                # Apply filters
                if warehouse_id:
                    query = query.filter(Warehouse.warehouse_id == warehouse_id)
                
                if category:
                    query = query.filter(Product.category == category)
                
                # Execute query
                results = query.all()
                
                # Format results
                inventory_data = []
                for inv, product, warehouse in results:
                    # Skip if any of the objects are None
                    if inv is None or product is None or warehouse is None:
                        # Provide more detailed logging about which object is None
                        if inv is None:
                            logger.warning(f"Skipping inventory record: Inventory object is None")
                        if product is None:
                            logger.warning(f"Skipping inventory record: Product object is None for inventory_id={inv.inventory_id if inv else 'unknown'}")
                        if warehouse is None:
                            logger.warning(f"Skipping inventory record: Warehouse object is None for inventory_id={inv.inventory_id if inv else 'unknown'}")
                        continue
                    
                    # Additional validation for required fields
                    try:
                        # Verify all required attributes exist before using them
                        _ = inv.inventory_id
                        _ = inv.product_id
                        _ = inv.warehouse_id
                        _ = inv.current_stock
                        _ = inv.min_threshold
                        _ = inv.max_capacity
                        _ = product.product_id
                        _ = product.name
                        _ = product.category
                        _ = product.price
                        _ = warehouse.warehouse_id
                        _ = warehouse.name
                    except AttributeError as e:
                        logger.warning(f"Skipping inventory record due to missing attribute: {str(e)} for inventory_id={inv.inventory_id}")
                        continue
                    
                    inventory_data.append({
                        "inventory_id": inv.inventory_id,
                        "warehouse_id": warehouse.warehouse_id,
                        "warehouse_name": warehouse.name,
                        "product_id": product.product_id,
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
    
    def _calculate_inventory_summary(self, inventory_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate summary statistics for inventory data.
        
        Args:
            inventory_data: List of inventory dictionaries
            
        Returns:
            Dictionary with summary statistics
        """
        if not inventory_data:
            return {
                "total_items": 0,
                "total_value": 0,
                "average_stock_level": 0,
                "capacity_utilization": 0
            }
        
        total_items = len(inventory_data)
        total_value = sum(item["total_value"] for item in inventory_data)
        total_stock = sum(item["current_stock"] for item in inventory_data)
        total_capacity = sum(item["max_capacity"] for item in inventory_data)
        
        return {
            "total_items": total_items,
            "total_value": total_value,
            "total_stock": total_stock,
            "total_capacity": total_capacity,
            "average_stock_level": total_stock / total_items,
            "capacity_utilization": (total_stock / total_capacity) * 100 if total_capacity > 0 else 0
        }
