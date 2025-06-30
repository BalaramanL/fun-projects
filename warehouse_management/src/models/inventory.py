"""
Inventory model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class Inventory(Base):
    """
    SQLAlchemy ORM model for inventory table.
    """
    __tablename__ = "inventory"
    
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), primary_key=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    current_stock = Column(Integer, nullable=False, default=0)
    min_threshold = Column(Integer, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # product = relationship("Product", back_populates="inventory_items")
    # warehouse = relationship("Warehouse", back_populates="inventory_items")
    
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'product_id', name='uix_inventory_warehouse_product'),
    )
    
    def __repr__(self) -> str:
        return f"<Inventory(warehouse_id={self.warehouse_id}, product_id={self.product_id}, stock={self.current_stock})>"


class InventoryBase(BaseModel):
    """
    Base Pydantic model for inventory data validation.
    """
    warehouse_id: str
    product_id: str
    current_stock: int = Field(ge=0)
    min_threshold: int = Field(ge=0)
    max_capacity: int = Field(gt=0)
    
    @validator('current_stock')
    def stock_must_be_non_negative(cls, v: int) -> int:
        """Validate that stock is non-negative."""
        if v < 0:
            raise ValueError('Stock must be non-negative')
        return v
    
    @validator('min_threshold')
    def threshold_must_be_non_negative(cls, v: int) -> int:
        """Validate that threshold is non-negative."""
        if v < 0:
            raise ValueError('Threshold must be non-negative')
        return v
    
    @validator('max_capacity')
    def capacity_must_be_positive(cls, v: int) -> int:
        """Validate that capacity is positive."""
        if v <= 0:
            raise ValueError('Capacity must be positive')
        return v
    
    @validator('max_capacity')
    def capacity_must_exceed_threshold(cls, v: int, values: dict) -> int:
        """Validate that capacity exceeds threshold."""
        if 'min_threshold' in values and v <= values['min_threshold']:
            raise ValueError('Capacity must exceed threshold')
        return v


class InventoryCreate(InventoryBase):
    """
    Pydantic model for creating a new inventory record.
    """
    pass


class InventoryUpdate(BaseModel):
    """
    Pydantic model for updating an existing inventory record.
    """
    current_stock: Optional[int] = None
    min_threshold: Optional[int] = None
    max_capacity: Optional[int] = None
    
    @validator('current_stock')
    def stock_must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        """Validate that stock is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Stock must be non-negative')
        return v
    
    @validator('min_threshold')
    def threshold_must_be_non_negative(cls, v: Optional[int]) -> Optional[int]:
        """Validate that threshold is non-negative if provided."""
        if v is not None and v < 0:
            raise ValueError('Threshold must be non-negative')
        return v
    
    @validator('max_capacity')
    def capacity_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that capacity is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Capacity must be positive')
        return v


class InventoryResponse(InventoryBase):
    """
    Pydantic model for inventory response.
    """
    last_updated: datetime
    
    class Config:
        orm_mode = True


class InventoryWithDetails(InventoryResponse):
    """
    Pydantic model for inventory with product and warehouse details.
    """
    product_name: str
    product_category: str
    product_subcategory: str
    warehouse_name: str
    warehouse_area: str


class InventoryAlert(BaseModel):
    """
    Pydantic model for inventory alerts.
    """
    warehouse_id: str
    warehouse_name: str
    product_id: str
    product_name: str
    current_stock: int
    min_threshold: int
    max_capacity: int
    stock_percentage: float
    alert_level: str  # 'critical', 'low', 'normal', 'overstocked'
    recommendation: str
