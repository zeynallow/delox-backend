"""
Workspace Service Business Logic
"""
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from shared.utils.messaging import get_event_publisher, EventTypes
from shared.models.enums import WorkspaceStatus, UserRole, UserStatus
from ..models import Workspace, User
from ..schemas import WorkspaceCreate, WorkspaceUpdate, WorkspaceStats


class WorkspaceService:
    """Workspace service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_workspace(self, workspace_data: WorkspaceCreate) -> Workspace:
        """Create new workspace"""
        # Generate slug if not provided
        if not workspace_data.slug:
            slug = self._generate_slug(workspace_data.name)
        else:
            slug = workspace_data.slug
        
        # Check if slug is unique
        existing = self.db.query(Workspace).filter(
            Workspace.slug == slug,
            Workspace.is_deleted == False
        ).first()
        
        if existing:
            raise ValueError(f"Workspace with slug '{slug}' already exists")
        
        # Generate API key
        api_key = self._generate_api_key()
        
        # Create workspace
        workspace = Workspace(
            name=workspace_data.name,
            slug=slug,
            description=workspace_data.description,
            primary_color=workspace_data.primary_color,
            status=WorkspaceStatus.TRIAL,
            trial_ends_at=datetime.utcnow() + timedelta(days=14),  # 14-day trial
            api_key=api_key,
            settings={
                "notifications": {
                    "email_enabled": True,
                    "sms_enabled": False,
                    "push_enabled": True
                },
                "delivery": {
                    "auto_assign_couriers": True,
                    "route_optimization": True,
                    "delivery_window_hours": 8
                },
                "branding": {
                    "show_logo": True,
                    "custom_domain": None
                }
            }
        )
        
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.WORKSPACE_CREATED,
                {
                    "workspace_id": str(workspace.id),
                    "name": workspace.name,
                    "slug": workspace.slug,
                    "status": workspace.status
                },
                workspace_id=str(workspace.id)
            )
        except Exception as e:
            print(f"Failed to publish workspace created event: {e}")
        
        return workspace
    
    def get_workspace_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID"""
        return self.db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == False
        ).first()
    
    def get_workspace_by_slug(self, slug: str) -> Optional[Workspace]:
        """Get workspace by slug"""
        return self.db.query(Workspace).filter(
            Workspace.slug == slug,
            Workspace.is_deleted == False
        ).first()
    
    def update_workspace(self, workspace_id: str, workspace_data: WorkspaceUpdate) -> Workspace:
        """Update workspace"""
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Update fields
        update_data = workspace_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(workspace, field):
                setattr(workspace, field, value)
        
        self.db.commit()
        self.db.refresh(workspace)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.WORKSPACE_UPDATED,
                {
                    "workspace_id": str(workspace.id),
                    "updated_fields": list(update_data.keys())
                },
                workspace_id=str(workspace.id)
            )
        except Exception as e:
            print(f"Failed to publish workspace updated event: {e}")
        
        return workspace
    
    def delete_workspace(self, workspace_id: str):
        """Soft delete workspace"""
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Soft delete workspace and all users
        workspace.is_deleted = True
        workspace.deleted_at = datetime.utcnow()
        
        # Soft delete all users in workspace
        self.db.query(User).filter(
            User.workspace_id == workspace_id
        ).update({
            "is_deleted": True,
            "deleted_at": datetime.utcnow()
        })
        
        self.db.commit()
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.WORKSPACE_DELETED,
                {
                    "workspace_id": str(workspace.id),
                    "name": workspace.name
                },
                workspace_id=str(workspace.id)
            )
        except Exception as e:
            print(f"Failed to publish workspace deleted event: {e}")
    
    def get_workspace_stats(self, workspace_id: str) -> WorkspaceStats:
        """Get workspace statistics"""
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Count users
        total_users = self.db.query(func.count(User.id)).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False
        ).scalar()
        
        active_users = self.db.query(func.count(User.id)).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False,
            User.is_active == True
        ).scalar()
        
        # Count couriers
        total_couriers = self.db.query(func.count(User.id)).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False,
            User.role == UserRole.COURIER
        ).scalar()
        
        active_couriers = self.db.query(func.count(User.id)).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False,
            User.role == UserRole.COURIER,
            User.is_active == True
        ).scalar()
        
        # TODO: Get order stats from order service
        orders_this_month = 0  # Placeholder
        
        return WorkspaceStats(
            total_users=total_users,
            active_users=active_users,
            total_couriers=total_couriers,
            active_couriers=active_couriers,
            orders_this_month=orders_this_month,
            orders_limit=workspace.max_orders_per_month
        )
    
    def regenerate_api_key(self, workspace_id: str) -> str:
        """Regenerate workspace API key"""
        workspace = self.get_workspace_by_id(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")
        
        new_api_key = self._generate_api_key()
        workspace.api_key = new_api_key
        
        self.db.commit()
        
        return new_api_key
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from workspace name"""
        # Convert to lowercase and replace spaces with hyphens
        slug = name.lower().replace(" ", "-")
        
        # Remove special characters
        allowed_chars = string.ascii_lowercase + string.digits + "-"
        slug = "".join(c for c in slug if c in allowed_chars)
        
        # Remove consecutive hyphens
        while "--" in slug:
            slug = slug.replace("--", "-")
        
        # Remove leading/trailing hyphens
        slug = slug.strip("-")
        
        # Ensure minimum length
        if len(slug) < 3:
            slug = f"workspace-{secrets.token_hex(4)}"
        
        # Check uniqueness and add suffix if needed
        original_slug = slug
        counter = 1
        while self.db.query(Workspace).filter(
            Workspace.slug == slug,
            Workspace.is_deleted == False
        ).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"dlx_{''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))}"
