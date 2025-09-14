"""
Workspace management router
"""
import secrets
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_admin, CurrentUser
from shared.models.base import SuccessResponse
from ..models import Workspace
from ..schemas import (
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceStats,
    WorkspaceListResponse
)
from ..services.workspace_service import WorkspaceService

router = APIRouter()


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    db: Session = Depends(get_session)
):
    """Create new workspace (public endpoint for registration)"""
    workspace_service = WorkspaceService(db)
    
    try:
        workspace = workspace_service.create_workspace(workspace_data)
        return WorkspaceResponse.from_orm(workspace)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=WorkspaceListResponse)
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List workspaces (admin only for now)"""
    workspace_service = WorkspaceService(db)
    
    # For now, only return current user's workspace
    # In future, super admin can see all workspaces
    workspace = workspace_service.get_workspace_by_id(current_user.workspace_id)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return WorkspaceListResponse(
        workspaces=[WorkspaceResponse.from_orm(workspace)],
        total=1
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get workspace by ID"""
    workspace_service = WorkspaceService(db)
    
    # Check if user has access to this workspace
    if str(current_user.workspace_id) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace"
        )
    
    workspace = workspace_service.get_workspace_by_id(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return WorkspaceResponse.from_orm(workspace)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    workspace_data: WorkspaceUpdate,
    current_user: CurrentUser = Depends(require_admin()),
    db: Session = Depends(get_session)
):
    """Update workspace (admin only)"""
    workspace_service = WorkspaceService(db)
    
    # Check if user has access to this workspace
    if str(current_user.workspace_id) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace"
        )
    
    try:
        workspace = workspace_service.update_workspace(workspace_id, workspace_data)
        return WorkspaceResponse.from_orm(workspace)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{workspace_id}", response_model=SuccessResponse)
async def delete_workspace(
    workspace_id: str,
    current_user: CurrentUser = Depends(require_admin()),
    db: Session = Depends(get_session)
):
    """Delete workspace (admin only)"""
    workspace_service = WorkspaceService(db)
    
    # Check if user has access to this workspace
    if str(current_user.workspace_id) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace"
        )
    
    try:
        workspace_service.delete_workspace(workspace_id)
        return SuccessResponse(message="Workspace deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{workspace_id}/stats", response_model=WorkspaceStats)
async def get_workspace_stats(
    workspace_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get workspace statistics"""
    workspace_service = WorkspaceService(db)
    
    # Check if user has access to this workspace
    if str(current_user.workspace_id) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace"
        )
    
    stats = workspace_service.get_workspace_stats(workspace_id)
    return stats


@router.post("/{workspace_id}/regenerate-api-key", response_model=SuccessResponse)
async def regenerate_api_key(
    workspace_id: str,
    current_user: CurrentUser = Depends(require_admin()),
    db: Session = Depends(get_session)
):
    """Regenerate workspace API key (admin only)"""
    workspace_service = WorkspaceService(db)
    
    # Check if user has access to this workspace
    if str(current_user.workspace_id) != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to workspace"
        )
    
    try:
        new_api_key = workspace_service.regenerate_api_key(workspace_id)
        return SuccessResponse(
            message="API key regenerated successfully",
            data={"api_key": new_api_key}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
