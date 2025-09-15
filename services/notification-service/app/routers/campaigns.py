"""
Campaigns router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/")
async def get_campaigns():
    """Get notification campaigns"""
    return {"message": "Campaigns data"}


@router.post("/")
async def create_campaign():
    """Create notification campaign"""
    return {"message": "Campaign created"}


@router.put("/{campaign_id}")
async def update_campaign(campaign_id: UUID):
    """Update notification campaign"""
    return {"message": f"Campaign {campaign_id} updated"}
