"""
Notification Service Models
"""
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid

from shared.models.base import BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity
from shared.models.enums import NotificationType, NotificationStatus, NotificationChannel


class NotificationTemplate(BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity):
    """Notification template model"""
    __tablename__ = "notification_templates"
    
    template_name = Column(String(255), nullable=False)
    template_code = Column(String(100), nullable=False)  # Unique code for template
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channels = Column(JSON, nullable=False, default=list)  # List of channels: email, sms, push
    
    # Template content
    subject_template = Column(String(500))  # For email/push
    body_template = Column(Text, nullable=False)
    html_template = Column(Text)  # For email
    
    # Template variables
    variables = Column(JSON, default=dict)  # Expected variables and their types
    
    # Settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 1=low, 2=medium, 3=high, 4=urgent
    
    # Delivery settings
    retry_count = Column(Integer, default=3)
    retry_delay_minutes = Column(Integer, default=5)
    
    # Scheduling
    send_immediately = Column(Boolean, default=True)
    delay_minutes = Column(Integer, default=0)


class Notification(BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity):
    """Notification model"""
    __tablename__ = "notifications"
    
    # Template and type
    template_id = Column(UUID(as_uuid=True))
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    
    # Recipient
    recipient_user_id = Column(UUID(as_uuid=True))
    recipient_email = Column(String(255))
    recipient_phone = Column(String(20))
    recipient_device_token = Column(String(500))
    
    # Content
    subject = Column(String(500))
    body = Column(Text, nullable=False)
    html_body = Column(Text)
    
    # Delivery
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Retry logic
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_retry_at = Column(DateTime)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    error_message = Column(Text)
    
    # External IDs
    external_id = Column(String(255))  # ID from external service (Twilio, Firebase, etc.)
    
    # Priority
    priority = Column(Integer, default=1)


class NotificationPreference(BaseEntity, WorkspaceEntity, TimestampEntity):
    """User notification preferences"""
    __tablename__ = "notification_preferences"
    
    user_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    
    # Notification type preferences
    order_notifications = Column(Boolean, default=True)
    delivery_notifications = Column(Boolean, default=True)
    system_notifications = Column(Boolean, default=True)
    marketing_notifications = Column(Boolean, default=False)
    
    # Timing preferences
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))    # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Frequency limits
    max_emails_per_day = Column(Integer, default=10)
    max_sms_per_day = Column(Integer, default=5)
    max_push_per_hour = Column(Integer, default=20)


class NotificationLog(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Notification delivery log"""
    __tablename__ = "notification_logs"
    
    notification_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # sent, delivered, failed, opened, clicked
    event_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Provider details
    provider = Column(String(50))  # twilio, firebase, sendgrid, etc.
    provider_response = Column(JSON)
    
    # Status
    success = Column(Boolean, nullable=False)
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Metadata
    metadata = Column(JSON, default=dict)


class NotificationCampaign(BaseEntity, WorkspaceEntity, TimestampEntity, SoftDeleteEntity):
    """Notification campaign for bulk notifications"""
    __tablename__ = "notification_campaigns"
    
    campaign_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Template
    template_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Targeting
    target_audience = Column(JSON, default=dict)  # Criteria for targeting users
    recipient_count = Column(Integer, default=0)
    
    # Scheduling
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Status
    status = Column(String(20), default="draft")  # draft, scheduled, running, completed, failed
    
    # Results
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    
    # Settings
    send_rate_per_minute = Column(Integer, default=100)
    
    # Metadata
    metadata = Column(JSON, default=dict)


class WebhookEvent(BaseEntity, WorkspaceEntity, TimestampEntity):
    """Webhook events from external providers"""
    __tablename__ = "webhook_events"
    
    # Provider details
    provider = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    external_id = Column(String(255))
    
    # Related notification
    notification_id = Column(UUID(as_uuid=True))
    
    # Event data
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, default=dict)
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)
    error_message = Column(Text)


# Create all tables
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Add all models to Base
for model_class in [
    NotificationTemplate,
    Notification,
    NotificationPreference,
    NotificationLog,
    NotificationCampaign,
    WebhookEvent
]:
    model_class.__table__.tometadata(Base.metadata)
