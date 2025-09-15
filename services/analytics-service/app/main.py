"""
Analytics Service - Main FastAPI application
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.utils.database import init_database
from shared.utils.messaging import init_messaging
from shared.models.base import Base
from .routers import analytics, reports, metrics, alerts, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Analytics Service...")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "sqlite:///./analytics_service.db")
    db_manager = init_database(database_url, echo=False)
    
    # Create tables
    db_manager.create_tables(Base)
    
    # Initialize messaging
    init_messaging("analytics-service")
    
    # Start background tasks for metrics aggregation
    # from .services.aggregation_service import AggregationService
    # aggregation_service = AggregationService()
    # aggregation_service.start_background_tasks()
    
    print("✅ Analytics Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Analytics Service...")


# Create FastAPI app
app = FastAPI(
    title="Delox Analytics Service",
    description="Analytics and reporting service for Delox delivery management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if os.getenv("DEBUG") else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
