"""
Real-time tracking router
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, CurrentUser
from ..schemas import LocationResponse, CourierResponse
from ..services.tracking_service import TrackingService

router = APIRouter()


@router.get("/couriers/live", response_model=List[CourierResponse])
async def get_live_courier_locations(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get live locations of all active couriers in workspace"""
    tracking_service = TrackingService(db)
    
    try:
        couriers = tracking_service.get_live_courier_locations(
            workspace_id=str(current_user.workspace_id)
        )
        return [CourierResponse.from_orm(courier) for courier in couriers]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/couriers/{courier_id}/live", response_model=Optional[CourierResponse])
async def get_courier_live_location(
    courier_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get live location of specific courier"""
    tracking_service = TrackingService(db)
    
    try:
        courier = tracking_service.get_courier_live_location(
            courier_id=courier_id,
            workspace_id=str(current_user.workspace_id)
        )
        return CourierResponse.from_orm(courier) if courier else None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/orders/{order_id}/courier", response_model=Optional[CourierResponse])
async def get_order_courier_location(
    order_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get location of courier assigned to specific order"""
    tracking_service = TrackingService(db)
    
    try:
        courier = tracking_service.get_order_courier_location(
            order_id=order_id,
            workspace_id=str(current_user.workspace_id)
        )
        return CourierResponse.from_orm(courier) if courier else None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/routes/{route_id}/progress")
async def get_route_progress(
    route_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get real-time progress of a route"""
    tracking_service = TrackingService(db)
    
    try:
        progress = tracking_service.get_route_progress(
            route_id=route_id,
            workspace_id=str(current_user.workspace_id)
        )
        return progress
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/analytics/delivery-times")
async def get_delivery_time_analytics(
    days: int = Query(7, ge=1, le=30),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get delivery time analytics for the workspace"""
    tracking_service = TrackingService(db)
    
    try:
        analytics = tracking_service.get_delivery_time_analytics(
            workspace_id=str(current_user.workspace_id),
            days=days
        )
        return analytics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/analytics/courier-performance")
async def get_courier_performance_analytics(
    courier_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get courier performance analytics"""
    tracking_service = TrackingService(db)
    
    try:
        analytics = tracking_service.get_courier_performance_analytics(
            workspace_id=str(current_user.workspace_id),
            courier_id=courier_id,
            days=days
        )
        return analytics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Public tracking endpoints (for customers)
@router.get("/public/orders/{order_id}/track")
async def track_order_public(
    order_id: str,
    tracking_code: str = Query(...),
    db: Session = Depends(get_session)
):
    """Public order tracking endpoint for customers"""
    tracking_service = TrackingService(db)
    
    try:
        tracking_info = tracking_service.get_public_order_tracking(
            order_id=order_id,
            tracking_code=tracking_code
        )
        return tracking_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/heatmap/deliveries")
async def get_delivery_heatmap(
    days: int = Query(30, ge=1, le=90),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get delivery heatmap data for the workspace"""
    tracking_service = TrackingService(db)
    
    try:
        heatmap_data = tracking_service.get_delivery_heatmap(
            workspace_id=str(current_user.workspace_id),
            days=days
        )
        return heatmap_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/zones/coverage")
async def get_zone_coverage(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get delivery zone coverage statistics"""
    tracking_service = TrackingService(db)
    
    try:
        coverage = tracking_service.get_zone_coverage_stats(
            workspace_id=str(current_user.workspace_id)
        )
        return coverage
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
