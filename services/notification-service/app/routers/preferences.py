"""
Preferences router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("/")
async def get_preferences():
    """Get notification preferences"""
    return {"message": "Preferences data"}


@router.post("/")
async def create_preferences():
    """Create notification preferences"""
    return {"message": "Preferences created"}


@router.put("/{user_id}")
async def update_preferences(user_id: UUID):
    """Update notification preferences"""
    return {"message": f"Preferences for user {user_id} updated"}
