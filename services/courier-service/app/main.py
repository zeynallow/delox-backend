"""
Courier Service - Main FastAPI application
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.utils.database import init_database
from shared.utils.messaging import init_messaging
from shared.models.base import Base
from .routers import couriers, routes, tasks, tracking, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Courier Service...")
    
    # Initialize database
    database_url = os.getenv("DATABASE_URL", "sqlite:///./courier_service.db")
    db_manager = init_database(database_url, echo=False)
    
    # Create tables
    db_manager.create_tables(Base)
    
    # Initialize messaging
    init_messaging("courier-service")
    
    print("✅ Courier Service started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Courier Service...")


# Create FastAPI app
app = FastAPI(
    title="Delox Courier Service",
    description="Courier and route management service for Delox delivery management platform",
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
app.include_router(couriers.router, prefix="/api/v1/couriers", tags=["Couriers"])
app.include_router(routes.router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(tracking.router, prefix="/api/v1/tracking", tags=["Tracking"])


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
