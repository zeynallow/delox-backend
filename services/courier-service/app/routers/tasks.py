"""
Task management router
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, require_manager, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import TaskStatus, TaskType
from ..schemas import (
    TaskCreate, TaskUpdate, TaskResponse, TaskAction
)
from ..services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[TaskStatus] = Query(None),
    task_type: Optional[TaskType] = Query(None),
    courier_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List tasks in workspace"""
    task_service = TaskService(db)
    
    tasks, total = task_service.list_tasks(
        workspace_id=str(current_user.workspace_id),
        skip=skip,
        limit=limit,
        status=status,
        task_type=task_type,
        courier_id=courier_id
    )
    
    return [TaskResponse.from_orm(task) for task in tasks]


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Create new task (manager/admin only)"""
    task_service = TaskService(db)
    
    try:
        task = task_service.create_task(
            workspace_id=str(current_user.workspace_id),
            task_data=task_data
        )
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get task by ID"""
    task_service = TaskService(db)
    
    task = task_service.get_task_by_id_and_workspace(
        task_id=task_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return TaskResponse.from_orm(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update task"""
    task_service = TaskService(db)
    
    # Check if user can update this task
    task = task_service.get_task_by_id_and_workspace(
        task_id=task_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Couriers can only update their own tasks
    if current_user.is_courier() and str(task.courier_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own tasks"
        )
    
    try:
        updated_task = task_service.update_task(task_id, task_data)
        return TaskResponse.from_orm(updated_task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{task_id}", response_model=SuccessResponse)
async def delete_task(
    task_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Delete task (manager/admin only)"""
    task_service = TaskService(db)
    
    try:
        task_service.delete_task(task_id, str(current_user.workspace_id))
        return SuccessResponse(message="Task deleted successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Task assignment
@router.put("/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: str,
    courier_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Assign task to courier (manager/admin only)"""
    task_service = TaskService(db)
    
    try:
        task = task_service.assign_task_to_courier(task_id, courier_id)
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{task_id}/unassign", response_model=TaskResponse)
async def unassign_task(
    task_id: str,
    current_user: CurrentUser = Depends(require_manager()),
    db: Session = Depends(get_session)
):
    """Unassign task from courier (manager/admin only)"""
    task_service = TaskService(db)
    
    try:
        task = task_service.unassign_task(task_id)
        return TaskResponse.from_orm(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Courier app endpoints
@router.get("/assigned/me", response_model=List[TaskResponse])
async def get_assigned_tasks(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get tasks assigned to current courier (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access assigned tasks"
        )
    
    task_service = TaskService(db)
    
    try:
        tasks = task_service.get_assigned_tasks_for_courier(str(current_user.user_id))
        return [TaskResponse.from_orm(task) for task in tasks]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{task_id}/action", response_model=TaskResponse)
async def perform_task_action(
    task_id: str,
    action_data: TaskAction,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Perform action on task (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can perform task actions"
        )
    
    task_service = TaskService(db)
    
    # Check if task belongs to current courier
    task = task_service.get_task_by_id_and_workspace(
        task_id=task_id,
        workspace_id=str(current_user.workspace_id)
    )
    
    if not task or str(task.courier_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or not assigned to you"
        )
    
    try:
        updated_task = task_service.perform_task_action(
            task_id=task_id,
            action=action_data.action,
            courier_id=str(current_user.user_id),
            latitude=action_data.latitude,
            longitude=action_data.longitude,
            notes=action_data.notes,
            photo_url=action_data.photo_url,
            signature_url=action_data.signature_url,
            failure_reason=action_data.failure_reason
        )
        return TaskResponse.from_orm(updated_task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/pending/me", response_model=List[TaskResponse])
async def get_pending_tasks(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get pending tasks for current courier (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access pending tasks"
        )
    
    task_service = TaskService(db)
    
    try:
        tasks = task_service.get_pending_tasks_for_courier(str(current_user.user_id))
        return [TaskResponse.from_orm(task) for task in tasks]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/next/me", response_model=Optional[TaskResponse])
async def get_next_task(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get next task for current courier (for courier app)"""
    if not current_user.is_courier():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only couriers can access next task"
        )
    
    task_service = TaskService(db)
    
    try:
        task = task_service.get_next_task_for_courier(str(current_user.user_id))
        return TaskResponse.from_orm(task) if task else None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
