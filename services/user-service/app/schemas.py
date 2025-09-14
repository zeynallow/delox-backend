"""
User Service Schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from shared.models.base import BaseSchema, UUIDSchema, TimestampSchema
from shared.models.enums import UserRole, UserStatus, WorkspaceStatus


# Workspace schemas
class WorkspaceBase(BaseModel):
    """Base workspace schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    primary_color: str = Field("#007bff", regex=r"^#[0-9A-Fa-f]{6}$")


class WorkspaceCreate(WorkspaceBase):
    """Workspace creation schema"""
    slug: Optional[str] = Field(None, min_length=3, max_length=100, regex=r"^[a-z0-9-]+$")


class WorkspaceUpdate(BaseModel):
    """Workspace update schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    primary_color: Optional[str] = Field(None, regex=r"^#[0-9A-Fa-f]{6}$")
    logo_url: Optional[str] = None
    webhook_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class WorkspaceResponse(UUIDSchema, TimestampSchema):
    """Workspace response schema"""
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str
    status: WorkspaceStatus
    is_active: bool
    plan: str
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    max_users: int
    max_orders_per_month: int
    max_couriers: int
    settings: Dict[str, Any]


class WorkspaceStats(BaseModel):
    """Workspace statistics"""
    total_users: int
    active_users: int
    total_couriers: int
    active_couriers: int
    orders_this_month: int
    orders_limit: int


# User schemas
class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    role: UserRole = UserRole.EMPLOYEE
    timezone: str = "UTC"
    language: str = "en"


class UserCreate(UserBase):
    """User creation schema"""
    permissions: Optional[List[str]] = []
    courier_license: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    max_delivery_distance: Optional[int] = None


class UserUpdate(BaseModel):
    """User update schema"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: Optional[List[str]] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    courier_license: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    max_delivery_distance: Optional[int] = None


class UserResponse(UUIDSchema, TimestampSchema):
    """User response schema"""
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    workspace_id: UUID
    role: UserRole
    permissions: List[str]
    status: UserStatus
    is_active: bool
    timezone: str
    language: str
    notification_preferences: Dict[str, Any]
    courier_license: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_plate: Optional[str] = None
    max_delivery_distance: Optional[int] = None


class UserWithWorkspace(UserResponse):
    """User response with workspace info"""
    workspace: WorkspaceResponse


# Invitation schemas
class InvitationCreate(BaseModel):
    """Invitation creation schema"""
    email: EmailStr
    role: UserRole = UserRole.EMPLOYEE


class InvitationResponse(UUIDSchema, TimestampSchema):
    """Invitation response schema"""
    workspace_id: UUID
    email: str
    role: UserRole
    invited_by: UUID
    invitation_token: str
    expires_at: datetime
    is_accepted: bool
    accepted_at: Optional[datetime] = None
    is_revoked: bool
    revoked_at: Optional[datetime] = None


class InvitationAccept(BaseModel):
    """Invitation acceptance schema"""
    invitation_token: str
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


# Session schemas
class SessionResponse(UUIDSchema, TimestampSchema):
    """Session response schema"""
    user_id: UUID
    workspace_id: UUID
    session_token: str
    ip_address: str
    user_agent: Optional[str] = None
    is_active: bool
    last_activity: datetime
    expires_at: datetime


# Activity schemas
class ActivityResponse(UUIDSchema, TimestampSchema):
    """Activity response schema"""
    user_id: UUID
    workspace_id: UUID
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None
    details: Dict[str, Any]
    ip_address: str
    user_agent: Optional[str] = None


# Request/Response wrappers
class WorkspaceListResponse(BaseModel):
    """Workspace list response"""
    workspaces: List[WorkspaceResponse]
    total: int


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int


class InvitationListResponse(BaseModel):
    """Invitation list response"""
    invitations: List[InvitationResponse]
    total: int


class ActivityListResponse(BaseModel):
    """Activity list response"""
    activities: List[ActivityResponse]
    total: int


# Health check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    service: str = "user-service"
    version: str = "1.0.0"
