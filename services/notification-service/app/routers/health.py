"""
Health check router
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Check external providers status
    providers = {}
    
    try:
        from ..services.provider_service import ProviderService
        provider_service = ProviderService()
        providers = provider_service.get_providers_status()
    except Exception as e:
        providers = {"error": str(e)}
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="notification-service",
        version="1.0.0",
        providers=providers
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check(db: Session = Depends(get_session)):
    """Readiness check with database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Check external providers
        providers = {}
        try:
            from ..services.provider_service import ProviderService
            provider_service = ProviderService()
            providers = provider_service.get_providers_status()
        except Exception as e:
            providers = {"error": str(e)}
        
        return HealthResponse(
            status="ready",
            timestamp=datetime.utcnow(),
            service="notification-service",
            version="1.0.0",
            providers=providers
        )
    except Exception as e:
        return HealthResponse(
            status="not_ready",
            timestamp=datetime.utcnow(),
            service="notification-service",
            version="1.0.0",
            providers={"database": "error"}
        )
