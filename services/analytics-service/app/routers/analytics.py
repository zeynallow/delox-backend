"""
Analytics router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics"""
    return {"message": "Analytics dashboard data"}


@router.get("/orders")
async def get_order_analytics():
    """Get order analytics"""
    return {"message": "Order analytics data"}


@router.get("/couriers")
async def get_courier_analytics():
    """Get courier analytics"""
    return {"message": "Courier analytics data"}
