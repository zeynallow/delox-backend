"""
User Service Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from shared.models.base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin
from shared.models.enums import UserRole, UserStatus, WorkspaceStatus


class Workspace(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Workspace (Company) model"""
    __tablename__ = "workspaces"
    
    # Basic info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#007bff", nullable=False)  # Hex color
    
    # Status and settings
    status = Column(String(20), default=WorkspaceStatus.TRIAL, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Subscription info
    plan = Column(String(50), default="trial", nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)
    
    # Limits
    max_users = Column(Integer, default=5, nullable=False)
    max_orders_per_month = Column(Integer, default=100, nullable=False)
    max_couriers = Column(Integer, default=2, nullable=False)
    
    # Settings
    settings = Column(JSON, default=dict, nullable=False)
    
    # API credentials
    api_key = Column(String(255), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="workspace", cascade="all, delete-orphan")
    invitations = relationship("WorkspaceInvitation", back_populates="workspace", cascade="all, delete-orphan")


class User(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """User model"""
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # Workspace relationship
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Role and permissions
    role = Column(String(20), default=UserRole.EMPLOYEE, nullable=False)
    permissions = Column(JSON, default=list, nullable=False)
    
    # Status
    status = Column(String(20), default=UserStatus.ACTIVE, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Profile settings
    timezone = Column(String(50), default="UTC", nullable=False)
    language = Column(String(10), default="en", nullable=False)
    notification_preferences = Column(JSON, default=dict, nullable=False)
    
    # Courier specific fields
    courier_license = Column(String(100), nullable=True)
    vehicle_type = Column(String(50), nullable=True)
    vehicle_plate = Column(String(20), nullable=True)
    max_delivery_distance = Column(Integer, nullable=True)  # in kilometers
    
    # Relationships
    workspace = relationship("Workspace", back_populates="users")


class WorkspaceInvitation(Base, UUIDMixin, TimestampMixin):
    """Workspace invitation model"""
    __tablename__ = "workspace_invitations"
    
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), default=UserRole.EMPLOYEE, nullable=False)
    
    # Invitation details
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invitation_token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Status
    is_accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])


class UserSession(Base, UUIDMixin, TimestampMixin):
    """User session tracking"""
    __tablename__ = "user_sessions"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Session info
    session_token = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User")
    workspace = relationship("Workspace")


class UserActivity(Base, UUIDMixin, TimestampMixin):
    """User activity log"""
    __tablename__ = "user_activities"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Activity details
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    
    # Request info
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    workspace = relationship("Workspace")
