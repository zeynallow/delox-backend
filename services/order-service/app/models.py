"""
Order Service Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, Numeric, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.models.base import BaseEntity
from shared.models.enums import OrderStatus, OrderPriority, PackageSize


class Order(BaseEntity):
    """Order model"""
    __tablename__ = "orders"
    
    # Order identification
    order_number = Column(String(50), nullable=False, unique=True, index=True)
    external_id = Column(String(100), nullable=True, index=True)  # For API integrations
    
    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    customer_email = Column(String(255), nullable=True)
    
    # Pickup information
    pickup_address = Column(Text, nullable=False)
    pickup_latitude = Column(DECIMAL(10, 8), nullable=True)
    pickup_longitude = Column(DECIMAL(11, 8), nullable=True)
    pickup_contact_name = Column(String(255), nullable=True)
    pickup_contact_phone = Column(String(20), nullable=True)
    pickup_notes = Column(Text, nullable=True)
    
    # Delivery information
    delivery_address = Column(Text, nullable=False)
    delivery_latitude = Column(DECIMAL(10, 8), nullable=True)
    delivery_longitude = Column(DECIMAL(11, 8), nullable=True)
    delivery_contact_name = Column(String(255), nullable=True)
    delivery_contact_phone = Column(String(20), nullable=True)
    delivery_notes = Column(Text, nullable=True)
    
    # Package information
    package_description = Column(Text, nullable=True)
    package_size = Column(String(20), default=PackageSize.MEDIUM, nullable=False)
    package_weight = Column(DECIMAL(8, 2), nullable=True)  # in kg
    package_value = Column(DECIMAL(10, 2), nullable=True)  # for insurance
    package_quantity = Column(Integer, default=1, nullable=False)
    
    # Order details
    status = Column(String(30), default=OrderStatus.CREATED, nullable=False, index=True)
    priority = Column(String(20), default=OrderPriority.NORMAL, nullable=False)
    
    # Scheduling
    scheduled_pickup_time = Column(DateTime, nullable=True)
    scheduled_delivery_time = Column(DateTime, nullable=True)
    delivery_window_start = Column(DateTime, nullable=True)
    delivery_window_end = Column(DateTime, nullable=True)
    
    # Pricing
    delivery_fee = Column(DECIMAL(10, 2), nullable=True)
    cod_amount = Column(DECIMAL(10, 2), nullable=True)  # Cash on delivery
    
    # Assignment
    assigned_courier_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Tracking
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Metadata
    meta_data = Column(JSON, default=dict, nullable=False)
    tags = Column(JSON, default=list, nullable=False)
    
    # Relationships
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    tracking_events = relationship("OrderTrackingEvent", back_populates="order", cascade="all, delete-orphan")


class OrderStatusHistory(BaseEntity):
    """Order status change history"""
    __tablename__ = "order_status_history"
    
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    
    # Status change
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    changed_by = Column(UUID(as_uuid=True), nullable=True)  # User who changed status
    change_reason = Column(Text, nullable=True)
    
    # Location when status changed
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    
    # Additional data
    meta_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="status_history")


class OrderTrackingEvent(BaseEntity):
    """Order tracking events"""
    __tablename__ = "order_tracking_events"
    
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)
    event_description = Column(Text, nullable=False)
    
    # Location
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    address = Column(Text, nullable=True)
    
    # Timing
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Source
    source = Column(String(50), nullable=False)  # 'system', 'courier', 'api', etc.
    source_id = Column(UUID(as_uuid=True), nullable=True)  # ID of the source (user, courier, etc.)
    
    # Additional data
    meta_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="tracking_events")


class OrderBatch(BaseEntity):
    """Order batch for bulk operations"""
    __tablename__ = "order_batches"
    
    # Batch info
    batch_name = Column(String(255), nullable=False)
    batch_type = Column(String(50), nullable=False)  # 'import', 'export', 'assignment'
    
    # Status
    status = Column(String(30), nullable=False)  # 'processing', 'completed', 'failed'
    total_orders = Column(Integer, default=0, nullable=False)
    processed_orders = Column(Integer, default=0, nullable=False)
    failed_orders = Column(Integer, default=0, nullable=False)
    
    # Processing details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # File info (for imports/exports)
    file_name = Column(String(255), nullable=True)
    file_url = Column(String(500), nullable=True)
    
    # Results
    results = Column(JSON, default=dict, nullable=False)


class APIIntegration(BaseEntity):
    """API integration configuration"""
    __tablename__ = "api_integrations"
    
    # Integration details
    name = Column(String(255), nullable=False)
    integration_type = Column(String(50), nullable=False)  # 'webhook', 'api', 'ecommerce'
    
    # Configuration
    endpoint_url = Column(String(500), nullable=True)
    api_key = Column(String(255), nullable=True)
    secret_key = Column(String(255), nullable=True)
    
    # Settings
    is_active = Column(Boolean, default=True, nullable=False)
    auto_import = Column(Boolean, default=False, nullable=False)
    auto_status_update = Column(Boolean, default=True, nullable=False)
    
    # Mapping configuration
    field_mapping = Column(JSON, default=dict, nullable=False)
    status_mapping = Column(JSON, default=dict, nullable=False)
    
    # Statistics
    last_sync_at = Column(DateTime, nullable=True)
    total_orders_imported = Column(Integer, default=0, nullable=False)
    total_orders_exported = Column(Integer, default=0, nullable=False)
    
    # Error tracking
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
