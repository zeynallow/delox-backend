"""
Task Service Business Logic
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from shared.utils.messaging import get_event_publisher, EventTypes
from shared.models.enums import TaskStatus, TaskType
from ..models import CourierTask, Courier, Route
from ..schemas import TaskCreate, TaskUpdate


class TaskService:
    """Task service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, workspace_id: str, task_data: TaskCreate) -> CourierTask:
        """Create new task"""
        # Create task
        task = CourierTask(
            workspace_id=workspace_id,
            order_id=task_data.order_id,
            task_type=task_data.task_type,
            address=task_data.address,
            latitude=task_data.latitude,
            longitude=task_data.longitude,
            contact_name=task_data.contact_name,
            contact_phone=task_data.contact_phone,
            scheduled_time=task_data.scheduled_time,
            notes=task_data.notes,
            special_instructions=task_data.special_instructions,
            status=TaskStatus.PENDING
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_task_by_id(self, task_id: str) -> Optional[CourierTask]:
        """Get task by ID"""
        return self.db.query(CourierTask).filter(
            CourierTask.id == task_id,
            CourierTask.is_deleted == False
        ).first()
    
    def get_task_by_id_and_workspace(self, task_id: str, workspace_id: str) -> Optional[CourierTask]:
        """Get task by ID and workspace"""
        return self.db.query(CourierTask).filter(
            CourierTask.id == task_id,
            CourierTask.workspace_id == workspace_id,
            CourierTask.is_deleted == False
        ).first()
    
    def list_tasks(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        courier_id: Optional[str] = None
    ) -> Tuple[List[CourierTask], int]:
        """List tasks in workspace with filtering"""
        query = self.db.query(CourierTask).filter(
            CourierTask.workspace_id == workspace_id,
            CourierTask.is_deleted == False
        )
        
        # Apply status filter
        if status:
            query = query.filter(CourierTask.status == status)
        
        # Apply task type filter
        if task_type:
            query = query.filter(CourierTask.task_type == task_type)
        
        # Apply courier filter
        if courier_id:
            query = query.filter(CourierTask.courier_id == courier_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        tasks = query.order_by(CourierTask.created_at.desc()).offset(skip).limit(limit).all()
        
        return tasks, total
    
    def update_task(self, task_id: str, task_data: TaskUpdate) -> CourierTask:
        """Update task"""
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # Update fields
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        # Update completion timestamp if status changed to completed
        if task_data.status == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def delete_task(self, task_id: str, workspace_id: str):
        """Soft delete task"""
        task = self.get_task_by_id_and_workspace(task_id, workspace_id)
        if not task:
            raise ValueError("Task not found")
        
        # Can't delete tasks in progress
        if task.status == TaskStatus.IN_PROGRESS:
            raise ValueError("Cannot delete task in progress")
        
        task.is_deleted = True
        task.deleted_at = datetime.utcnow()
        
        self.db.commit()
    
    def assign_task_to_courier(self, task_id: str, courier_id: str) -> CourierTask:
        """Assign task to courier"""
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.status != TaskStatus.PENDING:
            raise ValueError("Can only assign pending tasks")
        
        # Check if courier exists and is available
        courier = self.db.query(Courier).filter(
            Courier.id == courier_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier:
            raise ValueError("Courier not found")
        
        # Assign task
        task.courier_id = courier_id
        task.status = TaskStatus.ASSIGNED
        
        # Update courier's active task count
        courier.active_tasks_count += 1
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def unassign_task(self, task_id: str) -> CourierTask:
        """Unassign task from courier"""
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        
        if task.status == TaskStatus.IN_PROGRESS:
            raise ValueError("Cannot unassign task in progress")
        
        # Update courier's active task count
        if task.courier_id:
            courier = self.db.query(Courier).filter(Courier.id == task.courier_id).first()
            if courier and courier.active_tasks_count > 0:
                courier.active_tasks_count -= 1
        
        # Unassign task
        task.courier_id = None
        task.status = TaskStatus.PENDING
        
        self.db.commit()
        self.db.refresh(task)
        
        return task
    
    def get_assigned_tasks_for_courier(self, courier_user_id: str) -> List[CourierTask]:
        """Get all assigned tasks for courier"""
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier:
            raise ValueError("Courier not found")
        
        return self.db.query(CourierTask).filter(
            CourierTask.courier_id == courier.id,
            CourierTask.status.in_([TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]),
            CourierTask.is_deleted == False
        ).order_by(CourierTask.sequence_number, CourierTask.scheduled_time).all()
    
    def get_pending_tasks_for_courier(self, courier_user_id: str) -> List[CourierTask]:
        """Get pending tasks for courier"""
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier:
            raise ValueError("Courier not found")
        
        return self.db.query(CourierTask).filter(
            CourierTask.courier_id == courier.id,
            CourierTask.status == TaskStatus.PENDING,
            CourierTask.is_deleted == False
        ).order_by(CourierTask.sequence_number, CourierTask.scheduled_time).all()
    
    def get_next_task_for_courier(self, courier_user_id: str) -> Optional[CourierTask]:
        """Get next task for courier"""
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_user_id,
            Courier.is_deleted == False
        ).first()
        
        if not courier:
            raise ValueError("Courier not found")
        
        return self.db.query(CourierTask).filter(
            CourierTask.courier_id == courier.id,
            CourierTask.status.in_([TaskStatus.ASSIGNED, TaskStatus.PENDING]),
            CourierTask.is_deleted == False
        ).order_by(CourierTask.sequence_number, CourierTask.scheduled_time).first()
    
    def perform_task_action(
        self,
        task_id: str,
        action: str,
        courier_id: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        notes: Optional[str] = None,
        photo_url: Optional[str] = None,
        signature_url: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> CourierTask:
        """Perform action on task (for courier app)"""
        task = self.get_task_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        
        # Verify courier owns this task
        courier = self.db.query(Courier).filter(
            Courier.user_id == courier_id,
            Courier.id == task.courier_id
        ).first()
        
        if not courier:
            raise ValueError("Task not assigned to this courier")
        
        current_time = datetime.utcnow()
        
        if action == "start":
            if task.status != TaskStatus.ASSIGNED:
                raise ValueError("Can only start assigned tasks")
            
            task.status = TaskStatus.IN_PROGRESS
            task.actual_arrival = current_time
            
        elif action == "complete":
            if task.status != TaskStatus.IN_PROGRESS:
                raise ValueError("Can only complete tasks in progress")
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = current_time
            task.completion_notes = notes
            task.completion_photo_url = photo_url
            task.signature_url = signature_url
            
            # Update courier's active task count
            if courier.active_tasks_count > 0:
                courier.active_tasks_count -= 1
            
            # Update route progress
            if task.route_id:
                route = self.db.query(Route).filter(Route.id == task.route_id).first()
                if route:
                    route.completed_tasks += 1
            
        elif action == "fail":
            if task.status not in [TaskStatus.IN_PROGRESS, TaskStatus.ASSIGNED]:
                raise ValueError("Can only fail assigned or in-progress tasks")
            
            task.status = TaskStatus.FAILED
            task.completed_at = current_time
            task.failure_reason = failure_reason or "Task failed"
            task.completion_notes = notes
            
            # Update courier's active task count
            if courier.active_tasks_count > 0:
                courier.active_tasks_count -= 1
            
            # Update route progress
            if task.route_id:
                route = self.db.query(Route).filter(Route.id == task.route_id).first()
                if route:
                    route.failed_tasks += 1
            
        elif action == "skip":
            if task.status != TaskStatus.ASSIGNED:
                raise ValueError("Can only skip assigned tasks")
            
            task.status = TaskStatus.PENDING
            task.completion_notes = notes or "Task skipped by courier"
            
        else:
            raise ValueError(f"Invalid action: {action}")
        
        self.db.commit()
        self.db.refresh(task)
        
        # Publish task status change event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                f"task.{action}",
                {
                    "task_id": str(task.id),
                    "order_id": str(task.order_id),
                    "courier_id": str(task.courier_id),
                    "task_type": task.task_type,
                    "status": task.status,
                    "timestamp": current_time.isoformat(),
                    "location": {
                        "latitude": float(latitude) if latitude else None,
                        "longitude": float(longitude) if longitude else None
                    } if latitude and longitude else None
                },
                workspace_id=str(task.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish task action event: {e}")
        
        return task
