"""
Authentication and authorization utilities
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..models.enums import UserRole


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security scheme
security = HTTPBearer()


class AuthUtils:
    """Authentication utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """Decode JWT access token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


class CurrentUser:
    """Current user context"""
    
    def __init__(
        self,
        user_id: UUID,
        email: str,
        workspace_id: UUID,
        role: UserRole,
        permissions: list = None
    ):
        self.user_id = user_id
        self.email = email
        self.workspace_id = workspace_id
        self.role = role
        self.permissions = permissions or []
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == UserRole.ADMIN
    
    def is_manager(self) -> bool:
        """Check if user is manager or admin"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def is_courier(self) -> bool:
        """Check if user is courier"""
        return self.role == UserRole.COURIER
    
    def can_access_workspace(self, workspace_id: UUID) -> bool:
        """Check if user can access specific workspace"""
        return self.workspace_id == workspace_id


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> CurrentUser:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = AuthUtils.decode_access_token(token)
    
    # Extract user information from token
    user_id = payload.get("user_id")
    email = payload.get("email")
    workspace_id = payload.get("workspace_id")
    role = payload.get("role")
    permissions = payload.get("permissions", [])
    
    if not all([user_id, email, workspace_id, role]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(
        user_id=UUID(user_id),
        email=email,
        workspace_id=UUID(workspace_id),
        role=UserRole(role),
        permissions=permissions
    )


def require_role(required_role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role != required_role and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role.value}"
            )
        return current_user
    return role_checker


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_permission(permission) and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission}"
            )
        return current_user
    return permission_checker


def require_admin():
    """Decorator to require admin role"""
    return require_role(UserRole.ADMIN)


def require_manager():
    """Decorator to require manager role or higher"""
    def manager_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.is_manager():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager role required"
            )
        return current_user
    return manager_checker


# Workspace access control
def require_workspace_access(workspace_id: UUID):
    """Decorator to require access to specific workspace"""
    def workspace_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.can_access_workspace(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to workspace"
            )
        return current_user
    return workspace_checker
