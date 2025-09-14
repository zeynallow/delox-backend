"""
Authentication Service Business Logic
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from shared.utils.auth import AuthUtils
from shared.models.enums import UserStatus
from ..models import AuthUser, RefreshToken, LoginAttempt
from ..schemas import TokenResponse


class AuthService:
    """Authentication service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[AuthUser]:
        """Get user by email"""
        return self.db.query(AuthUser).filter(
            AuthUser.email == email,
            AuthUser.is_active == True
        ).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        return self.db.query(AuthUser).filter(
            AuthUser.id == user_id,
            AuthUser.is_active == True
        ).first()
    
    def create_user(self, email: str, password: str) -> AuthUser:
        """Create new user"""
        # Hash password
        password_hash = AuthUtils.hash_password(password)
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Create user
        user = AuthUser(
            email=email,
            password_hash=password_hash,
            status=UserStatus.PENDING,
            verification_token=verification_token,
            verification_token_expires=verification_expires
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[AuthUser]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        
        if not user:
            return None
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            return None
        
        # Verify password
        if not AuthUtils.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            self.db.commit()
            return None
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        self.db.commit()
        
        return user
    
    def create_tokens(self, user: AuthUser, device_info: str = None) -> TokenResponse:
        """Create access and refresh tokens"""
        # For now, we'll create tokens without workspace info
        # This will be enhanced when we integrate with user service
        token_data = {
            "user_id": str(user.id),
            "email": user.email,
            "sub": user.email
        }
        
        # Create access token
        access_token = AuthUtils.create_access_token(token_data)
        
        # Create refresh token
        refresh_token_value = secrets.token_urlsafe(32)
        refresh_token_hash = hashlib.sha256(refresh_token_value.encode()).hexdigest()
        
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=datetime.utcnow() + timedelta(days=30),
            device_info=device_info
        )
        
        self.db.add(refresh_token)
        self.db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_value,
            token_type="bearer",
            expires_in=30 * 60  # 30 minutes
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Hash the provided token
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # Find refresh token in database
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            raise ValueError("Invalid or expired refresh token")
        
        # Get user
        user = self.get_user_by_id(str(db_token.user_id))
        if not user:
            raise ValueError("User not found")
        
        # Create new tokens
        new_tokens = self.create_tokens(user, db_token.device_info)
        
        # Revoke old refresh token
        db_token.is_revoked = True
        self.db.commit()
        
        return new_tokens
    
    def revoke_refresh_token(self, refresh_token: str):
        """Revoke refresh token"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        db_token = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        
        if db_token:
            db_token.is_revoked = True
            self.db.commit()
    
    def update_login_info(self, user: AuthUser):
        """Update user login information"""
        user.last_login = datetime.utcnow()
        user.login_count += 1
        self.db.commit()
    
    def log_login_attempt(
        self,
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        failure_reason: str = None
    ):
        """Log login attempt"""
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        
        self.db.add(attempt)
        self.db.commit()
    
    def verify_email(self, token: str):
        """Verify user email with token"""
        user = self.db.query(AuthUser).filter(
            AuthUser.verification_token == token,
            AuthUser.verification_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise ValueError("Invalid or expired verification token")
        
        user.is_verified = True
        user.status = UserStatus.ACTIVE
        user.verification_token = None
        user.verification_token_expires = None
        
        self.db.commit()
    
    def create_password_reset_token(self, user: AuthUser) -> str:
        """Create password reset token"""
        reset_token = secrets.token_urlsafe(32)
        
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        
        self.db.commit()
        
        return reset_token
    
    def reset_password(self, token: str, new_password: str):
        """Reset password with token"""
        user = self.db.query(AuthUser).filter(
            AuthUser.reset_token == token,
            AuthUser.reset_token_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise ValueError("Invalid or expired reset token")
        
        # Update password
        user.password_hash = AuthUtils.hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Revoke all refresh tokens for security
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id
        ).update({"is_revoked": True})
        
        self.db.commit()
