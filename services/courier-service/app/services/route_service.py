"""
Route Service Business Logic
"""
import math
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from shared.utils.messaging import get_event_publisher, EventTypes
from shared.models.enums import RouteStatus, TaskStatus, TaskType
from ..models import Route, RouteOptimization, Courier, CourierTask
from ..schemas import RouteCreate, RouteUpdate, OptimizationRequest, RouteWithTasks


class RouteService:
    """Route service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_route(self, workspace_id: str, route_data: RouteCreate) -> Route:
        """Create new route"""
        # Create route
        route = Route(
            workspace_id=workspace_id,
            route_name=route_data.route_name,
            courier_id=route_data.courier_id,
            total_orders=len(route_data.order_ids),
            planned_start_time=route_data.planned_start_time
        )
        
        self.db.add(route)
        self.db.flush()  # Get route ID
        
        # Create tasks for each order
        from .task_service import TaskService
        task_service = TaskService(self.db)
        
        for i, order_id in enumerate(route_data.order_ids):
            # Create pickup and delivery tasks for each order
            # This is simplified - in real implementation, you'd get order details
            pickup_task = CourierTask(
                workspace_id=workspace_id,
                order_id=order_id,
                task_type=TaskType.PICKUP,
                courier_id=route_data.courier_id,
                route_id=route.id,
                sequence_number=i * 2,  # Even numbers for pickups
                address=f"Pickup address for order {order_id}",  # TODO: Get from order service
                status=TaskStatus.PENDING
            )
            
            delivery_task = CourierTask(
                workspace_id=workspace_id,
                order_id=order_id,
                task_type=TaskType.DELIVERY,
                courier_id=route_data.courier_id,
                route_id=route.id,
                sequence_number=i * 2 + 1,  # Odd numbers for deliveries
                address=f"Delivery address for order {order_id}",  # TODO: Get from order service
                status=TaskStatus.PENDING
            )
            
            self.db.add(pickup_task)
            self.db.add(delivery_task)
        
        # Assign courier if specified
        if route_data.courier_id:
            from .courier_service import CourierService
            courier_service = CourierService(self.db)
            courier_service.assign_courier_to_route(str(route_data.courier_id), str(route.id))
        
        self.db.commit()
        self.db.refresh(route)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.ROUTE_OPTIMIZED,
                {
                    "route_id": str(route.id),
                    "courier_id": str(route.courier_id) if route.courier_id else None,
                    "total_orders": route.total_orders,
                    "workspace_id": str(route.workspace_id)
                },
                workspace_id=str(route.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish route created event: {e}")
        
        return route
    
    def get_route_by_id(self, route_id: str) -> Optional[Route]:
        """Get route by ID"""
        return self.db.query(Route).filter(
            Route.id == route_id,
            Route.is_deleted == False
        ).first()
    
    def get_route_by_id_and_workspace(self, route_id: str, workspace_id: str) -> Optional[Route]:
        """Get route by ID and workspace"""
        return self.db.query(Route).filter(
            Route.id == route_id,
            Route.workspace_id == workspace_id,
            Route.is_deleted == False
        ).first()
    
    def list_routes(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[RouteStatus] = None,
        courier_id: Optional[str] = None
    ) -> Tuple[List[Route], int]:
        """List routes in workspace with filtering"""
        query = self.db.query(Route).filter(
            Route.workspace_id == workspace_id,
            Route.is_deleted == False
        )
        
        # Apply status filter
        if status:
            query = query.filter(Route.status == status)
        
        # Apply courier filter
        if courier_id:
            query = query.filter(Route.courier_id == courier_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        routes = query.order_by(Route.created_at.desc()).offset(skip).limit(limit).all()
        
        return routes, total
    
    def update_route(self, route_id: str, route_data: RouteUpdate) -> Route:
        """Update route"""
        route = self.get_route_by_id(route_id)
        if not route:
            raise ValueError("Route not found")
        
        # Update fields
        update_data = route_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(route, field):
                setattr(route, field, value)
        
        self.db.commit()
        self.db.refresh(route)
        
        return route
    
    def delete_route(self, route_id: str, workspace_id: str):
        """Soft delete route"""
        route = self.get_route_by_id_and_workspace(route_id, workspace_id)
        if not route:
            raise ValueError("Route not found")
        
        # Can't delete active routes
        if route.status == RouteStatus.IN_PROGRESS:
            raise ValueError("Cannot delete route in progress")
        
        route.is_deleted = True
        route.deleted_at = datetime.utcnow()
        
        # Also delete associated tasks
        self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id
        ).update({
            "is_deleted": True,
            "deleted_at": datetime.utcnow()
        })
        
        self.db.commit()
    
    def assign_route_to_courier(self, route_id: str, courier_id: str) -> Route:
        """Assign route to courier"""
        route = self.get_route_by_id(route_id)
        if not route:
            raise ValueError("Route not found")
        
        if route.status != RouteStatus.PENDING:
            raise ValueError("Can only assign pending routes")
        
        # Check if courier is available
        courier = self.db.query(Courier).filter(
            Courier.id == courier_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier:
            raise ValueError("Courier not found")
        
        if not courier.is_available:
            raise ValueError("Courier is not available")
        
        # Assign route
        route.courier_id = courier_id
        route.assigned_at = datetime.utcnow()
        
        # Update all tasks in route
        self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id
        ).update({"courier_id": courier_id})
        
        # Update courier
        from .courier_service import CourierService
        courier_service = CourierService(self.db)
        courier_service.assign_courier_to_route(courier_id, route_id)
        
        self.db.commit()
        self.db.refresh(route)
        
        return route
    
    def unassign_route(self, route_id: str) -> Route:
        """Unassign route from courier"""
        route = self.get_route_by_id(route_id)
        if not route:
            raise ValueError("Route not found")
        
        if route.status == RouteStatus.IN_PROGRESS:
            raise ValueError("Cannot unassign route in progress")
        
        courier_id = route.courier_id
        
        # Unassign route
        route.courier_id = None
        route.assigned_at = None
        
        # Update all tasks in route
        self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id
        ).update({"courier_id": None})
        
        # Update courier if assigned
        if courier_id:
            from .courier_service import CourierService
            courier_service = CourierService(self.db)
            courier_service.unassign_courier_from_route(str(courier_id))
        
        self.db.commit()
        self.db.refresh(route)
        
        return route
    
    def start_route(self, route_id: str, courier_user_id: str) -> Route:
        """Start route (for courier app)"""
        route = self.get_route_by_id(route_id)
        if not route:
            raise ValueError("Route not found")
        
        # Verify courier owns this route
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.id == route.courier_id
        ).first()
        
        if not courier:
            raise ValueError("Route not assigned to this courier")
        
        if route.status != RouteStatus.PENDING:
            raise ValueError("Route is not in pending status")
        
        # Start route
        route.status = RouteStatus.IN_PROGRESS
        route.actual_start_time = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(route)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.ROUTE_STARTED,
                {
                    "route_id": str(route.id),
                    "courier_id": str(route.courier_id),
                    "started_at": route.actual_start_time.isoformat()
                },
                workspace_id=str(route.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish route started event: {e}")
        
        return route
    
    def complete_route(self, route_id: str, courier_user_id: str) -> Route:
        """Complete route (for courier app)"""
        route = self.get_route_by_id(route_id)
        if not route:
            raise ValueError("Route not found")
        
        # Verify courier owns this route
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.id == route.courier_id
        ).first()
        
        if not courier:
            raise ValueError("Route not assigned to this courier")
        
        if route.status != RouteStatus.IN_PROGRESS:
            raise ValueError("Route is not in progress")
        
        # Check if all tasks are completed
        pending_tasks = self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id,
            CourierTask.status.in_([TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
        ).count()
        
        if pending_tasks > 0:
            raise ValueError("Cannot complete route with pending tasks")
        
        # Complete route
        route.status = RouteStatus.COMPLETED
        route.actual_end_time = datetime.utcnow()
        
        # Update courier availability
        from .courier_service import CourierService
        courier_service = CourierService(self.db)
        courier_service.unassign_courier_from_route(str(route.courier_id))
        
        self.db.commit()
        self.db.refresh(route)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.ROUTE_COMPLETED,
                {
                    "route_id": str(route.id),
                    "courier_id": str(route.courier_id),
                    "completed_at": route.actual_end_time.isoformat(),
                    "total_tasks": route.completed_tasks + route.failed_tasks
                },
                workspace_id=str(route.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish route completed event: {e}")
        
        return route
    
    def get_route_with_tasks(self, route_id: str) -> Optional[RouteWithTasks]:
        """Get route with all tasks"""
        route = self.get_route_by_id(route_id)
        if not route:
            return None
        
        tasks = self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id,
            CourierTask.is_deleted == False
        ).order_by(CourierTask.sequence_number).all()
        
        from ..schemas import RouteResponse, TaskResponse
        
        return RouteWithTasks(
            **RouteResponse.from_orm(route).dict(),
            tasks=[TaskResponse.from_orm(task) for task in tasks]
        )
    
    def get_current_route_for_courier(self, courier_user_id: str) -> Optional[RouteWithTasks]:
        """Get current route for courier"""
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier or not courier.current_route_id:
            return None
        
        return self.get_route_with_tasks(str(courier.current_route_id))
    
    def optimize_routes(
        self,
        workspace_id: str,
        optimization_data: OptimizationRequest,
        requested_by: str
    ) -> RouteOptimization:
        """Optimize routes for multiple couriers and orders"""
        # Create optimization record
        optimization = RouteOptimization(
            workspace_id=workspace_id,
            optimization_type=optimization_data.optimization_type,
            requested_by=requested_by,
            courier_ids=optimization_data.courier_ids,
            order_ids=optimization_data.order_ids,
            constraints=optimization_data.constraints or {},
            status="processing",
            started_at=datetime.utcnow()
        )
        
        self.db.add(optimization)
        self.db.flush()
        
        try:
            # Simple optimization algorithm (in production, use more sophisticated algorithms)
            optimized_routes = self._simple_route_optimization(
                optimization_data.courier_ids,
                optimization_data.order_ids,
                workspace_id
            )
            
            optimization.optimized_routes = optimized_routes
            optimization.status = "completed"
            optimization.completed_at = datetime.utcnow()
            optimization.processing_time_seconds = int(
                (optimization.completed_at - optimization.started_at).total_seconds()
            )
            
        except Exception as e:
            optimization.status = "failed"
            optimization.error_message = str(e)
            optimization.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(optimization)
        
        return optimization
    
    def get_optimization_by_id_and_workspace(
        self, optimization_id: str, workspace_id: str
    ) -> Optional[RouteOptimization]:
        """Get optimization by ID and workspace"""
        return self.db.query(RouteOptimization).filter(
            RouteOptimization.id == optimization_id,
            RouteOptimization.workspace_id == workspace_id,
            RouteOptimization.is_deleted == False
        ).first()
    
    def _simple_route_optimization(
        self, courier_ids: List[UUID], order_ids: List[UUID], workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Simple route optimization algorithm"""
        # This is a simplified implementation
        # In production, you'd use more sophisticated algorithms like:
        # - Vehicle Routing Problem (VRP) solvers
        # - Google OR-Tools
        # - Machine learning-based optimization
        
        optimized_routes = []
        orders_per_courier = len(order_ids) // len(courier_ids)
        
        for i, courier_id in enumerate(courier_ids):
            start_idx = i * orders_per_courier
            end_idx = start_idx + orders_per_courier
            
            # Last courier gets remaining orders
            if i == len(courier_ids) - 1:
                end_idx = len(order_ids)
            
            courier_orders = order_ids[start_idx:end_idx]
            
            optimized_routes.append({
                "courier_id": str(courier_id),
                "order_ids": [str(order_id) for order_id in courier_orders],
                "estimated_distance_km": len(courier_orders) * 5,  # Simplified
                "estimated_duration_minutes": len(courier_orders) * 30,  # Simplified
                "waypoints": []  # TODO: Calculate actual waypoints
            })
        
        return optimized_routes
