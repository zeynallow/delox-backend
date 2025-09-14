"""
Notifications router
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_manager, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import NotificationStatus, NotificationChannel, NotificationType
from ..schemas import (
    NotificationCreate, NotificationUpdate, NotificationResponse,
    BulkNotificationRequest, BulkNotificationResponse, NotificationAnalytics
)
from ..services.notification_service import NotificationService

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[NotificationStatus] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    notification_type: Optional[NotificationType] = Query(None),
    recipient_user_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List notifications in workspace"""
    notification_service = NotificationService(db)
    
    notifications, total = notification_service.list_notifications(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        status=status,
        channel=channel,
        notification_type=notification_type,
        recipient_user_id=recipient_user_id
    )
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create new notification"""
    notification_service = NotificationService(db)
    
    try:
        notification = notification_service.create_notification(
            workspace_id=str(current_user.workspace_id),
            notification_data=notification_data,
            created_by=str(current_user.user_id)
        )
        return NotificationResponse.from_orm(notification)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get notification by ID"""
    notification_service = NotificationService(db)
    
    notification = notification_service.get_notification_by_id_and_workspace(
        notification_id=notification_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return NotificationResponse.from_orm(notification)


@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    notification_data: NotificationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update notification"""
    notification_service = NotificationService(db)
    
    try:
        notification = notification_service.update_notification(
            notification_id, notification_data
        )
        return NotificationResponse.from_orm(notification)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{notification_id}", response_model=SuccessResponse)
async def delete_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Delete notification (manager/admin only)"""
    notification_service = NotificationService(db)
    
    try:
        notification_service.delete_notification(
            notification_id, str(current_user.workspace_id)
        )
        return SuccessResponse(message="Notification deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Bulk operations
@router.post("/bulk", response_model=BulkNotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_notifications(
    bulk_request: BulkNotificationRequest,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create bulk notifications (manager/admin only)"""
    notification_service = NotificationService(db)
    
    try:
        result = notification_service.create_bulk_notifications(
            workspace_id=str(current_user.workspace_id),
            bulk_request=bulk_request,
            created_by=str(current_user.user_id)
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# User-specific endpoints
@router.get("/user/me", response_model=List[NotificationResponse])
async def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get notifications for current user"""
    notification_service = NotificationService(db)
    
    notifications = notification_service.get_user_notifications(
        user_id=str(current_user.user_id),
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    return [NotificationResponse.from_orm(notification) for notification in notifications]


@router.put("/{notification_id}/read", response_model=SuccessResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Mark notification as read"""
    notification_service = NotificationService(db)
    
    try:
        notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=str(current_user.user_id)
        )
        return SuccessResponse(message="Notification marked as read")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/user/me/read-all", response_model=SuccessResponse)
async def mark_all_notifications_read(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Mark all notifications as read for current user"""
    notification_service = NotificationService(db)
    
    try:
        count = notification_service.mark_all_notifications_read(
            user_id=str(current_user.user_id),
            workspace_id=str(current_user.workspace_id)
        )
        return SuccessResponse(message=f"Marked {count} notifications as read")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Retry and resend
@router.post("/{notification_id}/retry", response_model=SuccessResponse)
async def retry_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Retry failed notification (manager/admin only)"""
    notification_service = NotificationService(db)
    
    try:
        notification_service.retry_notification(notification_id)
        return SuccessResponse(message="Notification queued for retry")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Analytics
@router.get("/analytics/summary", response_model=NotificationAnalytics)
async def get_notification_analytics(
    days: int = Query(7, ge=1, le=90),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get notification analytics for workspace"""
    notification_service = NotificationService(db)
    
    try:
        analytics = notification_service.get_notification_analytics(
            workspace_id=str(current_user.workspace_id),
            days=days
        )
        return analytics
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/user/me/unread-count")
async def get_unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get unread notification count for current user"""
    notification_service = NotificationService(db)
    
    try:
        count = notification_service.get_unread_count(
            user_id=str(current_user.user_id),
            workspace_id=str(current_user.workspace_id)
        )
        return {"unread_count": count}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
