"""
Notification Service Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator, EmailStr

from shared.models.base import BaseSchema, UUIDSchema, TimestampSchema
from shared.models.enums import NotificationType, NotificationStatus, NotificationChannel


# Template schemas
class NotificationTemplateCreate(BaseModel):
    """Notification template creation schema"""
    template_name: str = Field(..., min_length=1, max_length=255)
    template_code: str = Field(..., min_length=1, max_length=100)
    notification_type: NotificationType
    channels: List[NotificationChannel] = Field(..., min_items=1)
    subject_template: Optional[str] = Field(None, max_length=500)
    body_template: str = Field(..., min_length=1)
    html_template: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(1, ge=1, le=4)
    retry_count: int = Field(3, ge=0, le=10)
    retry_delay_minutes: int = Field(5, ge=1, le=60)
    send_immediately: bool = True
    delay_minutes: int = Field(0, ge=0)


class NotificationTemplateUpdate(BaseModel):
    """Notification template update schema"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=255)
    channels: Optional[List[NotificationChannel]] = Field(None, min_items=1)
    subject_template: Optional[str] = Field(None, max_length=500)
    body_template: Optional[str] = Field(None, min_length=1)
    html_template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_minutes: Optional[int] = Field(None, ge=1, le=60)
    send_immediately: Optional[bool] = None
    delay_minutes: Optional[int] = Field(None, ge=0)


class NotificationTemplateResponse(UUIDSchema, TimestampSchema):
    """Notification template response schema"""
    template_name: str
    template_code: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    subject_template: Optional[str] = None
    body_template: str
    html_template: Optional[str] = None
    variables: Dict[str, Any]
    is_active: bool
    priority: int
    retry_count: int
    retry_delay_minutes: int
    send_immediately: bool
    delay_minutes: int


# Notification schemas
class NotificationCreate(BaseModel):
    """Notification creation schema"""
    template_id: Optional[UUID] = None
    notification_type: NotificationType
    recipient_user_id: Optional[UUID] = None
    recipient_email: Optional[EmailStr] = None
    recipient_phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")
    recipient_device_token: Optional[str] = None
    subject: Optional[str] = Field(None, max_length=500)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = None
    channel: NotificationChannel
    scheduled_at: Optional[datetime] = None
    priority: int = Field(1, ge=1, le=4)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationUpdate(BaseModel):
    """Notification update schema"""
    status: Optional[NotificationStatus] = None
    read_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(UUIDSchema, TimestampSchema):
    """Notification response schema"""
    template_id: Optional[UUID] = None
    notification_type: NotificationType
    recipient_user_id: Optional[UUID] = None
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    subject: Optional[str] = None
    body: str
    channel: NotificationChannel
    status: NotificationStatus
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    priority: int
    metadata: Dict[str, Any]
    error_message: Optional[str] = None


# Preference schemas
class NotificationPreferenceUpdate(BaseModel):
    """Notification preference update schema"""
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    order_notifications: Optional[bool] = None
    delivery_notifications: Optional[bool] = None
    system_notifications: Optional[bool] = None
    marketing_notifications: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    quiet_hours_end: Optional[str] = Field(None, pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    timezone: Optional[str] = None
    max_emails_per_day: Optional[int] = Field(None, ge=1, le=50)
    max_sms_per_day: Optional[int] = Field(None, ge=1, le=20)
    max_push_per_hour: Optional[int] = Field(None, ge=1, le=100)


class NotificationPreferenceResponse(UUIDSchema, TimestampSchema):
    """Notification preference response schema"""
    user_id: UUID
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    order_notifications: bool
    delivery_notifications: bool
    system_notifications: bool
    marketing_notifications: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    timezone: str
    max_emails_per_day: int
    max_sms_per_day: int
    max_push_per_hour: int


# Campaign schemas
class NotificationCampaignCreate(BaseModel):
    """Notification campaign creation schema"""
    campaign_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    template_id: UUID
    target_audience: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    send_rate_per_minute: int = Field(100, ge=1, le=1000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationCampaignUpdate(BaseModel):
    """Notification campaign update schema"""
    campaign_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = Field(None, pattern="^(draft|scheduled|running|completed|failed|cancelled)$")
    send_rate_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    metadata: Optional[Dict[str, Any]] = None


class NotificationCampaignResponse(UUIDSchema, TimestampSchema):
    """Notification campaign response schema"""
    campaign_name: str
    description: Optional[str] = None
    template_id: UUID
    target_audience: Dict[str, Any]
    recipient_count: int
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    sent_count: int
    delivered_count: int
    failed_count: int
    opened_count: int
    clicked_count: int
    send_rate_per_minute: int
    metadata: Dict[str, Any]


# Bulk notification schemas
class BulkNotificationRequest(BaseModel):
    """Bulk notification request schema"""
    template_id: UUID
    recipients: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    variables: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    priority: int = Field(1, ge=1, le=4)


class BulkNotificationResponse(BaseModel):
    """Bulk notification response schema"""
    total_recipients: int
    notifications_created: int
    failed_recipients: List[Dict[str, Any]]
    batch_id: UUID


# Analytics schemas
class NotificationAnalytics(BaseModel):
    """Notification analytics schema"""
    period_start: datetime
    period_end: datetime
    total_sent: int
    total_delivered: int
    total_failed: int
    total_opened: int
    total_clicked: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    channel_breakdown: Dict[str, Dict[str, int]]
    type_breakdown: Dict[str, Dict[str, int]]


# Webhook schemas
class WebhookEventCreate(BaseModel):
    """Webhook event creation schema"""
    provider: str
    event_type: str
    external_id: Optional[str] = None
    notification_id: Optional[UUID] = None
    payload: Dict[str, Any]
    headers: Dict[str, str] = Field(default_factory=dict)


class WebhookEventResponse(UUIDSchema, TimestampSchema):
    """Webhook event response schema"""
    provider: str
    event_type: str
    external_id: Optional[str] = None
    notification_id: Optional[UUID] = None
    payload: Dict[str, Any]
    processed: bool
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# Health check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    service: str = "notification-service"
    version: str = "1.0.0"
    providers: Dict[str, str] = Field(default_factory=dict)  # Status of external providers
