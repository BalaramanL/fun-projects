"""
Inventory service for the warehouse management system.
Provides functions for inventory management, alerts, and replenishment.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.models.database import get_db
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory, InventoryAlert
from src.config.constants import INVENTORY_THRESHOLDS
from src.utils.helpers import calculate_stock_percentage, get_alert_level, get_recommendation

logger = logging.getLogger(__name__)

class InventoryService:
    """Service for inventory management."""
    
    def __init__(self, db: Session):
        """
        Initialize inventory service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_inventory(self, warehouse_id: Optional[str] = None, 
                     product_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get inventory items with optional filtering.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            product_id: Optional product ID to filter by
            
        Returns:
            List of inventory items with product and warehouse details
        """
        query = (
            self.db.query(
                Inventory.warehouse_id,
                Inventory.product_id,
                Inventory.current_stock,
                Inventory.min_threshold,
                Inventory.max_capacity,
                Inventory.last_updated,
                Product.name.label('product_name'),
                Product.category.label('product_category'),
                Product.subcategory.label('product_subcategory'),
                Warehouse.name.label('warehouse_name'),
                Warehouse.area.label('warehouse_area')
            )
            .join(Product, Inventory.product_id == Product.id)
            .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        )
        
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)
        
        if product_id:
            query = query.filter(Inventory.product_id == product_id)
        
        inventory_items = query.all()
        
        # Convert to list of dictionaries
        result = []
        for item in inventory_items:
            item_dict = {
                'warehouse_id': item.warehouse_id,
                'product_id': item.product_id,
                'current_stock': item.current_stock,
                'min_threshold': item.min_threshold,
                'max_capacity': item.max_capacity,
                'last_updated': item.last_updated,
                'product_name': item.product_name,
                'product_category': item.product_category,
                'product_subcategory': item.product_subcategory,
                'warehouse_name': item.warehouse_name,
                'warehouse_area': item.warehouse_area,
                'stock_percentage': calculate_stock_percentage(item.current_stock, item.max_capacity)
            }
            result.append(item_dict)
        
        return result
    
    def update_inventory(self, warehouse_id: str, product_id: str, 
                        quantity_change: int) -> Dict[str, Any]:
        """
        Update inventory by adding or removing stock.
        
        Args:
            warehouse_id: Warehouse ID
            product_id: Product ID
            quantity_change: Quantity to add (positive) or remove (negative)
            
        Returns:
            Updated inventory item
        """
        # Get inventory item
        inventory_item = (
            self.db.query(Inventory)
            .filter(Inventory.warehouse_id == warehouse_id)
            .filter(Inventory.product_id == product_id)
            .first()
        )
        
        if not inventory_item:
            logger.error(f"Inventory item not found: warehouse_id={warehouse_id}, product_id={product_id}")
            raise ValueError(f"Inventory item not found")
        
        # Update stock
        new_stock = inventory_item.current_stock + quantity_change
        
        # Ensure stock doesn't go below zero
        if new_stock < 0:
            logger.warning(f"Attempted to reduce stock below zero: warehouse_id={warehouse_id}, "
                          f"product_id={product_id}, current={inventory_item.current_stock}, change={quantity_change}")
            new_stock = 0
        
        # Update inventory
        inventory_item.current_stock = new_stock
        inventory_item.last_updated = datetime.utcnow()
        
        # Commit changes
        self.db.commit()
        
        # Get updated item with details
        updated_item = self.get_inventory(warehouse_id, product_id)[0]
        
        # Log update
        logger.info(f"Updated inventory: warehouse={updated_item['warehouse_name']}, "
                   f"product={updated_item['product_name']}, "
                   f"new_stock={new_stock}, change={quantity_change}")
        
        return updated_item
    
    def get_alerts(self, threshold_percent: Optional[int] = None) -> List[InventoryAlert]:
        """
        Get inventory alerts for items below threshold.
        
        Args:
            threshold_percent: Optional threshold percentage override
            
        Returns:
            List of inventory alerts
        """
        # Use provided threshold or default from constants
        threshold = threshold_percent or INVENTORY_THRESHOLDS['min_percent']
        
        # Get all inventory items
        inventory_items = self.get_inventory()
        
        # Generate alerts
        alerts = []
        for item in inventory_items:
            stock_percentage = item['stock_percentage']
            alert_level = get_alert_level(stock_percentage)
            
            # Include all items for comprehensive reporting
            recommendation = get_recommendation(
                alert_level, 
                item['product_name'], 
                item['warehouse_name']
            )
            
            alert = InventoryAlert(
                warehouse_id=item['warehouse_id'],
                warehouse_name=item['warehouse_name'],
                product_id=item['product_id'],
                product_name=item['product_name'],
                current_stock=item['current_stock'],
                min_threshold=item['min_threshold'],
                max_capacity=item['max_capacity'],
                stock_percentage=stock_percentage,
                alert_level=alert_level,
                recommendation=recommendation
            )
            
            alerts.append(alert)
        
        return alerts
    
    def get_critical_alerts(self) -> List[InventoryAlert]:
        """
        Get critical inventory alerts.
        
        Returns:
            List of critical inventory alerts
        """
        all_alerts = self.get_alerts()
        return [alert for alert in all_alerts if alert.alert_level == "critical"]
    
    def calculate_restock_needs(self) -> List[Dict[str, Any]]:
        """
        Calculate restocking needs for all inventory items.
        
        Returns:
            List of restocking recommendations
        """
        # Get all inventory items
        inventory_items = self.get_inventory()
        
        # Calculate restocking needs
        restock_needs = []
        for item in inventory_items:
            stock_percentage = item['stock_percentage']
            
            # Check if restocking is needed
            if stock_percentage < INVENTORY_THRESHOLDS['reorder_percent']:
                # Calculate quantity to order
                target_stock = int(item['max_capacity'] * 0.8)  # Target 80% of capacity
                restock_quantity = target_stock - item['current_stock']
                
                if restock_quantity > 0:
                    restock_needs.append({
                        'warehouse_id': item['warehouse_id'],
                        'warehouse_name': item['warehouse_name'],
                        'product_id': item['product_id'],
                        'product_name': item['product_name'],
                        'current_stock': item['current_stock'],
                        'target_stock': target_stock,
                        'restock_quantity': restock_quantity,
                        'stock_percentage': stock_percentage,
                        'priority': 'high' if stock_percentage < INVENTORY_THRESHOLDS['critical_percent'] else 'medium'
                    })
        
        # Sort by priority and stock percentage
        restock_needs.sort(key=lambda x: (0 if x['priority'] == 'high' else 1, x['stock_percentage']))
        
        return restock_needs
    
    def get_product_distribution(self) -> List[Dict[str, Any]]:
        """
        Get product distribution across warehouses.
        
        Returns:
            List of product distribution data
        """
        # Get all inventory items
        inventory_items = self.get_inventory()
        
        # Group by product
        product_distribution = {}
        for item in inventory_items:
            product_id = item['product_id']
            product_name = item['product_name']
            
            if product_id not in product_distribution:
                product_distribution[product_id] = {
                    'product_id': product_id,
                    'product_name': product_name,
                    'total_stock': 0,
                    'warehouses': []
                }
            
            product_distribution[product_id]['total_stock'] += item['current_stock']
            product_distribution[product_id]['warehouses'].append({
                'warehouse_id': item['warehouse_id'],
                'warehouse_name': item['warehouse_name'],
                'current_stock': item['current_stock'],
                'stock_percentage': item['stock_percentage']
            })
        
        return list(product_distribution.values())
    
    def get_warehouse_capacity_usage(self) -> List[Dict[str, Any]]:
        """
        Get warehouse capacity usage.
        
        Returns:
            List of warehouse capacity usage data
        """
        # Query to get warehouse capacity usage
        query = (
            self.db.query(
                Warehouse.id,
                Warehouse.name,
                Warehouse.area,
                Warehouse.capacity,
                func.sum(Inventory.current_stock).label('total_stock')
            )
            .outerjoin(Inventory, Warehouse.id == Inventory.warehouse_id)
            .group_by(Warehouse.id)
        )
        
        warehouses = query.all()
        
        # Calculate usage
        result = []
        for warehouse in warehouses:
            # Assume each item takes 1 cubic unit of space on average
            # This is a simplification - in a real system, products would have dimensions
            total_stock = warehouse.total_stock or 0
            usage_percentage = (total_stock / warehouse.capacity) * 100 if warehouse.capacity > 0 else 0
            
            result.append({
                'warehouse_id': warehouse.id,
                'warehouse_name': warehouse.name,
                'warehouse_area': warehouse.area,
                'capacity': warehouse.capacity,
                'total_stock': total_stock,
                'usage_percentage': usage_percentage,
                'available_capacity': warehouse.capacity - total_stock
            })
        
        return result
