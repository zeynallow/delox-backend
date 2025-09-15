"""
Notifications router
"""
from fastapi import APIRouter

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications():
    """List notifications in workspace"""
    return {"message": "Notifications list"}


@router.post("/")
async def create_notification():
    """Create new notification"""
    return {"message": "Notification created"}


@router.get("/{notification_id}")
async def get_notification(notification_id: str):
    """Get notification by ID"""
    return {"message": f"Notification {notification_id}"}


@router.put("/{notification_id}")
async def update_notification(notification_id: str):
    """Update notification"""
    return {"message": f"Notification {notification_id} updated"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete notification"""
    return {"message": f"Notification {notification_id} deleted"}
