"""
Tracking Service Business Logic
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from shared.models.enums import CourierStatus, TaskStatus, RouteStatus
from ..models import Courier, CourierLocationHistory, CourierTask, Route


class TrackingService:
    """Tracking service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_live_courier_locations(self, workspace_id: str) -> List[Courier]:
        """Get live locations of all active couriers"""
        # Get couriers that have updated location in last 10 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        
        return self.db.query(Courier).filter(
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False,
            Courier.status.in_([CourierStatus.AVAILABLE, CourierStatus.BUSY]),
            Courier.location_updated_at >= cutoff_time,
            Courier.current_latitude.isnot(None),
            Courier.current_longitude.isnot(None)
        ).all()
    
    def get_courier_live_location(self, courier_id: str, workspace_id: str) -> Optional[Courier]:
        """Get live location of specific courier"""
        return self.db.query(Courier).filter(
            Courier.id == courier_id,
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False,
            Courier.current_latitude.isnot(None),
            Courier.current_longitude.isnot(None)
        ).first()
    
    def get_order_courier_location(self, order_id: str, workspace_id: str) -> Optional[Courier]:
        """Get location of courier assigned to specific order"""
        # Find task for this order
        task = self.db.query(CourierTask).filter(
            CourierTask.order_id == order_id,
            CourierTask.workspace_id == workspace_id,
            CourierTask.is_deleted == False,
            CourierTask.status.in_([TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
        ).first()
        
        if not task or not task.courier_id:
            return None
        
        return self.get_courier_live_location(str(task.courier_id), workspace_id)
    
    def get_route_progress(self, route_id: str, workspace_id: str) -> Dict[str, Any]:
        """Get real-time progress of a route"""
        route = self.db.query(Route).filter(
            Route.id == route_id,
            Route.workspace_id == workspace_id,
            Route.is_deleted == False
        ).first()
        
        if not route:
            raise ValueError("Route not found")
        
        # Get all tasks for this route
        tasks = self.db.query(CourierTask).filter(
            CourierTask.route_id == route_id,
            CourierTask.is_deleted == False
        ).all()
        
        # Calculate progress
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in tasks if t.status == TaskStatus.FAILED])
        in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.IN_PROGRESS])
        
        # Get courier location if assigned
        courier_location = None
        if route.courier_id:
            courier = self.get_courier_live_location(str(route.courier_id), workspace_id)
            if courier:
                courier_location = {
                    "latitude": float(courier.current_latitude),
                    "longitude": float(courier.current_longitude),
                    "updated_at": courier.location_updated_at.isoformat() if courier.location_updated_at else None
                }
        
        # Calculate estimated completion time
        estimated_completion = None
        if route.status == RouteStatus.IN_PROGRESS and total_tasks > 0:
            avg_task_time = 30  # minutes per task (simplified)
            remaining_tasks = total_tasks - completed_tasks - failed_tasks
            estimated_completion = datetime.utcnow() + timedelta(minutes=remaining_tasks * avg_task_time)
        
        return {
            "route_id": str(route.id),
            "route_name": route.route_name,
            "status": route.status,
            "progress": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "courier_location": courier_location,
            "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
            "actual_start_time": route.actual_start_time.isoformat() if route.actual_start_time else None,
            "tasks": [
                {
                    "task_id": str(task.id),
                    "order_id": str(task.order_id),
                    "task_type": task.task_type,
                    "status": task.status,
                    "address": task.address,
                    "sequence_number": task.sequence_number,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                }
                for task in sorted(tasks, key=lambda t: t.sequence_number or 0)
            ]
        }
    
    def get_delivery_time_analytics(self, workspace_id: str, days: int = 7) -> Dict[str, Any]:
        """Get delivery time analytics for the workspace"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get completed delivery tasks
        completed_deliveries = self.db.query(CourierTask).filter(
            CourierTask.workspace_id == workspace_id,
            CourierTask.task_type == "delivery",
            CourierTask.status == TaskStatus.COMPLETED,
            CourierTask.completed_at >= since,
            CourierTask.is_deleted == False
        ).all()
        
        if not completed_deliveries:
            return {
                "period_days": days,
                "total_deliveries": 0,
                "average_delivery_time_minutes": 0,
                "on_time_percentage": 0,
                "daily_breakdown": []
            }
        
        # Calculate delivery times
        delivery_times = []
        on_time_count = 0
        
        for delivery in completed_deliveries:
            if delivery.scheduled_time and delivery.completed_at:
                delivery_time = (delivery.completed_at - delivery.scheduled_time).total_seconds() / 60
                delivery_times.append(delivery_time)
                
                # Consider on-time if within 15 minutes of scheduled time
                if abs(delivery_time) <= 15:
                    on_time_count += 1
        
        avg_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        on_time_percentage = (on_time_count / len(completed_deliveries)) * 100 if completed_deliveries else 0
        
        # Daily breakdown
        daily_breakdown = []
        for i in range(days):
            day = datetime.utcnow().date() - timedelta(days=i)
            day_deliveries = [d for d in completed_deliveries if d.completed_at.date() == day]
            
            daily_breakdown.append({
                "date": day.isoformat(),
                "deliveries": len(day_deliveries),
                "average_time": sum([
                    (d.completed_at - d.scheduled_time).total_seconds() / 60
                    for d in day_deliveries
                    if d.scheduled_time
                ]) / len(day_deliveries) if day_deliveries else 0
            })
        
        return {
            "period_days": days,
            "total_deliveries": len(completed_deliveries),
            "average_delivery_time_minutes": round(avg_delivery_time, 2),
            "on_time_percentage": round(on_time_percentage, 2),
            "daily_breakdown": list(reversed(daily_breakdown))
        }
    
    def get_courier_performance_analytics(
        self, workspace_id: str, courier_id: Optional[str] = None, days: int = 7
    ) -> Dict[str, Any]:
        """Get courier performance analytics"""
        since = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(Courier).filter(
            Courier.workspace_id == workspace_id,
            Courier.is_deleted == False
        )
        
        if courier_id:
            query = query.filter(Courier.id == courier_id)
        
        couriers = query.all()
        
        performance_data = []
        
        for courier in couriers:
            # Get tasks for this courier in the period
            tasks = self.db.query(CourierTask).filter(
                CourierTask.courier_id == courier.id,
                CourierTask.created_at >= since,
                CourierTask.is_deleted == False
            ).all()
            
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            failed_tasks = [t for t in tasks if t.status == TaskStatus.FAILED]
            
            # Calculate metrics
            total_tasks = len(tasks)
            success_rate = (len(completed_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            
            # Calculate average completion time
            completion_times = []
            for task in completed_tasks:
                if task.actual_arrival and task.completed_at:
                    completion_time = (task.completed_at - task.actual_arrival).total_seconds() / 60
                    completion_times.append(completion_time)
            
            avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Calculate distance (simplified - would need actual GPS tracking)
            total_distance = len(completed_tasks) * 5  # 5km per delivery (simplified)
            
            performance_data.append({
                "courier_id": str(courier.id),
                "user_id": str(courier.user_id),
                "period_start": since.isoformat(),
                "period_end": datetime.utcnow().isoformat(),
                "total_tasks": total_tasks,
                "completed_tasks": len(completed_tasks),
                "failed_tasks": len(failed_tasks),
                "success_rate": round(success_rate, 2),
                "average_completion_time_minutes": round(avg_completion_time, 2),
                "total_distance_km": total_distance,
                "average_rating": float(courier.average_rating) if courier.average_rating else None
            })
        
        return {
            "period_days": days,
            "courier_performance": performance_data
        }
    
    def get_public_order_tracking(self, order_id: str, tracking_code: str) -> Dict[str, Any]:
        """Public order tracking for customers"""
        # Find task for this order
        task = self.db.query(CourierTask).filter(
            CourierTask.order_id == order_id,
            CourierTask.is_deleted == False
        ).first()
        
        if not task:
            raise ValueError("Order not found")
        
        # Verify tracking code (simplified - in production, use proper tracking codes)
        expected_code = f"TRK{str(order_id)[-6:].upper()}"
        if tracking_code != expected_code:
            raise ValueError("Invalid tracking code")
        
        # Get courier location if assigned and in progress
        courier_location = None
        estimated_arrival = None
        
        if task.courier_id and task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
            courier = self.db.query(Courier).filter(
                Courier.id == task.courier_id,
                Courier.is_deleted == False
            ).first()
            
            if courier and courier.current_latitude and courier.current_longitude:
                courier_location = {
                    "latitude": float(courier.current_latitude),
                    "longitude": float(courier.current_longitude),
                    "last_updated": courier.location_updated_at.isoformat() if courier.location_updated_at else None
                }
                
                # Estimate arrival (simplified)
                if task.status == TaskStatus.IN_PROGRESS:
                    estimated_arrival = (datetime.utcnow() + timedelta(minutes=15)).isoformat()
        
        return {
            "order_id": str(task.order_id),
            "tracking_code": tracking_code,
            "status": task.status,
            "task_type": task.task_type,
            "delivery_address": task.address,
            "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
            "estimated_arrival": estimated_arrival,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "courier_location": courier_location,
            "status_history": [
                {
                    "status": task.status,
                    "timestamp": task.updated_at.isoformat(),
                    "description": self._get_status_description(task.status)
                }
            ]
        }
    
    def get_delivery_heatmap(self, workspace_id: str, days: int = 30) -> Dict[str, Any]:
        """Get delivery heatmap data"""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get completed deliveries with coordinates
        deliveries = self.db.query(CourierTask).filter(
            CourierTask.workspace_id == workspace_id,
            CourierTask.task_type == "delivery",
            CourierTask.status == TaskStatus.COMPLETED,
            CourierTask.completed_at >= since,
            CourierTask.latitude.isnot(None),
            CourierTask.longitude.isnot(None),
            CourierTask.is_deleted == False
        ).all()
        
        heatmap_points = []
        for delivery in deliveries:
            heatmap_points.append({
                "latitude": float(delivery.latitude),
                "longitude": float(delivery.longitude),
                "weight": 1,
                "completed_at": delivery.completed_at.isoformat()
            })
        
        return {
            "period_days": days,
            "total_deliveries": len(deliveries),
            "heatmap_points": heatmap_points
        }
    
    def get_zone_coverage_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get delivery zone coverage statistics"""
        # This would integrate with delivery zones
        # For now, return placeholder data
        return {
            "total_zones": 0,
            "active_zones": 0,
            "coverage_percentage": 0,
            "zones": []
        }
    
    def _get_status_description(self, status: TaskStatus) -> str:
        """Get human-readable status description"""
        descriptions = {
            TaskStatus.PENDING: "Order received and being processed",
            TaskStatus.ASSIGNED: "Assigned to courier",
            TaskStatus.IN_PROGRESS: "Courier is on the way",
            TaskStatus.COMPLETED: "Delivered successfully",
            TaskStatus.FAILED: "Delivery failed",
            TaskStatus.CANCELLED: "Order cancelled"
        }
        return descriptions.get(status, "Unknown status")
