"""
Shared enums for all microservices
"""
from enum import Enum


class UserRole(str, Enum):
    """User roles within a workspace"""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    COURIER = "courier"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class WorkspaceStatus(str, Enum):
    """Workspace status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class OrderStatus(str, Enum):
    """Order delivery status"""
    CREATED = "created"
    CONFIRMED = "confirmed"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class OrderPriority(str, Enum):
    """Order priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class PackageSize(str, Enum):
    """Package size categories"""
    SMALL = "small"      # < 1kg, fits in mailbox
    MEDIUM = "medium"    # 1-5kg, standard package
    LARGE = "large"      # 5-20kg, requires two hands
    EXTRA_LARGE = "extra_large"  # > 20kg, special handling


class TaskStatus(str, Enum):
    """Courier task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Types of courier tasks"""
    PICKUP = "pickup"
    DELIVERY = "delivery"
    RETURN = "return"


class NotificationType(str, Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    READ = "read"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class CourierStatus(str, Enum):
    """Courier availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    ON_BREAK = "on_break"


class RouteStatus(str, Enum):
    """Route optimization status"""
    PENDING = "pending"
    OPTIMIZING = "optimizing"
    OPTIMIZED = "optimized"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationType(str, Enum):
    """Third-party integration types"""
    ECOMMERCE = "ecommerce"
    ERP = "erp"
    CRM = "crm"
    WEBHOOK = "webhook"
    API = "api"


class WebhookEvent(str, Enum):
    """Webhook event types"""
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_DELIVERED = "order.delivered"
    ORDER_FAILED = "order.failed"
    COURIER_ASSIGNED = "courier.assigned"
    COURIER_LOCATION_UPDATED = "courier.location_updated"
    ROUTE_OPTIMIZED = "route.optimized"
