"""
Optimization service for the warehouse management system.
Provides functions for optimizing inventory, warehouse allocation, and delivery routes.
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory
from src.models.events import PurchaseEvent, PincodeMapping
from src.config.constants import OPTIMIZATION_CONFIG

# Import specialized optimization modules
from src.services.optimization import (
    inventory_optimization,
    warehouse_allocation,
    route_optimization,
    stock_balancing
)

logger = logging.getLogger(__name__)

class OptimizationService:
    """Service for optimization operations."""
    
    def __init__(self, db: Session):
        """
        Initialize optimization service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def optimize_inventory_levels(self, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Optimize inventory levels based on historical demand.
        
        Args:
            warehouse_id: Optional warehouse ID to optimize for
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Optimizing inventory levels for warehouse: {warehouse_id or 'all'}")
        
        # Get historical purchase data (last 90 days)
        start_date = datetime.utcnow() - timedelta(days=90)
        
        query = self.db.query(PurchaseEvent).filter(PurchaseEvent.timestamp >= start_date)
        
        if warehouse_id:
            query = query.filter(PurchaseEvent.warehouse_fulfilled == warehouse_id)
        
        purchase_events = query.all()
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity,
                'customer_pincode': event.customer_pincode,
                'warehouse_fulfilled': event.warehouse_fulfilled
            }
            for event in purchase_events
        ]
        
        # Get current inventory data
        inventory_query = self.db.query(Inventory)
        
        if warehouse_id:
            inventory_query = inventory_query.filter(Inventory.warehouse_id == warehouse_id)
        
        inventory_items = inventory_query.all()
        
        # Convert to list of dictionaries
        inventory_data = [
            {
                'warehouse_id': item.warehouse_id,
                'product_id': item.product_id,
                'current_stock': item.current_stock,
                'min_threshold': item.min_threshold,
                'max_capacity': item.max_capacity
            }
            for item in inventory_items
        ]
        
        # Get product data
        product_ids = {item['product_id'] for item in inventory_data}
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        
        # Convert to list of dictionaries
        product_data = [
            {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'subcategory': product.subcategory,
                'price': float(product.price),
                'shelf_life_days': product.shelf_life_days
            }
            for product in products
        ]
        
        # Optimize inventory levels
        return inventory_optimization.optimize_inventory_levels(
            purchase_data=purchase_data,
            inventory_data=inventory_data,
            product_data=product_data,
            config=OPTIMIZATION_CONFIG
        )
    
    def optimize_warehouse_allocation(self) -> Dict[str, Any]:
        """
        Optimize product allocation across warehouses.
        
        Returns:
            Dictionary with optimization results
        """
        logger.info("Optimizing warehouse allocation")
        
        # Get warehouse data
        warehouses = self.db.query(Warehouse).all()
        
        # Convert to list of dictionaries
        warehouse_data = [
            {
                'id': warehouse.id,
                'name': warehouse.name,
                'area': warehouse.area,
                'latitude': warehouse.latitude,
                'longitude': warehouse.longitude,
                'capacity': warehouse.capacity,
                'staff_count': warehouse.staff_count
            }
            for warehouse in warehouses
        ]
        
        # Get historical purchase data (last 90 days)
        start_date = datetime.utcnow() - timedelta(days=90)
        purchase_events = self.db.query(PurchaseEvent).filter(PurchaseEvent.timestamp >= start_date).all()
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity,
                'customer_pincode': event.customer_pincode,
                'warehouse_fulfilled': event.warehouse_fulfilled
            }
            for event in purchase_events
        ]
        
        # Get pincode mapping data
        pincode_mappings = self.db.query(PincodeMapping).all()
        
        # Convert to list of dictionaries
        pincode_data = [
            {
                'pincode': mapping.pincode,
                'area_name': mapping.area_name,
                'latitude': mapping.latitude,
                'longitude': mapping.longitude
            }
            for mapping in pincode_mappings
        ]
        
        # Optimize warehouse allocation
        return warehouse_allocation.optimize_allocation(
            warehouse_data=warehouse_data,
            purchase_data=purchase_data,
            pincode_data=pincode_data,
            config=OPTIMIZATION_CONFIG
        )
    
    def optimize_delivery_routes(self, warehouse_id: str) -> Dict[str, Any]:
        """
        Optimize delivery routes for a warehouse.
        
        Args:
            warehouse_id: Warehouse ID to optimize routes for
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Optimizing delivery routes for warehouse: {warehouse_id}")
        
        # Get warehouse data
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        
        if not warehouse:
            logger.error(f"Warehouse not found: {warehouse_id}")
            return {"error": "Warehouse not found"}
        
        # Get historical purchase data (last 30 days)
        start_date = datetime.utcnow() - timedelta(days=30)
        purchase_events = (
            self.db.query(PurchaseEvent)
            .filter(PurchaseEvent.timestamp >= start_date)
            .filter(PurchaseEvent.warehouse_fulfilled == warehouse_id)
            .all()
        )
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity,
                'customer_pincode': event.customer_pincode
            }
            for event in purchase_events
        ]
        
        # Get pincode mapping data
        pincodes = {event.customer_pincode for event in purchase_events}
        pincode_mappings = self.db.query(PincodeMapping).filter(PincodeMapping.pincode.in_(pincodes)).all()
        
        # Convert to list of dictionaries
        pincode_data = [
            {
                'pincode': mapping.pincode,
                'area_name': mapping.area_name,
                'latitude': mapping.latitude,
                'longitude': mapping.longitude
            }
            for mapping in pincode_mappings
        ]
        
        # Optimize delivery routes
        return route_optimization.optimize_routes(
            warehouse_data={
                'id': warehouse.id,
                'name': warehouse.name,
                'latitude': warehouse.latitude,
                'longitude': warehouse.longitude
            },
            purchase_data=purchase_data,
            pincode_data=pincode_data,
            config=OPTIMIZATION_CONFIG
        )
    
    def balance_stock_across_warehouses(self) -> Dict[str, Any]:
        """
        Balance stock levels across warehouses.
        
        Returns:
            Dictionary with stock balancing results
        """
        logger.info("Balancing stock across warehouses")
        
        # Get warehouse data
        warehouses = self.db.query(Warehouse).all()
        
        # Convert to list of dictionaries
        warehouse_data = [
            {
                'id': warehouse.id,
                'name': warehouse.name,
                'area': warehouse.area,
                'latitude': warehouse.latitude,
                'longitude': warehouse.longitude,
                'capacity': warehouse.capacity
            }
            for warehouse in warehouses
        ]
        
        # Get inventory data
        inventory_items = self.db.query(Inventory).all()
        
        # Convert to list of dictionaries
        inventory_data = [
            {
                'warehouse_id': item.warehouse_id,
                'product_id': item.product_id,
                'current_stock': item.current_stock,
                'min_threshold': item.min_threshold,
                'max_capacity': item.max_capacity
            }
            for item in inventory_items
        ]
        
        # Get product data
        product_ids = {item.product_id for item in inventory_items}
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        
        # Convert to list of dictionaries
        product_data = [
            {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'price': float(product.price),
                'shelf_life_days': product.shelf_life_days
            }
            for product in products
        ]
        
        # Get historical purchase data (last 30 days)
        start_date = datetime.utcnow() - timedelta(days=30)
        purchase_events = self.db.query(PurchaseEvent).filter(PurchaseEvent.timestamp >= start_date).all()
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity,
                'customer_pincode': event.customer_pincode,
                'warehouse_fulfilled': event.warehouse_fulfilled
            }
            for event in purchase_events
        ]
        
        # Balance stock across warehouses
        return stock_balancing.balance_stock(
            warehouse_data=warehouse_data,
            inventory_data=inventory_data,
            product_data=product_data,
            purchase_data=purchase_data,
            config=OPTIMIZATION_CONFIG
        )
