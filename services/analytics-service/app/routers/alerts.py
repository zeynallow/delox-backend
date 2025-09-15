"""
Alerts router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/")
async def get_alerts():
    """Get alerts"""
    return {"message": "Alerts data"}


@router.post("/")
async def create_alert():
    """Create alert"""
    return {"message": "Alert created"}


@router.put("/{alert_id}")
async def update_alert(alert_id: UUID):
    """Update alert"""
    return {"message": f"Alert {alert_id} updated"}
