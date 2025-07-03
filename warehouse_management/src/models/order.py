"""
Order model for the warehouse management system.
Defines SQLAlchemy ORM model and Pydantic validation models.
"""
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from src.models.database import Base

class Order(Base):
    """
    SQLAlchemy ORM model for orders table.
    """
    __tablename__ = "orders"
    
    order_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False, default="pending")  # pending, processing, shipped, delivered, cancelled
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(String, nullable=True)
    shipping_pincode = Column(String, nullable=False)
    delivery_address = Column(String, nullable=True)
    delivery_latitude = Column(Float, nullable=True)
    delivery_longitude = Column(Float, nullable=True)
    payment_method = Column(String, nullable=False, default="credit_card")
    warehouse_id = Column(String(36), ForeignKey("warehouses.warehouse_id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    # items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    # customer = relationship("Customer", back_populates="orders")
    # warehouse = relationship("Warehouse", back_populates="orders")
    
    def __repr__(self) -> str:
        return f"<Order(order_id={self.order_id}, customer_id={self.customer_id}, status={self.status})>"


class OrderItem(Base):
    """
    SQLAlchemy ORM model for order_items table.
    """
    __tablename__ = "order_items"
    
    item_id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String(36), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    # order = relationship("Order", back_populates="items")
    # product = relationship("Product", back_populates="order_items")
    
    def __repr__(self) -> str:
        return f"<OrderItem(item_id={self.item_id}, order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"


class OrderItemBase(BaseModel):
    """
    Base Pydantic model for order item data validation.
    """
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    total_price: float = Field(gt=0)
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v: int) -> int:
        """Validate that quantity is positive."""
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v
    
    @validator('unit_price')
    def price_must_be_positive(cls, v: float) -> float:
        """Validate that price is positive."""
        if v <= 0:
            raise ValueError('Price must be positive')
        return v


class OrderItemCreate(OrderItemBase):
    """
    Pydantic model for creating a new order item.
    """
    pass


class OrderItemResponse(OrderItemBase):
    """
    Pydantic model for order item response.
    """
    item_id: str
    order_id: str
    created_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class OrderBase(BaseModel):
    """
    Base Pydantic model for order data validation.
    """
    customer_id: str
    status: str = "pending"
    total_amount: float = Field(ge=0)
    shipping_address: Optional[str] = None
    shipping_pincode: str
    delivery_address: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    payment_method: str = "credit_card"
    warehouse_id: Optional[str] = None
    items: List[OrderItemCreate]
    
    @validator('status')
    def status_must_be_valid(cls, v: str) -> str:
        """Validate order status."""
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of {valid_statuses}')
        return v
    
    @validator('total_amount')
    def amount_must_be_non_negative(cls, v: float) -> float:
        """Validate that amount is non-negative."""
        if v < 0:
            raise ValueError('Total amount must be non-negative')
        return v


class OrderCreate(OrderBase):
    """
    Pydantic model for creating a new order.
    """
    pass


class OrderUpdate(BaseModel):
    """
    Pydantic model for updating an existing order.
    """
    status: Optional[str] = None
    warehouse_id: Optional[str] = None
    
    @validator('status')
    def status_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        """Validate order status if provided."""
        if v is not None:
            valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of {valid_statuses}')
        return v


class OrderResponse(BaseModel):
    """
    Pydantic model for order response.
    """
    order_id: str
    customer_id: str
    order_date: datetime
    status: str
    total_amount: float
    shipping_address: Optional[str]
    shipping_pincode: str
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    payment_method: str
    warehouse_id: Optional[str]
    items: List[OrderItemResponse]
    
    class Config:
        orm_mode = True


class OrderSummary(BaseModel):
    """
    Pydantic model for order summary.
    """
    order_id: str
    order_date: datetime
    status: str
    total_amount: float
    customer_name: str
    warehouse_name: Optional[str] = None
    item_count: int
    
    class Config:
        orm_mode = True
