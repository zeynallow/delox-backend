"""
Webhooks router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.get("/")
async def get_webhooks():
    """Get webhooks"""
    return {"message": "Webhooks data"}


@router.post("/")
async def create_webhook():
    """Create webhook"""
    return {"message": "Webhook created"}


@router.put("/{webhook_id}")
async def update_webhook(webhook_id: UUID):
    """Update webhook"""
    return {"message": f"Webhook {webhook_id} updated"}
