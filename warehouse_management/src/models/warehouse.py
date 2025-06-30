"""
Warehouse model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from typing import Optional, List
from datetime import time

from sqlalchemy import Column, String, Float, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from pydantic import BaseModel, Field, validator, confloat

from src.models.database import Base

class Warehouse(Base):
    """
    SQLAlchemy ORM model for warehouses table.
    """
    __tablename__ = "warehouses"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    area = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)  # in cubic meters
    current_staff = Column(Integer, nullable=False)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    
    # Add spatial column for location
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    
    def __repr__(self) -> str:
        return f"<Warehouse(id={self.id}, name={self.name}, area={self.area})>"


class WarehouseBase(BaseModel):
    """
    Base Pydantic model for warehouse data validation.
    """
    name: str
    area: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    capacity: int = Field(gt=0)
    current_staff: int = Field(ge=0)
    opening_time: time
    closing_time: time
    
    @validator('capacity')
    def capacity_must_be_positive(cls, v: int) -> int:
        """Validate that capacity is positive."""
        if v <= 0:
            raise ValueError('Capacity must be positive')
        return v
    
    @validator('current_staff')
    def staff_must_be_non_negative(cls, v: int) -> int:
        """Validate that staff count is non-negative."""
        if v < 0:
            raise ValueError('Staff count must be non-negative')
        return v
    
    @validator('closing_time')
    def closing_after_opening(cls, v: time, values: dict) -> time:
        """Validate that closing time is after opening time."""
        if 'opening_time' in values and v <= values['opening_time']:
            raise ValueError('Closing time must be after opening time')
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
    area: Optional[str] = None
    latitude: Optional[confloat(ge=-90, le=90)] = None
    longitude: Optional[confloat(ge=-180, le=180)] = None
    capacity: Optional[int] = None
    current_staff: Optional[int] = None
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    
    @validator('capacity')
    def capacity_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that capacity is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Capacity must be positive')
        return v
    
    @validator('current_staff')
    def staff_must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        """Validate that staff count is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Staff count must be non-negative')
        return v


class WarehouseResponse(WarehouseBase):
    """
    Pydantic model for warehouse response.
    """
    id: str
    
    class Config:
        orm_mode = True


class WarehouseDistance(BaseModel):
    """
    Pydantic model for warehouse distance calculation.
    """
    warehouse_id: str
    warehouse_name: str
    distance_km: float
    estimated_travel_time_min: int
