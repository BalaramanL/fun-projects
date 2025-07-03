"""
Warehouse model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from typing import Optional, List
from datetime import time, datetime

from sqlalchemy import Column, String, Float, Integer, Time, DateTime
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from pydantic import BaseModel, Field, validator, confloat

from src.models.database import Base

class Warehouse(Base):
    """
    SQLAlchemy ORM model for warehouses table.
    """
    __tablename__ = "warehouses"
    
    warehouse_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    capacity_sqm = Column(Float, nullable=False)
    refrigerated_capacity_sqm = Column(Float, nullable=True)
    operational_hours = Column(String, nullable=True)
    manager_name = Column(String, nullable=True)
    contact_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Location is represented by latitude and longitude fields
    
    def __repr__(self) -> str:
        return f"<Warehouse(warehouse_id={self.warehouse_id}, name={self.name}, address={self.address})>"


class WarehouseBase(BaseModel):
    """
    Base Pydantic model for warehouse data validation.
    """
    name: str
    address: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    capacity_sqm: float = Field(gt=0)
    refrigerated_capacity_sqm: Optional[float] = None
    operational_hours: Optional[str] = None
    manager_name: Optional[str] = None
    contact_number: Optional[str] = None
    
    @validator('capacity_sqm')
    def capacity_must_be_positive(cls, v: float) -> float:
        """Validate that capacity is positive."""
        if v <= 0:
            raise ValueError('Capacity must be positive')
        return v
    
    @validator('refrigerated_capacity_sqm')
    def refrigerated_capacity_must_be_non_negative(cls, v: Optional[float]) -> Optional[float]:
        """Validate that refrigerated capacity is non-negative."""
        if v is not None and v < 0:
            raise ValueError('Refrigerated capacity must be non-negative')
        return v


class WarehouseCreate(WarehouseBase):
    """
    Pydantic model for creating a new warehouse.
    """
    pass


class WarehouseUpdate(BaseModel):
    """
    Pydantic model for updating an existing warehouse.
    """
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[confloat(ge=-90, le=90)] = None
    longitude: Optional[confloat(ge=-180, le=180)] = None
    capacity_sqm: Optional[float] = None
    refrigerated_capacity_sqm: Optional[float] = None
    operational_hours: Optional[str] = None
    manager_name: Optional[str] = None
    contact_number: Optional[str] = None
    
    @validator('capacity_sqm')
    def capacity_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        """Validate that capacity is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Capacity must be positive')
        return v
    
    @validator('refrigerated_capacity_sqm')
    def refrigerated_capacity_must_be_non_negative(cls, v: Optional[float]) -> Optional[float]:
        """Validate that refrigerated capacity is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Refrigerated capacity must be non-negative')
        return v


class WarehouseResponse(WarehouseBase):
    """
    Pydantic model for warehouse response.
    """
    warehouse_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WarehouseDistance(BaseModel):
    """
    Pydantic model for warehouse distance calculation.
    """
    warehouse_id: str
    warehouse_name: str
    distance_km: float
    estimated_travel_time_min: int
