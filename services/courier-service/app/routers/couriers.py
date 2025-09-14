"""
Courier management router
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_manager, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import CourierStatus, UserRole
from ..models import Courier, CourierLocationHistory
from ..schemas import (
    CourierCreate, CourierUpdate, CourierResponse, LocationUpdate, 
    LocationResponse, CourierDashboard
)
from ..services.courier_service import CourierService

router = APIRouter()


@router.get("/", response_model=List[CourierResponse])
async def list_couriers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[CourierStatus] = Query(None),
    available_only: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List couriers in workspace"""
    courier_service = CourierService(db)
    
    couriers, total = courier_service.list_couriers(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        status=status,
        available_only=available_only
    )
    
    return [CourierResponse.from_orm(courier) for courier in couriers]


@router.post("/", response_model=CourierResponse, status_code=status.HTTP_201_CREATED)
async def create_courier(
    courier_data: CourierCreate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create new courier (manager/admin only)"""
    courier_service = CourierService(db)
    
    try:
        courier = courier_service.create_courier(
            workspace_id=str(current_user.workspace_id),
            courier_data=courier_data
        )
        return CourierResponse.from_orm(courier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=CourierResponse)
async def get_current_courier(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get current courier info (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access this endpoint"
        )
    
    courier_service = CourierService(db)
    courier = courier_service.get_courier_by_user_id(str(current_user.user_id))
    
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier profile not found"
        )
    
    return CourierResponse.from_orm(courier)


@router.put("/me", response_model=CourierResponse)
async def update_current_courier(
    courier_data: CourierUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update current courier info (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access this endpoint"
        )
    
    courier_service = CourierService(db)
    
    try:
        courier = courier_service.update_courier_by_user_id(
            str(current_user.user_id), courier_data
        )
        return CourierResponse.from_orm(courier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{courier_id}", response_model=CourierResponse)
async def get_courier(
    courier_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get courier by ID"""
    courier_service = CourierService(db)
    
    courier = courier_service.get_courier_by_id_and_workspace(
        courier_id=courier_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not courier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Courier not found"
        )
    
    return CourierResponse.from_orm(courier)


@router.put("/{courier_id}", response_model=CourierResponse)
async def update_courier(
    courier_id: str,
    courier_data: CourierUpdate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Update courier (manager/admin only)"""
    courier_service = CourierService(db)
    
    try:
        courier = courier_service.update_courier(courier_id, courier_data)
        return CourierResponse.from_orm(courier)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{courier_id}", response_model=SuccessResponse)
async def delete_courier(
    courier_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Delete courier (manager/admin only)"""
    courier_service = CourierService(db)
    
    try:
        courier_service.delete_courier(courier_id, str(current_user.workspace_id))
        return SuccessResponse(message="Courier deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Location tracking endpoints
@router.post("/location", response_model=SuccessResponse)
async def update_location(
    location_data: LocationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update courier location (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can update location"
        )
    
    courier_service = CourierService(db)
    
    try:
        courier_service.update_courier_location(
            str(current_user.user_id), location_data
        )
        return SuccessResponse(message="Location updated successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{courier_id}/location-history", response_model=List[LocationResponse])
async def get_location_history(
    courier_id: str,
    hours: int = Query(24, ge=1, le=168),  # Last 24 hours by default, max 1 week
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get courier location history"""
    courier_service = CourierService(db)
    
    # Check if user can access this courier's data
    if not current_user.is_manager() and str(current_user.user_id) != courier_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        locations = courier_service.get_location_history(courier_id, hours)
        return [LocationResponse.from_orm(loc) for loc in locations]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Courier app dashboard
@router.get("/dashboard/me", response_model=CourierDashboard)
async def get_courier_dashboard(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get courier dashboard data (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access dashboard"
        )
    
    courier_service = CourierService(db)
    
    try:
        dashboard_data = courier_service.get_courier_dashboard(str(current_user.user_id))
        return dashboard_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Status management
@router.put("/status", response_model=SuccessResponse)
async def update_courier_status(
    new_status: CourierStatus,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update courier status (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can update status"
        )
    
    courier_service = CourierService(db)
    
    try:
        courier_service.update_courier_status(str(current_user.user_id), new_status)
        return SuccessResponse(message=f"Status updated to {new_status}")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
