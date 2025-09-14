"""
Health check router
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.utils.database import get_session

router = APIRouter()


@router.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "service": "order-service",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_session)):
    """Readiness check with database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "service": "order-service",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "timestamp": datetime.utcnow(),
            "service": "order-service",
            "version": "1.0.0",
            "error": str(e)
        }
