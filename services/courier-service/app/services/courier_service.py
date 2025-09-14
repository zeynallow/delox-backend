"""
Courier Service Business Logic
"""
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from shared.utils.messaging import get_event_publisher, EventTypes
from shared.models.enums import CourierStatus, UserRole
from ..models import Courier, CourierLocationHistory
from ..schemas import CourierCreate, CourierUpdate, LocationUpdate, CourierDashboard


class CourierService:
    """Courier service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_courier(self, workspace_id: str, courier_data: CourierCreate) -> Courier:
        """Create new courier"""
        # Check if courier already exists for this user
        existing_courier = self.db.query(Courier).filter(
            Courier.user_id == courier_data.user_id,
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False
        ).first()
        
        if existing_courier:
            raise ValueError("Courier already exists for this user")
        
        # Create courier
        courier = Courier(
            workspace_id=workspace_id,
            user_id=courier_data.user_id,
            vehicle_type=courier_data.vehicle_type,
            vehicle_plate=courier_data.vehicle_plate,
            vehicle_capacity=courier_data.vehicle_capacity,
            max_delivery_distance=courier_data.max_delivery_distance,
            working_hours_start=courier_data.working_hours_start,
            working_hours_end=courier_data.working_hours_end,
            working_days=courier_data.working_days or [1, 2, 3, 4, 5],  # Mon-Fri default
            status=CourierStatus.OFFLINE
        )
        
        self.db.add(courier)
        self.db.commit()
        self.db.refresh(courier)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.COURIER_ASSIGNED,
                {
                    "courier_id": str(courier.id),
                    "user_id": str(courier.user_id),
                    "workspace_id": str(courier.workspace_id),
                    "vehicle_type": courier.vehicle_type
                },
                workspace_id=str(courier.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish courier created event: {e}")
        
        return courier
    
    def get_courier_by_id(self, courier_id: str) -> Optional[Courier]:
        """Get courier by ID"""
        return self.db.query(Courier).filter(
            Courier.id == courier_id,
            Courier.is_deleted == False
        ).first()
    
    def get_courier_by_user_id(self, user_id: str) -> Optional[Courier]:
        """Get courier by user ID"""
        return self.db.query(Courier).filter(
            Courier.user_id == user_id,
            Courier.is_deleted == False
        ).first()
    
    def get_courier_by_id_and_workspace(self, courier_id: str, workspace_id: str) -> Optional[Courier]:
        """Get courier by ID and workspace"""
        return self.db.query(Courier).filter(
            Courier.id == courier_id,
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False
        ).first()
    
    def list_couriers(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[CourierStatus] = None,
        available_only: bool = False
    ) -> Tuple[List[Courier], int]:
        """List couriers in workspace with filtering"""
        query = self.db.query(Courier).filter(
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False
        )
        
        # Apply status filter
        if status:
            query = query.filter(Courier.status == status)
        
        # Apply availability filter
        if available_only:
            query = query.filter(
                Courier.is_available == True,
                Courier.status.in_([CourierStatus.AVAILABLE, CourierStatus.BUSY])
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        couriers = query.offset(skip).limit(limit).all()
        
        return couriers, total
    
    def update_courier(self, courier_id: str, courier_data: CourierUpdate) -> Courier:
        """Update courier"""
        courier = self.get_courier_by_id(courier_id)
        if not courier:
            raise ValueError("Courier not found")
        
        # Update fields
        update_data = courier_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(courier, field):
                setattr(courier, field, value)
        
        self.db.commit()
        self.db.refresh(courier)
        
        return courier
    
    def update_courier_by_user_id(self, user_id: str, courier_data: CourierUpdate) -> Courier:
        """Update courier by user ID"""
        courier = self.get_courier_by_user_id(user_id)
        if not courier:
            raise ValueError("Courier not found")
        
        return self.update_courier(str(courier.id), courier_data)
    
    def delete_courier(self, courier_id: str, workspace_id: str):
        """Soft delete courier"""
        courier = self.get_courier_by_id_and_workspace(courier_id, workspace_id)
        if not courier:
            raise ValueError("Courier not found")
        
        courier.is_deleted = True
        courier.deleted_at = datetime.utcnow()
        
        self.db.commit()
    
    def update_courier_location(self, user_id: str, location_data: LocationUpdate):
        """Update courier location"""
        courier = self.get_courier_by_user_id(user_id)
        if not courier:
            raise ValueError("Courier not found")
        
        # Update current location
        courier.current_latitude = location_data.latitude
        courier.current_longitude = location_data.longitude
        courier.location_updated_at = datetime.utcnow()
        courier.location_accuracy = location_data.accuracy
        courier.last_seen_at = datetime.utcnow()
        
        # Save location history
        location_history = CourierLocationHistory(
            workspace_id=courier.workspace_id,
            courier_id=courier.id,
            latitude=location_data.latitude,
            longitude=location_data.longitude,
            accuracy=location_data.accuracy,
            altitude=location_data.altitude,
            speed=location_data.speed,
            heading=location_data.heading,
            route_id=courier.current_route_id,
            battery_level=location_data.battery_level,
            is_charging=location_data.is_charging
        )
        
        self.db.add(location_history)
        self.db.commit()
        
        # Publish location update event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.COURIER_LOCATION_UPDATED,
                {
                    "courier_id": str(courier.id),
                    "user_id": str(courier.user_id),
                    "latitude": float(location_data.latitude),
                    "longitude": float(location_data.longitude),
                    "timestamp": datetime.utcnow().isoformat(),
                    "route_id": str(courier.current_route_id) if courier.current_route_id else None
                },
                workspace_id=str(courier.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish location update event: {e}")
    
    def get_location_history(self, courier_id: str, hours: int = 24) -> List[CourierLocationHistory]:
        """Get courier location history"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return self.db.query(CourierLocationHistory).filter(
            CourierLocationHistory.courier_id == courier_id,
            CourierLocationHistory.created_at >= since
        ).order_by(CourierLocationHistory.created_at.desc()).all()
    
    def update_courier_status(self, user_id: str, new_status: CourierStatus):
        """Update courier status"""
        courier = self.get_courier_by_user_id(user_id)
        if not courier:
            raise ValueError("Courier not found")
        
        old_status = courier.status
        courier.status = new_status
        courier.last_seen_at = datetime.utcnow()
        
        # Update availability based on status
        if new_status == CourierStatus.OFFLINE:
            courier.is_available = False
        elif new_status in [CourierStatus.AVAILABLE, CourierStatus.BUSY]:
            courier.is_available = True
        
        self.db.commit()
        
        # Publish status change event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.COURIER_STATUS_CHANGED,
                {
                    "courier_id": str(courier.id),
                    "user_id": str(courier.user_id),
                    "old_status": old_status,
                    "new_status": new_status,
                    "timestamp": datetime.utcnow().isoformat()
                },
                workspace_id=str(courier.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish status change event: {e}")
    
    def get_courier_dashboard(self, user_id: str) -> CourierDashboard:
        """Get courier dashboard data for mobile app"""
        courier = self.get_courier_by_user_id(user_id)
        if not courier:
            raise ValueError("Courier not found")
        
        # Get current route
        current_route = None
        if courier.current_route_id:
            from .route_service import RouteService
            route_service = RouteService(self.db)
            current_route = route_service.get_route_with_tasks(str(courier.current_route_id))
        
        # Get pending tasks
        from .task_service import TaskService
        task_service = TaskService(self.db)
        pending_tasks = task_service.get_pending_tasks_for_courier(user_id)
        
        # Get today's stats
        today = datetime.utcnow().date()
        today_stats = {
            "deliveries_completed": 0,  # TODO: Calculate from tasks
            "distance_traveled": 0,     # TODO: Calculate from location history
            "earnings": 0,              # TODO: Calculate from completed deliveries
            "hours_worked": 0           # TODO: Calculate from status changes
        }
        
        # Get notifications (placeholder)
        notifications = []
        
        from ..schemas import CourierResponse, TaskResponse

        return CourierDashboard(
            courier=CourierResponse.from_orm(courier),
            current_route=current_route,
            pending_tasks=[TaskResponse.from_orm(task) for task in pending_tasks],
            today_stats=today_stats,
            notifications=notifications
        )
    
    def get_available_couriers(self, workspace_id: str) -> List[Courier]:
        """Get available couriers for assignment"""
        return self.db.query(Courier).filter(
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False,
            Courier.is_available == True,
            Courier.status == CourierStatus.AVAILABLE
        ).all()
    
    def assign_courier_to_route(self, courier_id: str, route_id: str):
        """Assign courier to route"""
        courier = self.get_courier_by_id(courier_id)
        if not courier:
            raise ValueError("Courier not found")
        
        if not courier.is_available:
            raise ValueError("Courier is not available")
        
        courier.current_route_id = route_id
        courier.status = CourierStatus.BUSY
        
        self.db.commit()
    
    def unassign_courier_from_route(self, courier_id: str):
        """Unassign courier from route"""
        courier = self.get_courier_by_id(courier_id)
        if not courier:
            raise ValueError("Courier not found")
        
        courier.current_route_id = None
        courier.status = CourierStatus.AVAILABLE
        courier.active_tasks_count = 0
        
        self.db.commit()
