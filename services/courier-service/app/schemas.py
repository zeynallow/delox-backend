"""
Courier Service Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, validator

from shared.models.base import BaseSchema, UUIDSchema, TimestampSchema
from shared.models.enums import CourierStatus, TaskStatus, TaskType, RouteStatus


# Location schemas
class LocationUpdate(BaseModel):
    """Location update from courier app"""
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    altitude: Optional[float] = None
    speed: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, lt=360)
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    is_charging: Optional[bool] = None


class LocationResponse(UUIDSchema, TimestampSchema):
    """Location history response"""
    courier_id: UUID
    latitude: Decimal
    longitude: Decimal
    accuracy: Optional[float] = None
    speed: Optional[float] = None
    route_id: Optional[UUID] = None
    task_id: Optional[UUID] = None


# Courier schemas
class CourierCreate(BaseModel):
    """Courier creation schema"""
    user_id: UUID
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_capacity: Optional[int] = Field(None, ge=1)
    max_delivery_distance: Optional[int] = Field(None, ge=1)
    working_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_days: Optional[List[int]] = Field(None, min_items=1, max_items=7)


class CourierUpdate(BaseModel):
    """Courier update schema"""
    status: Optional[CourierStatus] = None
    is_available: Optional[bool] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_capacity: Optional[int] = Field(None, ge=1)
    max_delivery_distance: Optional[int] = Field(None, ge=1)
    working_hours_start: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_hours_end: Optional[str] = Field(None, regex=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    working_days: Optional[List[int]] = Field(None, min_items=1, max_items=7)
    device_token: Optional[str] = None


class CourierResponse(UUIDSchema, TimestampSchema):
    """Courier response schema"""
    user_id: UUID
    workspace_id: UUID
    status: CourierStatus
    is_available: bool
    current_latitude: Optional[Decimal] = None
    current_longitude: Optional[Decimal] = None
    location_updated_at: Optional[datetime] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    vehicle_capacity: Optional[int] = None
    max_delivery_distance: Optional[int] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    working_days: List[int]
    total_deliveries: int
    successful_deliveries: int
    average_rating: Optional[Decimal] = None
    current_route_id: Optional[UUID] = None
    active_tasks_count: int
    last_seen_at: Optional[datetime] = None


# Task schemas
class TaskCreate(BaseModel):
    """Task creation schema"""
    order_id: UUID
    task_type: TaskType
    address: str = Field(..., min_length=1)
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None


class TaskUpdate(BaseModel):
    """Task update schema"""
    status: Optional[TaskStatus] = None
    completion_notes: Optional[str] = None
    completion_photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    failure_reason: Optional[str] = None
    customer_rating: Optional[int] = Field(None, ge=1, le=5)
    customer_feedback: Optional[str] = None


class TaskResponse(UUIDSchema, TimestampSchema):
    """Task response schema"""
    order_id: UUID
    task_type: TaskType
    courier_id: UUID
    route_id: Optional[UUID] = None
    status: TaskStatus
    sequence_number: Optional[int] = None
    address: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    special_instructions: Optional[str] = None
    completion_notes: Optional[str] = None
    failure_reason: Optional[str] = None
    customer_rating: Optional[int] = None


# Route schemas
class RouteCreate(BaseModel):
    """Route creation schema"""
    route_name: str = Field(..., min_length=1, max_length=255)
    courier_id: Optional[UUID] = None
    order_ids: List[UUID] = Field(..., min_items=1)
    planned_start_time: Optional[datetime] = None


class RouteUpdate(BaseModel):
    """Route update schema"""
    route_name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[RouteStatus] = None
    courier_id: Optional[UUID] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None


class RouteResponse(UUIDSchema, TimestampSchema):
    """Route response schema"""
    route_name: str
    status: RouteStatus
    courier_id: Optional[UUID] = None
    total_distance_km: Optional[Decimal] = None
    estimated_duration_minutes: Optional[int] = None
    total_orders: int
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    completed_tasks: int
    failed_tasks: int
    waypoints: List[Dict[str, Any]]


class RouteWithTasks(RouteResponse):
    """Route response with tasks"""
    tasks: List[TaskResponse]


# Route optimization schemas
class OptimizationRequest(BaseModel):
    """Route optimization request"""
    courier_ids: List[UUID] = Field(..., min_items=1)
    order_ids: List[UUID] = Field(..., min_items=1)
    optimization_type: str = "auto"
    constraints: Optional[Dict[str, Any]] = {}


class OptimizationResponse(UUIDSchema, TimestampSchema):
    """Route optimization response"""
    optimization_type: str
    status: str
    courier_ids: List[UUID]
    order_ids: List[UUID]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[int] = None
    optimized_routes: List[Dict[str, Any]]
    total_distance_saved: Optional[Decimal] = None
    total_time_saved: Optional[int] = None
    error_message: Optional[str] = None


# Delivery zone schemas
class DeliveryZoneCreate(BaseModel):
    """Delivery zone creation schema"""
    zone_name: str = Field(..., min_length=1, max_length=255)
    zone_code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    boundary_coordinates: List[List[Decimal]] = Field(..., min_items=3)  # At least 3 points for polygon
    center_latitude: Decimal = Field(..., ge=-90, le=90)
    center_longitude: Decimal = Field(..., ge=-180, le=180)
    max_couriers: Optional[int] = Field(None, ge=1)
    standard_delivery_fee: Optional[Decimal] = Field(None, ge=0)
    express_delivery_fee: Optional[Decimal] = Field(None, ge=0)
    max_delivery_time_hours: int = Field(24, ge=1, le=168)  # Max 1 week
    operating_hours: Optional[Dict[str, Dict[str, str]]] = {}


class DeliveryZoneResponse(UUIDSchema, TimestampSchema):
    """Delivery zone response schema"""
    zone_name: str
    zone_code: str
    description: Optional[str] = None
    boundary_coordinates: List[List[Decimal]]
    center_latitude: Decimal
    center_longitude: Decimal
    is_active: bool
    priority: int
    max_couriers: Optional[int] = None
    standard_delivery_fee: Optional[Decimal] = None
    express_delivery_fee: Optional[Decimal] = None
    max_delivery_time_hours: int
    operating_hours: Dict[str, Dict[str, str]]
    total_deliveries: int
    average_delivery_time: Optional[int] = None


# Mobile app specific schemas
class CourierDashboard(BaseModel):
    """Courier dashboard data for mobile app"""
    courier: CourierResponse
    current_route: Optional[RouteResponse] = None
    pending_tasks: List[TaskResponse]
    today_stats: Dict[str, Any]
    notifications: List[Dict[str, Any]]


class TaskAction(BaseModel):
    """Task action from mobile app"""
    action: str = Field(..., regex="^(start|complete|fail|skip)$")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    notes: Optional[str] = None
    photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    failure_reason: Optional[str] = None


# Analytics schemas
class CourierPerformance(BaseModel):
    """Courier performance metrics"""
    courier_id: UUID
    period_start: datetime
    period_end: datetime
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    average_completion_time: Optional[int] = None  # in minutes
    total_distance_km: Decimal
    average_rating: Optional[Decimal] = None
    on_time_delivery_rate: float


# Health check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    service: str = "courier-service"
    version: str = "1.0.0"
