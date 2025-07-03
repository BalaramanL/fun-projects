"""
Delivery model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class DeliveryAgent(Base):
    """
    SQLAlchemy ORM model for delivery_agents table.
    """
    __tablename__ = "delivery_agents"
    
    agent_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    vehicle_type = Column(String, nullable=False)  # bike, car, van, truck
    status = Column(String, nullable=False, default="available")
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.warehouse_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # deliveries = relationship("Delivery", back_populates="agent")
    
    def __repr__(self) -> str:
        return f"<DeliveryAgent(agent_id={self.agent_id}, name={self.name}, vehicle={self.vehicle_type})>"


class Delivery(Base):
    """
    SQLAlchemy ORM model for deliveries table.
    """
    __tablename__ = "deliveries"
    
    delivery_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, unique=True)
    agent_id = Column(String(36), ForeignKey("delivery_agents.agent_id", ondelete="SET NULL"), nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, in_transit, delivered, failed
    assigned_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    delivery_time_minutes = Column(Integer, nullable=True)
    distance_km = Column(Float, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_comments = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # order = relationship("Order", back_populates="delivery")
    # agent = relationship("DeliveryAgent", back_populates="deliveries")
    
    def __repr__(self) -> str:
        return f"<Delivery(delivery_id={self.delivery_id}, order_id={self.order_id}, status={self.status})>"


class DeliveryAgentBase(BaseModel):
    """
    Base Pydantic model for delivery agent data validation.
    """
    name: str
    contact_number: str
    vehicle_type: str
    status: str = "available"
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    warehouse_id: Optional[str] = None
    
    @validator('vehicle_type')
    def vehicle_type_must_be_valid(cls, v: str) -> str:
        """Validate vehicle type."""
        valid_types = ["bike", "car", "van", "truck"]
        if v not in valid_types:
            raise ValueError(f'Vehicle type must be one of {valid_types}')
        return v


class DeliveryAgentCreate(DeliveryAgentBase):
    """
    Pydantic model for creating a new delivery agent.
    """
    pass


class DeliveryAgentUpdate(BaseModel):
    """
    Pydantic model for updating an existing delivery agent.
    """
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    is_active: Optional[bool] = None
    current_pincode: Optional[str] = None
    
    @validator('vehicle_type')
    def vehicle_type_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate vehicle type if provided."""
        if v is not None:
            valid_types = ["bike", "car", "van", "truck"]
            if v not in valid_types:
                raise ValueError(f'Vehicle type must be one of {valid_types}')
        return v


class DeliveryAgentResponse(DeliveryAgentBase):
    """
    Pydantic model for delivery agent response.
    """
    agent_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class DeliveryBase(BaseModel):
    """
    Base Pydantic model for delivery data validation.
    """
    order_id: str
    agent_id: str
    status: str = "pending"
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    delivery_time_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    feedback_rating: Optional[int] = None
    feedback_comments: Optional[str] = None
    
    @validator('status')
    def status_must_be_valid(cls, v: str) -> str:
        """Validate delivery status."""
        valid_statuses = ["pending", "in_transit", "delivered", "failed"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class DeliveryCreate(DeliveryBase):
    """
    Pydantic model for creating a new delivery.
    """
    pass


class DeliveryUpdate(BaseModel):
    """
    Pydantic model for updating an existing delivery.
    """
    agent_id: Optional[str] = None
    status: Optional[str] = None
    pickup_time: Optional[datetime] = None
    delivery_time: Optional[datetime] = None
    estimated_delivery_time: Optional[datetime] = None
    actual_delivery_time: Optional[datetime] = None
    delivery_notes: Optional[str] = None
    
    @validator('status')
    def status_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate delivery status if provided."""
        if v is not None:
            valid_statuses = ["pending", "in_transit", "delivered", "failed"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class DeliveryResponse(DeliveryBase):
    """
    Pydantic model for delivery response.
    """
    delivery_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class DeliveryWithDetails(DeliveryResponse):
    """
    Pydantic model for delivery with order and agent details.
    """
    order_total: float
    customer_name: str
    customer_pincode: str
    agent_name: Optional[str] = None
    agent_vehicle: Optional[str] = None
    warehouse_name: Optional[str] = None
    
    class Config:
        orm_mode = True
