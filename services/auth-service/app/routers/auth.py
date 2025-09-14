"""
Authentication router
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import AuthUtils
from shared.models.base import SuccessResponse
from ..models import AuthUser, RefreshToken, LoginAttempt
from ..schemas import (
    LoginRequest, LoginResponse, RegisterRequest, PasswordResetRequest,
    PasswordResetConfirm, EmailVerificationRequest, RefreshTokenRequest,
    TokenResponse, UserResponse, ChangePasswordRequest, TokenValidationRequest,
    TokenValidationResponse
)
from ..services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=SuccessResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_session)
):
    """Register new user"""
    auth_service = AuthService(db)
    
    # Check if user already exists
    existing_user = auth_service.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user
    user = auth_service.create_user(request.email, request.password)
    
    # Send verification email (implement later)
    # await send_verification_email(user.email, user.verification_token)
    
    return SuccessResponse(
        message="User registered successfully. Please check your email for verification.",
        data={"user_id": str(user.id)}
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_session)
):
    """User login"""
    auth_service = AuthService(db)
    
    # Get client IP
    client_ip = http_request.client.host
    user_agent = http_request.headers.get("user-agent", "")
    
    try:
        # Authenticate user
        user = auth_service.authenticate_user(request.email, request.password)
        
        if not user:
            # Log failed attempt
            auth_service.log_login_attempt(
                request.email, client_ip, user_agent, False, "Invalid credentials"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            auth_service.log_login_attempt(
                request.email, client_ip, user_agent, False, "Account inactive"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            auth_service.log_login_attempt(
                request.email, client_ip, user_agent, False, "Account locked"
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to failed login attempts"
            )
        
        # Generate tokens
        tokens = auth_service.create_tokens(user, request.device_info)
        
        # Update login info
        auth_service.update_login_info(user)
        
        # Log successful attempt
        auth_service.log_login_attempt(
            request.email, client_ip, user_agent, True
        )
        
        return LoginResponse(
            message="Login successful",
            tokens=tokens,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Log failed attempt
        auth_service.log_login_attempt(
            request.email, client_ip, user_agent, False, "System error"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_session)
):
    """Refresh access token"""
    auth_service = AuthService(db)
    
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_session)
):
    """User logout"""
    auth_service = AuthService(db)
    
    try:
        auth_service.revoke_refresh_token(request.refresh_token)
        return SuccessResponse(message="Logged out successfully")
    except ValueError:
        # Token already invalid, but logout is successful
        return SuccessResponse(message="Logged out successfully")


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    request: TokenValidationRequest,
    db: Session = Depends(get_session)
):
    """Validate access token (for other services)"""
    auth_service = AuthService(db)
    
    try:
        payload = AuthUtils.decode_access_token(request.token)
        user = auth_service.get_user_by_id(payload.get("user_id"))
        
        if not user or not user.is_active:
            return TokenValidationResponse(valid=False)
        
        return TokenValidationResponse(
            valid=True,
            user_id=user.id,
            email=user.email,
            workspace_id=payload.get("workspace_id"),
            role=payload.get("role"),
            permissions=payload.get("permissions", []),
            expires_at=datetime.fromtimestamp(payload.get("exp"))
        )
        
    except Exception:
        return TokenValidationResponse(valid=False)


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    request: EmailVerificationRequest,
    db: Session = Depends(get_session)
):
    """Verify user email"""
    auth_service = AuthService(db)
    
    try:
        auth_service.verify_email(request.token)
        return SuccessResponse(message="Email verified successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_session)
):
    """Request password reset"""
    auth_service = AuthService(db)
    
    user = auth_service.get_user_by_email(request.email)
    if user:
        reset_token = auth_service.create_password_reset_token(user)
        # Send reset email (implement later)
        # await send_password_reset_email(user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return SuccessResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_session)
):
    """Reset password with token"""
    auth_service = AuthService(db)
    
    try:
        auth_service.reset_password(request.token, request.new_password)
        return SuccessResponse(message="Password reset successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
