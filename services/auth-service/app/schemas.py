"""
Authentication Service Schemas
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from shared.models.base import BaseSchema, UUIDSchema, TimestampSchema
from shared.models.enums import UserStatus


# Request schemas
class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    remember_me: bool = False
    device_info: Optional[str] = None


class RegisterRequest(BaseModel):
    """Registration request schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# Response schemas
class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(UUIDSchema, TimestampSchema):
    """User response schema"""
    email: str
    is_active: bool
    is_verified: bool
    status: UserStatus
    last_login: Optional[datetime] = None
    login_count: int


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool = True
    message: str
    tokens: TokenResponse
    user: UserResponse


class RefreshTokenResponse(UUIDSchema, TimestampSchema):
    """Refresh token response schema"""
    user_id: UUID
    expires_at: datetime
    is_revoked: bool
    device_info: Optional[str] = None


class LoginAttemptResponse(UUIDSchema, TimestampSchema):
    """Login attempt response schema"""
    email: str
    ip_address: str
    user_agent: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None


class APIKeyResponse(UUIDSchema, TimestampSchema):
    """API key response schema"""
    name: str
    service_name: str
    is_active: bool
    expires_at: Optional[datetime] = None
    permissions: Optional[list] = None
    last_used: Optional[datetime] = None


class APIKeyCreateRequest(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    service_name: str = Field(..., min_length=1, max_length=50)
    expires_in_days: Optional[int] = Field(None, gt=0, le=365)
    permissions: Optional[list] = None


class APIKeyCreateResponse(BaseModel):
    """API key creation response"""
    api_key: str
    key_info: APIKeyResponse


# Validation schemas
class TokenValidationRequest(BaseModel):
    """Token validation request"""
    token: str


class TokenValidationResponse(BaseModel):
    """Token validation response"""
    valid: bool
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    workspace_id: Optional[UUID] = None
    role: Optional[str] = None
    permissions: Optional[list] = None
    expires_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime
    service: str = "auth-service"
    version: str = "1.0.0"
