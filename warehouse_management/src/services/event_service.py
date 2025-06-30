"""
Event handling service for the warehouse management system.

This service handles various events in the system, including:
- Order events (placement, fulfillment, cancellation)
- Inventory events (stock updates, transfers)
- Delivery events (dispatch, delivery, failed delivery)
- System events (alerts, notifications)
"""
import logging
import json
import datetime
from typing import Dict, List, Any, Optional, Callable, Union
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field, validator

from src.models.database import Order, Inventory, Delivery, SystemEvent
from src.utils.helpers import get_db_session

logger = logging.getLogger(__name__)

class EventBase(BaseModel):
    """Base class for all events."""
    event_type: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrderEvent(EventBase):
    """Order event model."""
    order_id: str
    customer_id: str
    status: str
    items: List[Dict[str, Any]]
    total_amount: float

class InventoryEvent(EventBase):
    """Inventory event model."""
    warehouse_id: str
    product_id: str
    quantity_change: int
    current_quantity: int
    reason: str

class DeliveryEvent(EventBase):
    """Delivery event model."""
    delivery_id: str
    order_id: str
    warehouse_id: str
    status: str
    location: Optional[Dict[str, float]] = None
    agent_id: Optional[str] = None

class SystemAlertEvent(EventBase):
    """System alert event model."""
    alert_level: str
    message: str
    component: str
    requires_action: bool = False
    action_by: Optional[str] = None


