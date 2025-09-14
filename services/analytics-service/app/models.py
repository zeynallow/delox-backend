"""
Analytics Service Models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.models.base import BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity


class AnalyticsReport(BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity):
    """Analytics report model"""
    __tablename__ = "analytics_reports"
    
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # delivery, courier, revenue, customer
    description = Column(Text)
    
    # Report configuration
    config = Column(JSON, nullable=False, default=dict)
    
    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Report data
    data = Column(JSON, nullable=False, default=dict)
    charts = Column(JSON, default=list)  # Chart configurations
    
    # Generation info
    generated_by = Column(UUID(as_uuid=True), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String(20), default="pending")  # pending, generating, completed, failed
    error_message = Column(Text)
    
    # Sharing
    is_public = Column(Boolean, default=False)
    shared_with = Column(JSON, default=list)  # List of user IDs


class DeliveryMetrics(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Daily delivery metrics aggregation"""
    __tablename__ = "delivery_metrics"
    
    date = Column(Date, nullable=False)
    
    # Order metrics
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    
    # Delivery metrics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    on_time_deliveries = Column(Integer, default=0)
    
    # Time metrics (in minutes)
    avg_delivery_time = Column(Numeric(10, 2))
    avg_preparation_time = Column(Numeric(10, 2))
    avg_pickup_time = Column(Numeric(10, 2))
    
    # Distance metrics (in km)
    total_distance = Column(Numeric(10, 2), default=0)
    avg_distance_per_delivery = Column(Numeric(10, 2))
    
    # Revenue metrics
    total_revenue = Column(Numeric(12, 2), default=0)
    delivery_fees = Column(Numeric(12, 2), default=0)
    avg_order_value = Column(Numeric(10, 2))
    
    # Customer metrics
    unique_customers = Column(Integer, default=0)
    new_customers = Column(Integer, default=0)
    returning_customers = Column(Integer, default=0)
    
    # Courier metrics
    active_couriers = Column(Integer, default=0)
    avg_deliveries_per_courier = Column(Numeric(10, 2))


class CourierMetrics(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Daily courier performance metrics"""
    __tablename__ = "courier_metrics"
    
    date = Column(Date, nullable=False)
    courier_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Task metrics
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    
    # Time metrics (in minutes)
    total_working_time = Column(Integer, default=0)
    total_driving_time = Column(Integer, default=0)
    avg_task_completion_time = Column(Numeric(10, 2))
    
    # Distance metrics (in km)
    total_distance = Column(Numeric(10, 2), default=0)
    
    # Performance metrics
    success_rate = Column(Numeric(5, 2), default=0)  # Percentage
    on_time_rate = Column(Numeric(5, 2), default=0)  # Percentage
    customer_rating = Column(Numeric(3, 2))  # Average rating
    
    # Earnings
    total_earnings = Column(Numeric(10, 2), default=0)
    
    # Status tracking
    online_hours = Column(Numeric(5, 2), default=0)
    offline_hours = Column(Numeric(5, 2), default=0)


class CustomerMetrics(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Customer behavior and satisfaction metrics"""
    __tablename__ = "customer_metrics"
    
    date = Column(Date, nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Order metrics
    total_orders = Column(Integer, default=0)
    completed_orders = Column(Integer, default=0)
    cancelled_orders = Column(Integer, default=0)
    
    # Spending metrics
    total_spent = Column(Numeric(12, 2), default=0)
    avg_order_value = Column(Numeric(10, 2))
    
    # Satisfaction metrics
    avg_rating = Column(Numeric(3, 2))
    total_ratings = Column(Integer, default=0)
    
    # Behavior metrics
    repeat_orders = Column(Integer, default=0)
    days_since_last_order = Column(Integer)
    
    # Delivery preferences
    preferred_delivery_time = Column(String(50))
    preferred_payment_method = Column(String(50))


class RevenueMetrics(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Revenue and financial metrics"""
    __tablename__ = "revenue_metrics"
    
    date = Column(Date, nullable=False)
    
    # Revenue breakdown
    gross_revenue = Column(Numeric(12, 2), default=0)
    delivery_fees = Column(Numeric(12, 2), default=0)
    service_fees = Column(Numeric(12, 2), default=0)
    tips = Column(Numeric(12, 2), default=0)
    
    # Costs
    courier_payments = Column(Numeric(12, 2), default=0)
    fuel_costs = Column(Numeric(12, 2), default=0)
    operational_costs = Column(Numeric(12, 2), default=0)
    
    # Net metrics
    net_revenue = Column(Numeric(12, 2), default=0)
    profit_margin = Column(Numeric(5, 2), default=0)  # Percentage
    
    # Payment methods
    cash_payments = Column(Numeric(12, 2), default=0)
    card_payments = Column(Numeric(12, 2), default=0)
    digital_payments = Column(Numeric(12, 2), default=0)
    
    # Refunds and adjustments
    refunds = Column(Numeric(12, 2), default=0)
    adjustments = Column(Numeric(12, 2), default=0)


class ZoneMetrics(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Delivery zone performance metrics"""
    __tablename__ = "zone_metrics"
    
    date = Column(Date, nullable=False)
    zone_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Delivery metrics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    
    # Time metrics
    avg_delivery_time = Column(Numeric(10, 2))
    peak_hours = Column(JSON, default=list)  # List of busy hours
    
    # Demand metrics
    total_orders = Column(Integer, default=0)
    peak_demand_hour = Column(Integer)  # Hour of day (0-23)
    demand_density = Column(Numeric(10, 2))  # Orders per sq km
    
    # Coverage metrics
    coverage_percentage = Column(Numeric(5, 2), default=0)
    avg_distance_to_customer = Column(Numeric(10, 2))
    
    # Revenue metrics
    total_revenue = Column(Numeric(12, 2), default=0)
    avg_order_value = Column(Numeric(10, 2))


class PerformanceAlert(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Performance alerts and anomaly detection"""
    __tablename__ = "performance_alerts"
    
    alert_type = Column(String(50), nullable=False)  # delivery_delay, low_rating, high_cancellation
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Related entities
    entity_type = Column(String(50))  # courier, zone, customer, order
    entity_id = Column(UUID(as_uuid=True))
    
    # Metrics
    current_value = Column(Numeric(15, 2))
    threshold_value = Column(Numeric(15, 2))
    previous_value = Column(Numeric(15, 2))
    
    # Status
    status = Column(String(20), default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(UUID(as_uuid=True))
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Actions taken
    actions_taken = Column(JSON, default=list)
    
    # Metadata
    metadata = Column(JSON, default=dict)


# Create all tables
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Add all models to Base
for model_class in [
    AnalyticsReport,
    DeliveryMetrics,
    CourierMetrics,
    CustomerMetrics,
    RevenueMetrics,
    ZoneMetrics,
    PerformanceAlert
]:
    model_class.__table__.tometadata(Base.metadata)
