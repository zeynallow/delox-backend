"""
Courier Service Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON, DECIMAL, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.models.base import BaseEntity
from shared.models.enums import CourierStatus, TaskStatus, TaskType, RouteStatus


class Courier(BaseEntity):
    """Courier model"""
    __tablename__ = "couriers"
    
    # Basic info (linked to user service)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    # Status and availability
    status = Column(String(20), default=CourierStatus.OFFLINE, nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    
    # Current location
    current_latitude = Column(DECIMAL(10, 8), nullable=True)
    current_longitude = Column(DECIMAL(11, 8), nullable=True)
    location_updated_at = Column(DateTime, nullable=True)
    location_accuracy = Column(Float, nullable=True)  # in meters
    
    # Vehicle information
    vehicle_type = Column(String(50), nullable=True)  # motorcycle, car, bicycle, walking
    vehicle_plate = Column(String(20), nullable=True)
    vehicle_capacity = Column(Integer, nullable=True)  # max packages
    
    # Working preferences
    max_delivery_distance = Column(Integer, nullable=True)  # in kilometers
    working_hours_start = Column(String(5), nullable=True)  # HH:MM format
    working_hours_end = Column(String(5), nullable=True)    # HH:MM format
    working_days = Column(JSON, default=list, nullable=False)  # [1,2,3,4,5] for Mon-Fri
    
    # Performance metrics
    total_deliveries = Column(Integer, default=0, nullable=False)
    successful_deliveries = Column(Integer, default=0, nullable=False)
    average_rating = Column(DECIMAL(3, 2), nullable=True)
    total_distance_km = Column(DECIMAL(10, 2), default=0, nullable=False)
    
    # Current assignment
    current_route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True)
    active_tasks_count = Column(Integer, default=0, nullable=False)
    
    # Device info
    device_token = Column(String(255), nullable=True)  # for push notifications
    app_version = Column(String(20), nullable=True)
    last_seen_at = Column(DateTime, nullable=True)
    
    # Relationships
    current_route = relationship("Route", foreign_keys=[current_route_id])
    location_history = relationship("CourierLocationHistory", back_populates="courier", cascade="all, delete-orphan")
    tasks = relationship("CourierTask", back_populates="courier")


class Route(BaseEntity):
    """Delivery route model"""
    __tablename__ = "routes"
    
    # Route info
    route_name = Column(String(255), nullable=False)
    status = Column(String(20), default=RouteStatus.PENDING, nullable=False, index=True)
    
    # Assignment
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    
    # Route details
    total_distance_km = Column(DECIMAL(10, 2), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    total_orders = Column(Integer, default=0, nullable=False)
    
    # Timing
    planned_start_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    planned_end_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Optimization data
    optimization_data = Column(JSON, default=dict, nullable=False)
    waypoints = Column(JSON, default=list, nullable=False)  # Optimized order of stops
    
    # Progress tracking
    completed_tasks = Column(Integer, default=0, nullable=False)
    failed_tasks = Column(Integer, default=0, nullable=False)
    
    # Relationships
    courier = relationship("Courier", foreign_keys=[courier_id])
    tasks = relationship("CourierTask", back_populates="route", cascade="all, delete-orphan")


class CourierTask(BaseEntity):
    """Individual courier task (pickup/delivery)"""
    __tablename__ = "courier_tasks"
    
    # Task identification
    order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    task_type = Column(String(20), nullable=False)  # pickup, delivery, return
    
    # Assignment
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id"), nullable=False, index=True)
    route_id = Column(UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True, index=True)
    
    # Status and timing
    status = Column(String(20), default=TaskStatus.PENDING, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=True)  # Order in route
    
    # Location
    address = Column(Text, nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    
    # Contact info
    contact_name = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Timing
    scheduled_time = Column(DateTime, nullable=True)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Task details
    notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Completion data
    completion_notes = Column(Text, nullable=True)
    completion_photo_url = Column(String(500), nullable=True)
    signature_url = Column(String(500), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Customer feedback
    customer_rating = Column(Integer, nullable=True)  # 1-5 stars
    customer_feedback = Column(Text, nullable=True)
    
    # Relationships
    courier = relationship("Courier", back_populates="tasks")
    route = relationship("Route", back_populates="tasks")


class CourierLocationHistory(BaseEntity):
    """Courier location tracking history"""
    __tablename__ = "courier_location_history"
    
    courier_id = Column(UUID(as_uuid=True), ForeignKey("couriers.id"), nullable=False, index=True)
    
    # Location data
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    accuracy = Column(Float, nullable=True)  # in meters
    altitude = Column(Float, nullable=True)  # in meters
    speed = Column(Float, nullable=True)     # in km/h
    heading = Column(Float, nullable=True)   # in degrees
    
    # Context
    route_id = Column(UUID(as_uuid=True), nullable=True)
    task_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Device info
    battery_level = Column(Integer, nullable=True)  # percentage
    is_charging = Column(Boolean, nullable=True)
    
    # Relationships
    courier = relationship("Courier", back_populates="location_history")


class RouteOptimization(BaseEntity):
    """Route optimization requests and results"""
    __tablename__ = "route_optimizations"
    
    # Request info
    optimization_type = Column(String(50), nullable=False)  # manual, auto, scheduled
    requested_by = Column(UUID(as_uuid=True), nullable=True)  # user who requested
    
    # Input data
    courier_ids = Column(JSON, default=list, nullable=False)
    order_ids = Column(JSON, default=list, nullable=False)
    constraints = Column(JSON, default=dict, nullable=False)
    
    # Processing
    status = Column(String(20), default="pending", nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Results
    optimized_routes = Column(JSON, default=list, nullable=False)
    total_distance_saved = Column(DECIMAL(10, 2), nullable=True)
    total_time_saved = Column(Integer, nullable=True)  # in minutes
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)


class DeliveryZone(BaseEntity):
    """Delivery zones for courier assignment"""
    __tablename__ = "delivery_zones"
    
    # Zone info
    zone_name = Column(String(255), nullable=False)
    zone_code = Column(String(20), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Geographic boundaries (polygon)
    boundary_coordinates = Column(JSON, nullable=False)  # Array of [lat, lng] points
    center_latitude = Column(DECIMAL(10, 8), nullable=False)
    center_longitude = Column(DECIMAL(11, 8), nullable=False)
    
    # Zone settings
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    max_couriers = Column(Integer, nullable=True)
    
    # Delivery settings
    standard_delivery_fee = Column(DECIMAL(10, 2), nullable=True)
    express_delivery_fee = Column(DECIMAL(10, 2), nullable=True)
    max_delivery_time_hours = Column(Integer, default=24, nullable=False)
    
    # Operating hours
    operating_hours = Column(JSON, default=dict, nullable=False)  # {day: {start, end}}
    
    # Statistics
    total_deliveries = Column(Integer, default=0, nullable=False)
    average_delivery_time = Column(Integer, nullable=True)  # in minutes
