"""
Analytics service for the warehouse management system.
Main entry point for analytics functionality.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.models.database import get_db
from src.models.product import Product
from src.models.warehouse import Warehouse
from src.models.inventory import Inventory
from src.models.events import PurchaseEvent, PincodeMapping

# Import specialized analytics modules
from src.services.analytics import (
    demand_forecasting,
    pattern_analysis,
    product_analytics,
    time_series_analysis
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analytics and insights."""
    
    def __init__(self, db: Session):
        """
        Initialize analytics service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def analyze_demand(self, warehouse_id: Optional[str] = None, 
                      days_back: int = 90) -> Dict[str, Any]:
        """
        Analyze demand patterns.
        
        Args:
            warehouse_id: Optional warehouse ID to filter by
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with demand analysis results
        """
        logger.info(f"Analyzing demand for past {days_back} days")
        
        # Get historical purchase data
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        query = self.db.query(PurchaseEvent).filter(PurchaseEvent.timestamp >= start_date)
        
        if warehouse_id and warehouse_id != 'all':
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
                'warehouse_fulfilled': event.warehouse_fulfilled,
                'delivery_time': event.delivery_time
            }
            for event in purchase_events
        ]
        
        # Get product details for all products in purchase events
        product_ids = {event.product_id for event in purchase_events}
        products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        product_map = {product.id: product for product in products}
        
        # Add product details to purchase data
        for item in purchase_data:
            product = product_map.get(item['product_id'])
            if product:
                item['product_name'] = product.name
                item['product_category'] = product.category
                item['product_subcategory'] = product.subcategory
        
        # Analyze demand patterns
        hourly_patterns = demand_forecasting.analyze_hourly_patterns(purchase_data)
        daily_patterns = demand_forecasting.analyze_daily_patterns(purchase_data)
        product_demand = product_analytics.analyze_product_demand(purchase_data)
        area_demand = pattern_analysis.analyze_area_demand(purchase_data, self.db)
        demand_forecast = demand_forecasting.forecast_demand(purchase_data, days=7)
        
        return {
            'hourly_patterns': hourly_patterns,
            'daily_patterns': daily_patterns,
            'product_demand': product_demand,
            'area_demand': area_demand,
            'demand_forecast': demand_forecast,
            'total_events': len(purchase_data),
            'total_quantity': sum(item['quantity'] for item in purchase_data),
            'analysis_period': {
                'start_date': start_date,
                'end_date': datetime.utcnow()
            }
        }
    
    def detect_anomalies(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Detect anomalies in purchase patterns.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of detected anomalies
        """
        logger.info(f"Detecting anomalies for past {days_back} days")
        
        # Get historical purchase data
        start_date = datetime.utcnow() - timedelta(days=days_back)
        purchase_events = (
            self.db.query(PurchaseEvent)
            .filter(PurchaseEvent.timestamp >= start_date)
            .all()
        )
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity,
                'customer_pincode': event.customer_pincode,
                'warehouse_fulfilled': event.warehouse_fulfilled,
                'delivery_time': event.delivery_time
            }
            for event in purchase_events
        ]
        
        # Detect anomalies using time series analysis
        return time_series_analysis.detect_anomalies(purchase_data)
    
    def get_product_insights(self, top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get insights about top and bottom performing products.
        
        Args:
            top_n: Number of top/bottom products to return
            
        Returns:
            Dictionary with top and bottom products
        """
        logger.info(f"Getting product insights for top/bottom {top_n} products")
        
        # Get purchase data for the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        purchase_events = (
            self.db.query(PurchaseEvent)
            .filter(PurchaseEvent.timestamp >= start_date)
            .all()
        )
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'product_id': event.product_id,
                'quantity': event.quantity
            }
            for event in purchase_events
        ]
        
        # Get product insights
        return product_analytics.get_product_insights(purchase_data, self.db, top_n)
    
    def get_area_insights(self) -> List[Dict[str, Any]]:
        """
        Get insights about demand by area.
        
        Returns:
            List of area insights
        """
        logger.info("Getting area insights")
        
        # Get purchase data for the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        purchase_events = (
            self.db.query(PurchaseEvent)
            .filter(PurchaseEvent.timestamp >= start_date)
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
        
        # Get area insights
        return pattern_analysis.get_area_insights(purchase_data, self.db)
    
    def get_time_series_data(self, interval: str = 'hourly', 
                           days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get time series data for demand.
        
        Args:
            interval: Time interval ('hourly', 'daily', 'weekly')
            days_back: Number of days to analyze
            
        Returns:
            List of time series data points
        """
        logger.info(f"Getting {interval} time series data for past {days_back} days")
        
        # Get historical purchase data
        start_date = datetime.utcnow() - timedelta(days=days_back)
        purchase_events = (
            self.db.query(PurchaseEvent)
            .filter(PurchaseEvent.timestamp >= start_date)
            .all()
        )
        
        # Convert to list of dictionaries
        purchase_data = [
            {
                'id': event.id,
                'timestamp': event.timestamp,
                'quantity': event.quantity
            }
            for event in purchase_events
        ]
        
        # Get time series data
        return time_series_analysis.get_time_series_data(purchase_data, interval)
