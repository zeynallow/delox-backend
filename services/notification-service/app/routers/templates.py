"""
Templates router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/")
async def get_templates():
    """Get notification templates"""
    return {"message": "Templates data"}


@router.post("/")
async def create_template():
    """Create notification template"""
    return {"message": "Template created"}


@router.put("/{template_id}")
async def update_template(template_id: UUID):
    """Update notification template"""
    return {"message": f"Template {template_id} updated"}
