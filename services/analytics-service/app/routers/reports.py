"""
Reports router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily")
async def get_daily_report():
    """Get daily report"""
    return {"message": "Daily report data"}


@router.get("/weekly")
async def get_weekly_report():
    """Get weekly report"""
    return {"message": "Weekly report data"}


@router.get("/monthly")
async def get_monthly_report():
    """Get monthly report"""
    return {"message": "Monthly report data"}
