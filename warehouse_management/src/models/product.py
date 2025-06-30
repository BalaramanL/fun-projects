"""
Product model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class Product(Base):
    """
    SQLAlchemy ORM model for products table.
    """
    __tablename__ = "products"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False)
    subcategory = Column(String, index=True, nullable=False)
    price = Column(Float, nullable=False)
    unit_type = Column(String, nullable=False)
    shelf_life_days = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, category={self.category})>"


class ProductBase(BaseModel):
    """
    Base Pydantic model for product data validation.
    """
    name: str
    category: str
    subcategory: str
    price: float = Field(gt=0)
    unit_type: str
    shelf_life_days: int = Field(gt=0)
    
    @validator('price')
    def price_must_be_positive(cls, v: float) -> float:
        """Validate that price is positive."""
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('shelf_life_days')
    def shelf_life_must_be_positive(cls, v: int) -> int:
        """Validate that shelf life is positive."""
        if v <= 0:
            raise ValueError('Shelf life must be positive')
        return v


class ProductCreate(ProductBase):
    """
    Pydantic model for creating a new product.
    """
    pass


class ProductUpdate(BaseModel):
    """
    Pydantic model for updating an existing product.
    """
    name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    price: Optional[float] = None
    unit_type: Optional[str] = None
    shelf_life_days: Optional[int] = None
    
    @validator('price')
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        """Validate that price is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('shelf_life_days')
    def shelf_life_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        """Validate that shelf life is positive if provided."""
        if v is not None and v <= 0:
            raise ValueError('Shelf life must be positive')
        return v


class ProductResponse(ProductBase):
    """
    Pydantic model for product response.
    """
    id: str
    created_at: datetime
    
    class Config:
        orm_mode = True
