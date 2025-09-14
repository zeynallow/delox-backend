"""
Authentication Service Models
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID

from shared.models.base import Base, UUIDMixin, TimestampMixin
from shared.models.enums import UserStatus


class AuthUser(Base, UUIDMixin, TimestampMixin):
    """Authentication user model - minimal user data for auth"""
    __tablename__ = "auth_users"
    
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    status = Column(String(20), default=UserStatus.PENDING, nullable=False)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Email verification
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Login tracking
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    """Refresh token for JWT authentication"""
    __tablename__ = "refresh_tokens"
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    device_info = Column(Text, nullable=True)  # JSON string with device info


class LoginAttempt(Base, UUIDMixin, TimestampMixin):
    """Login attempt tracking for security"""
    __tablename__ = "login_attempts"
    
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100), nullable=True)


class APIKey(Base, UUIDMixin, TimestampMixin):
    """API keys for service-to-service authentication"""
    __tablename__ = "api_keys"
    
    name = Column(String(100), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    service_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON string with permissions
    last_used = Column(DateTime, nullable=True)
