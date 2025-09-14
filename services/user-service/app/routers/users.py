"""
User management router
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_admin, require_manager, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import UserRole
from ..schemas import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    InvitationCreate, InvitationResponse, InvitationAccept, InvitationListResponse
)
from ..services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get current user information"""
    user_service = UserService(db)
    
    user = user_service.get_user_by_id(str(current_user.user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update current user information"""
    user_service = UserService(db)
    
    # Users can't change their own role
    if user_data.role is not None:
        user_data.role = None
    
    try:
        user = user_service.update_user(str(current_user.user_id), user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[UserRole] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List users in workspace"""
    user_service = UserService(db)
    
    users, total = user_service.list_users(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        search=search,
        role=role
    )
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total
    )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create new user in workspace (manager/admin only)"""
    user_service = UserService(db)
    
    try:
        user = user_service.create_user(
            workspace_id=str(current_user.workspace_id),
            user_data=user_data
        )
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get user by ID"""
    user_service = UserService(db)
    
    user = user_service.get_user_by_id_and_workspace(
        user_id=user_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Update user (manager/admin only)"""
    user_service = UserService(db)
    
    # Check if user exists in workspace
    user = user_service.get_user_by_id_and_workspace(
        user_id=user_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Only admin can change roles
    if user_data.role is not None and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can change user roles"
        )
    
    try:
        updated_user = user_service.update_user(user_id, user_data)
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{user_id}", response_model=SuccessResponse)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_admin()),
    db: Session = Depends(get_session)
):
    """Delete user (admin only)"""
    user_service = UserService(db)
    
    # Check if user exists in workspace
    user = user_service.get_user_by_id_and_workspace(
        user_id=user_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Can't delete yourself
    if user_id == str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    try:
        user_service.delete_user(user_id)
        return SuccessResponse(message="User deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Invitation endpoints
@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create user invitation (manager/admin only)"""
    user_service = UserService(db)
    
    try:
        invitation = user_service.create_invitation(
            workspace_id=str(current_user.workspace_id),
            invited_by=str(current_user.user_id),
            invitation_data=invitation_data
        )
        return InvitationResponse.from_orm(invitation)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """List workspace invitations (manager/admin only)"""
    user_service = UserService(db)
    
    invitations, total = user_service.list_invitations(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit
    )
    
    return InvitationListResponse(
        invitations=[InvitationResponse.from_orm(inv) for inv in invitations],
        total=total
    )


@router.post("/invitations/accept", response_model=UserResponse)
async def accept_invitation(
    acceptance_data: InvitationAccept,
    db: Session = Depends(get_session)
):
    """Accept workspace invitation (public endpoint)"""
    user_service = UserService(db)
    
    try:
        user = user_service.accept_invitation(acceptance_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/invitations/{invitation_id}", response_model=SuccessResponse)
async def revoke_invitation(
    invitation_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Revoke invitation (manager/admin only)"""
    user_service = UserService(db)
    
    try:
        user_service.revoke_invitation(
            invitation_id=invitation_id,
            workspace_id=str(current_user.workspace_id)
        )
        return SuccessResponse(message="Invitation revoked successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