class EventService:
    """Service for handling events in the warehouse management system."""
    
    def __init__(self):
        """Initialize the event service."""
        self.handlers = defaultdict(list)
        self._register_default_handlers()
        logger.info("EventService initialized")
    
    def _register_default_handlers(self):
        """Register default event handlers."""
        # Order events
        self.register_handler("order.placed", self._handle_order_placed)
        self.register_handler("order.fulfilled", self._handle_order_fulfilled)
        self.register_handler("order.cancelled", self._handle_order_cancelled)
        
        # Inventory events
        self.register_handler("inventory.updated", self._handle_inventory_updated)
        self.register_handler("inventory.critical", self._handle_inventory_critical)
        self.register_handler("inventory.transfer", self._handle_inventory_transfer)
        
        # Delivery events
        self.register_handler("delivery.dispatched", self._handle_delivery_dispatched)
        self.register_handler("delivery.completed", self._handle_delivery_completed)
        self.register_handler("delivery.failed", self._handle_delivery_failed)
        
        # System events
        self.register_handler("system.alert", self._handle_system_alert)
        self.register_handler("system.notification", self._handle_system_notification)
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register a handler for a specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Function to call when event occurs
        """
        self.handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")
    
    def publish_event(self, event_type: str, event_data: Union[Dict[str, Any], BaseModel]) -> bool:
        """
        Publish an event to all registered handlers.
        
        Args:
            event_type: Type of event to publish
            event_data: Event data as dictionary or Pydantic model
            
        Returns:
            True if event was handled by at least one handler, False otherwise
        """
        if isinstance(event_data, BaseModel):
            event_dict = event_data.dict()
        else:
            event_dict = event_data
        
        # Add event type if not present
        if "event_type" not in event_dict:
            event_dict["event_type"] = event_type
        
        # Add timestamp if not present
        if "timestamp" not in event_dict:
            event_dict["timestamp"] = datetime.datetime.now().isoformat()
        
        logger.info(f"Publishing event: {event_type}")
        logger.debug(f"Event data: {event_dict}")
        
        # Get handlers for this event type
        event_handlers = self.handlers.get(event_type, [])
        
        if not event_handlers:
            logger.warning(f"No handlers registered for event type: {event_type}")
            return False
        
        # Call all handlers
        for handler in event_handlers:
            try:
                handler(event_dict)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {str(e)}")
        
        # Store event in database
        self._store_event(event_type, event_dict)
        
        return True
    
    def _store_event(self, event_type: str, event_data: Dict[str, Any]):
        """
        Store event in database.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        try:
            with get_db_session() as session:
                # Create system event
                system_event = SystemEvent(
                    event_type=event_type,
                    event_data=json.dumps(event_data),
                    timestamp=datetime.datetime.now(),
                    source=event_data.get("source", "system")
                )
                session.add(system_event)
                session.commit()
        except Exception as e:
            logger.error(f"Error storing event in database: {str(e)}")
    
    def get_events(self, 
                  event_type: Optional[str] = None, 
                  start_time: Optional[datetime.datetime] = None,
                  end_time: Optional[datetime.datetime] = None,
                  source: Optional[str] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get events from database with optional filtering.
        
        Args:
            event_type: Filter by event type
            start_time: Filter by start time
            end_time: Filter by end time
            source: Filter by source
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        try:
            with get_db_session() as session:
                query = session.query(SystemEvent)
                
                # Apply filters
                if event_type:
                    query = query.filter(SystemEvent.event_type == event_type)
                
                if start_time:
                    query = query.filter(SystemEvent.timestamp >= start_time)
                
                if end_time:
                    query = query.filter(SystemEvent.timestamp <= end_time)
                
                if source:
                    query = query.filter(SystemEvent.source == source)
                
                # Order by timestamp (newest first) and limit
                query = query.order_by(SystemEvent.timestamp.desc()).limit(limit)
                
                # Get results
                events = []
                for event in query.all():
                    event_dict = {
                        "id": event.id,
                        "event_type": event.event_type,
                        "timestamp": event.timestamp.isoformat(),
                        "source": event.source,
                        "data": json.loads(event.event_data)
                    }
                    events.append(event_dict)
                
                return events
        except Exception as e:
            logger.error(f"Error getting events from database: {str(e)}")
            return []
    
    def get_event_stats(self, 
                       start_time: Optional[datetime.datetime] = None,
                       end_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Get event statistics.
        
        Args:
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            Dictionary with event statistics
        """
        try:
            with get_db_session() as session:
                query = session.query(SystemEvent)
                
                # Apply time filters
                if start_time:
                    query = query.filter(SystemEvent.timestamp >= start_time)
                
                if end_time:
                    query = query.filter(SystemEvent.timestamp <= end_time)
                
                # Get total count
                total_count = query.count()
                
                # Get counts by event type
                event_type_counts = {}
                for event_type, count in session.query(
                    SystemEvent.event_type, 
                    func.count(SystemEvent.id)
                ).filter(
                    *[SystemEvent.timestamp >= start_time] if start_time else [],
                    *[SystemEvent.timestamp <= end_time] if end_time else []
                ).group_by(SystemEvent.event_type).all():
                    event_type_counts[event_type] = count
                
                # Get counts by source
                source_counts = {}
                for source, count in session.query(
                    SystemEvent.source, 
                    func.count(SystemEvent.id)
                ).filter(
                    *[SystemEvent.timestamp >= start_time] if start_time else [],
                    *[SystemEvent.timestamp <= end_time] if end_time else []
                ).group_by(SystemEvent.source).all():
                    source_counts[source] = count
                
                return {
                    "total_count": total_count,
                    "by_event_type": event_type_counts,
                    "by_source": source_counts,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None
                }
        except Exception as e:
            logger.error(f"Error getting event statistics: {str(e)}")
            return {
                "total_count": 0,
                "by_event_type": {},
                "by_source": {},
                "error": str(e)
            }
    
    # Default event handlers
    
    def _handle_order_placed(self, event_data: Dict[str, Any]):
        """Handle order placed event."""
        logger.info(f"Order placed: {event_data.get('order_id')}")
        # Implementation would update order status in database
        # and trigger inventory reservation
    
    def _handle_order_fulfilled(self, event_data: Dict[str, Any]):
        """Handle order fulfilled event."""
        logger.info(f"Order fulfilled: {event_data.get('order_id')}")
        # Implementation would update order status in database
    
    def _handle_order_cancelled(self, event_data: Dict[str, Any]):
        """Handle order cancelled event."""
        logger.info(f"Order cancelled: {event_data.get('order_id')}")
        # Implementation would update order status in database
        # and release reserved inventory
    
    def _handle_inventory_updated(self, event_data: Dict[str, Any]):
        """Handle inventory updated event."""
        logger.info(f"Inventory updated: {event_data.get('product_id')} in warehouse {event_data.get('warehouse_id')}")
        # Implementation would check for low stock levels
        # and trigger alerts if necessary
    
    def _handle_inventory_critical(self, event_data: Dict[str, Any]):
        """Handle inventory critical event."""
        logger.info(f"Inventory critical: {event_data.get('product_id')} in warehouse {event_data.get('warehouse_id')}")
        # Implementation would trigger restock order
        # and notify warehouse manager
    
    def _handle_inventory_transfer(self, event_data: Dict[str, Any]):
        """Handle inventory transfer event."""
        logger.info(f"Inventory transfer: {event_data.get('product_id')} from {event_data.get('source_warehouse_id')} to {event_data.get('destination_warehouse_id')}")
        # Implementation would update inventory in both warehouses
    
    def _handle_delivery_dispatched(self, event_data: Dict[str, Any]):
        """Handle delivery dispatched event."""
        logger.info(f"Delivery dispatched: {event_data.get('delivery_id')} for order {event_data.get('order_id')}")
        # Implementation would update delivery status in database
    
    def _handle_delivery_completed(self, event_data: Dict[str, Any]):
        """Handle delivery completed event."""
        logger.info(f"Delivery completed: {event_data.get('delivery_id')} for order {event_data.get('order_id')}")
        # Implementation would update delivery status in database
        # and trigger order completion
    
    def _handle_delivery_failed(self, event_data: Dict[str, Any]):
        """Handle delivery failed event."""
        logger.info(f"Delivery failed: {event_data.get('delivery_id')} for order {event_data.get('order_id')}")
        # Implementation would update delivery status in database
        # and trigger rescheduling or return to warehouse
    
    def _handle_system_alert(self, event_data: Dict[str, Any]):
        """Handle system alert event."""
        logger.info(f"System alert: {event_data.get('message')} ({event_data.get('alert_level')})")
        # Implementation would store alert in database
        # and notify relevant personnel if high priority
    
    def _handle_system_notification(self, event_data: Dict[str, Any]):
        """Handle system notification event."""
        logger.info(f"System notification: {event_data.get('message')}")
        # Implementation would store notification in database
