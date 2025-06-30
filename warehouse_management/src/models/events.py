"""
Events model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models for purchase events.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class PurchaseEvent(Base):
    """
    SQLAlchemy ORM model for purchase_events table.
    """
    __tablename__ = "purchase_events"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    customer_pincode = Column(String, index=True, nullable=False)
    warehouse_fulfilled = Column(String(36), ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True)
    delivery_time = Column(Integer, nullable=True)  # in minutes
    
    def __repr__(self) -> str:
        return f"<PurchaseEvent(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"


class PurchaseEventBase(BaseModel):
    """
    Base Pydantic model for purchase event data validation.
    """
    timestamp: datetime
    product_id: str
    quantity: int = Field(gt=0)
    customer_pincode: str
    warehouse_fulfilled: Optional[str] = None
    delivery_time: Optional[int] = None
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v: int) -> int:
        """Validate that quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('delivery_time')
    def delivery_time_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that delivery time is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Delivery time must be positive')
        return v


class PurchaseEventCreate(PurchaseEventBase):
    """
    Pydantic model for creating a new purchase event.
    """
    pass


class PurchaseEventUpdate(BaseModel):
    """
    Pydantic model for updating an existing purchase event.
    """
    warehouse_fulfilled: Optional[str] = None
    delivery_time: Optional[int] = None
    
    @validator('delivery_time')
    def delivery_time_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that delivery time is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Delivery time must be positive')
        return v


class PurchaseEventResponse(PurchaseEventBase):
    """
    Pydantic model for purchase event response.
    """
    id: str
    
    class Config:
        orm_mode = True


class PurchaseEventWithDetails(PurchaseEventResponse):
    """
    Pydantic model for purchase event with product and warehouse details.
    """
    product_name: str
    product_category: str
    warehouse_name: Optional[str] = None
    customer_area: Optional[str] = None


class PincodeMapping(Base):
    """
    SQLAlchemy ORM model for pincode_mapping table.
    """
    __tablename__ = "pincode_mapping"
    
    pincode = Column(String, primary_key=True, index=True)
    area_name = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    serviceability = Column(String, nullable=False, default="active")  # active, limited, inactive
    
    # Add spatial column for location
    location = Column("location", String)  # This will be converted to a spatial point in SQLite
    
    def __repr__(self) -> str:
        return f"<PincodeMapping(pincode={self.pincode}, area_name={self.area_name})>"


class PincodeMappingBase(BaseModel):
    """
    Base Pydantic model for pincode mapping data validation.
    """
    pincode: str
    area_name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    serviceability: str = "active"
    
    @validator('serviceability')
    def validate_serviceability(cls, v: str) -> str:
        """Validate serviceability value."""
        valid_values = ["active", "limited", "inactive"]
        if v not in valid_values:
            raise ValueError(f'Serviceability must be one of {valid_values}')
        return v


class PincodeMappingCreate(PincodeMappingBase):
    """
    Pydantic model for creating a new pincode mapping.
    """
    pass


class PincodeMappingUpdate(BaseModel):
    """
    Pydantic model for updating an existing pincode mapping.
    """
    area_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    serviceability: Optional[str] = None
    
    @validator('latitude')
    def validate_latitude(cls, v: Optional[float]) -> Optional[float]:
        """Validate latitude if provided."""
        if v is not None and (v < -90 or v > 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('longitude')
    def validate_longitude(cls, v: Optional[float]) -> Optional[float]:
        """Validate longitude if provided."""
        if v is not None and (v < -180 or v > 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @validator('serviceability')
    def validate_serviceability(cls, v: Optional[str]) -> Optional[str]:
        """Validate serviceability value if provided."""
        if v is not None:
            valid_values = ["active", "limited", "inactive"]
            if v not in valid_values:
                raise ValueError(f'Serviceability must be one of {valid_values}')
        return v


class PincodeMappingResponse(PincodeMappingBase):
    """
    Pydantic model for pincode mapping response.
    """
    class Config:
        orm_mode = True
