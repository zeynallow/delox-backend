"""
Route management router
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_manager, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import RouteStatus
from ..schemas import (
    RouteCreate, RouteUpdate, RouteResponse, RouteWithTasks,
    OptimizationRequest, OptimizationResponse
)
from ..services.route_service import RouteService

router = APIRouter()


@router.get("/", response_model=List[RouteResponse])
async def list_routes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[RouteStatus] = Query(None),
    courier_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List routes in workspace"""
    route_service = RouteService(db)
    
    routes, total = route_service.list_routes(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        status=status,
        courier_id=courier_id
    )
    
    return [RouteResponse.from_orm(route) for route in routes]


@router.post("/", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def create_route(
    route_data: RouteCreate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create new route (manager/admin only)"""
    route_service = RouteService(db)
    
    try:
        route = route_service.create_route(
            workspace_id=str(current_user.workspace_id),
            route_data=route_data
        )
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{route_id}", response_model=RouteWithTasks)
async def get_route(
    route_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get route by ID with tasks"""
    route_service = RouteService(db)
    
    route = route_service.get_route_by_id_and_workspace(
        route_id=route_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not route:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found"
        )
    
    # Get route with tasks
    route_with_tasks = route_service.get_route_with_tasks(route_id)
    return route_with_tasks


@router.put("/{route_id}", response_model=RouteResponse)
async def update_route(
    route_id: str,
    route_data: RouteUpdate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Update route (manager/admin only)"""
    route_service = RouteService(db)
    
    try:
        route = route_service.update_route(route_id, route_data)
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{route_id}", response_model=SuccessResponse)
async def delete_route(
    route_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Delete route (manager/admin only)"""
    route_service = RouteService(db)
    
    try:
        route_service.delete_route(route_id, str(current_user.workspace_id))
        return SuccessResponse(message="Route deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Route assignment
@router.put("/{route_id}/assign", response_model=RouteResponse)
async def assign_route(
    route_id: str,
    courier_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Assign route to courier (manager/admin only)"""
    route_service = RouteService(db)
    
    try:
        route = route_service.assign_route_to_courier(route_id, courier_id)
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{route_id}/unassign", response_model=RouteResponse)
async def unassign_route(
    route_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Unassign route from courier (manager/admin only)"""
    route_service = RouteService(db)
    
    try:
        route = route_service.unassign_route(route_id)
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Route optimization
@router.post("/optimize", response_model=OptimizationResponse, status_code=status.HTTP_201_CREATED)
async def optimize_routes(
    optimization_data: OptimizationRequest,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Optimize routes for multiple couriers and orders"""
    route_service = RouteService(db)
    
    try:
        optimization = route_service.optimize_routes(
            workspace_id=str(current_user.workspace_id),
            optimization_data=optimization_data,
            requested_by=str(current_user.user_id)
        )
        return OptimizationResponse.from_orm(optimization)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/optimization/{optimization_id}", response_model=OptimizationResponse)
async def get_optimization_result(
    optimization_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get route optimization result"""
    route_service = RouteService(db)
    
    optimization = route_service.get_optimization_by_id_and_workspace(
        optimization_id=optimization_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Optimization not found"
        )
    
    return OptimizationResponse.from_orm(optimization)


# Route control for couriers
@router.put("/{route_id}/start", response_model=RouteResponse)
async def start_route(
    route_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Start route (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can start routes"
        )
    
    route_service = RouteService(db)
    
    try:
        route = route_service.start_route(route_id, str(current_user.user_id))
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{route_id}/complete", response_model=RouteResponse)
async def complete_route(
    route_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Complete route (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can complete routes"
        )
    
    route_service = RouteService(db)
    
    try:
        route = route_service.complete_route(route_id, str(current_user.user_id))
        return RouteResponse.from_orm(route)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Get current route for courier
@router.get("/current/me", response_model=Optional[RouteWithTasks])
async def get_current_route(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get current route for courier (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access current route"
        )
    
    route_service = RouteService(db)
    
    try:
        route = route_service.get_current_route_for_courier(str(current_user.user_id))
        return route
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
