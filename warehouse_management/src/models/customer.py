"""
Customer model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class Customer(Base):
    """
    SQLAlchemy ORM model for customers table.
    """
    __tablename__ = "customers"
    
    customer_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Customer(customer_id={self.customer_id}, name={self.name}, phone={self.phone})>"


class CustomerBase(BaseModel):
    """
    Base Pydantic model for customer data validation.
    """
    name: str
    email: str
    phone: Optional[str] = None
    pincode: str
    address: Optional[str] = None
    
    @validator('email')
    def email_must_be_valid(cls, v: str) -> str:
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v


class CustomerCreate(CustomerBase):
    """
    Pydantic model for creating a new customer.
    """
    pass


class CustomerUpdate(BaseModel):
    """
    Pydantic model for updating an existing customer.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    pincode: Optional[str] = None
    address: Optional[str] = None
    
    @validator('email')
    def email_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format if provided."""
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class CustomerResponse(CustomerBase):
    """
    Pydantic model for customer response.
    """
    customer_id: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True
