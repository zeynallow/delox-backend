"""
User Service Business Logic
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from shared.utils.messaging import get_event_publisher, EventTypes
from shared.models.enums import UserRole, UserStatus
from ..models import User, Workspace, WorkspaceInvitation
from ..schemas import UserCreate, UserUpdate, InvitationCreate, InvitationAccept


class UserService:
    """User service business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, workspace_id: str, user_data: UserCreate) -> User:
        """Create new user in workspace"""
        # Check if workspace exists
        workspace = self.db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == False
        ).first()
        
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Check if user already exists in workspace
        existing_user = self.db.query(User).filter(
            User.email == user_data.email,
            User.workspace_id == workspace_id,
            User.is_deleted == False
        ).first()
        
        if existing_user:
            raise ValueError("User with this email already exists in workspace")
        
        # Check workspace user limits
        current_user_count = self.db.query(func.count(User.id)).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False
        ).scalar()
        
        if current_user_count >= workspace.max_users:
            raise ValueError("Workspace user limit reached")
        
        # Create user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            workspace_id=workspace_id,
            role=user_data.role,
            permissions=user_data.permissions or [],
            status=UserStatus.ACTIVE,
            timezone=user_data.timezone,
            language=user_data.language,
            notification_preferences={
                "email": True,
                "sms": False,
                "push": True,
                "order_updates": True,
                "delivery_notifications": True
            },
            courier_license=user_data.courier_license,
            vehicle_type=user_data.vehicle_type,
            vehicle_plate=user_data.vehicle_plate,
            max_delivery_distance=user_data.max_delivery_distance
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.USER_CREATED,
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "workspace_id": str(user.workspace_id)
                },
                workspace_id=str(user.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish user created event: {e}")
        
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(
            User.id == user_id,
            User.is_deleted == False
        ).first()
    
    def get_user_by_id_and_workspace(self, user_id: str, workspace_id: str) -> Optional[User]:
        """Get user by ID and workspace"""
        return self.db.query(User).filter(
            User.id == user_id,
            User.workspace_id == workspace_id,
            User.is_deleted == False
        ).first()
    
    def get_user_by_email_and_workspace(self, email: str, workspace_id: str) -> Optional[User]:
        """Get user by email and workspace"""
        return self.db.query(User).filter(
            User.email == email,
            User.workspace_id == workspace_id,
            User.is_deleted == False
        ).first()
    
    def list_users(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        role: Optional[UserRole] = None
    ) -> Tuple[List[User], int]:
        """List users in workspace with filtering"""
        query = self.db.query(User).filter(
            User.workspace_id == workspace_id,
            User.is_deleted == False
        )
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Apply role filter
        if role:
            query = query.filter(User.role == role)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        users = query.offset(skip).limit(limit).all()
        
        return users, total
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.USER_UPDATED,
                {
                    "user_id": str(user.id),
                    "updated_fields": list(update_data.keys()),
                    "workspace_id": str(user.workspace_id)
                },
                workspace_id=str(user.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish user updated event: {e}")
        
        return user
    
    def delete_user(self, user_id: str):
        """Soft delete user"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        user.is_deleted = True
        user.deleted_at = datetime.utcnow()
        
        self.db.commit()
        
        # Publish event
        try:
            event_publisher = get_event_publisher()
            event_publisher.publish_event(
                EventTypes.USER_DELETED,
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "workspace_id": str(user.workspace_id)
                },
                workspace_id=str(user.workspace_id)
            )
        except Exception as e:
            print(f"Failed to publish user deleted event: {e}")
    
    def create_invitation(
        self,
        workspace_id: str,
        invited_by: str,
        invitation_data: InvitationCreate
    ) -> WorkspaceInvitation:
        """Create workspace invitation"""
        # Check if workspace exists
        workspace = self.db.query(Workspace).filter(
            Workspace.id == workspace_id,
            Workspace.is_deleted == False
        ).first()
        
        if not workspace:
            raise ValueError("Workspace not found")
        
        # Check if user already exists
        existing_user = self.get_user_by_email_and_workspace(
            invitation_data.email, workspace_id
        )
        if existing_user:
            raise ValueError("User already exists in workspace")
        
        # Check if invitation already exists
        existing_invitation = self.db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.workspace_id == workspace_id,
            WorkspaceInvitation.email == invitation_data.email,
            WorkspaceInvitation.is_accepted == False,
            WorkspaceInvitation.is_revoked == False
        ).first()
        
        if existing_invitation:
            raise ValueError("Invitation already sent to this email")
        
        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)
        
        # Create invitation
        invitation = WorkspaceInvitation(
            workspace_id=workspace_id,
            email=invitation_data.email,
            role=invitation_data.role,
            invited_by=invited_by,
            invitation_token=invitation_token,
            expires_at=datetime.utcnow() + timedelta(days=7)  # 7 days to accept
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        # TODO: Send invitation email
        
        return invitation
    
    def list_invitations(
        self,
        workspace_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[WorkspaceInvitation], int]:
        """List workspace invitations"""
        query = self.db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.workspace_id == workspace_id
        ).order_by(WorkspaceInvitation.created_at.desc())
        
        total = query.count()
        invitations = query.offset(skip).limit(limit).all()
        
        return invitations, total
    
    def accept_invitation(self, acceptance_data: InvitationAccept) -> User:
        """Accept workspace invitation"""
        # Find invitation
        invitation = self.db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.invitation_token == acceptance_data.invitation_token,
            WorkspaceInvitation.is_accepted == False,
            WorkspaceInvitation.is_revoked == False,
            WorkspaceInvitation.expires_at > datetime.utcnow()
        ).first()
        
        if not invitation:
            raise ValueError("Invalid or expired invitation")
        
        # Check if user already exists
        existing_user = self.get_user_by_email_and_workspace(
            invitation.email, str(invitation.workspace_id)
        )
        if existing_user:
            raise ValueError("User already exists in workspace")
        
        # Create user
        user_data = UserCreate(
            email=invitation.email,
            first_name=acceptance_data.first_name,
            last_name=acceptance_data.last_name,
            phone=acceptance_data.phone,
            role=invitation.role
        )
        
        user = self.create_user(str(invitation.workspace_id), user_data)
        
        # Mark invitation as accepted
        invitation.is_accepted = True
        invitation.accepted_at = datetime.utcnow()
        
        self.db.commit()
        
        return user
    
    def revoke_invitation(self, invitation_id: str, workspace_id: str):
        """Revoke workspace invitation"""
        invitation = self.db.query(WorkspaceInvitation).filter(
            WorkspaceInvitation.id == invitation_id,
            WorkspaceInvitation.workspace_id == workspace_id
        ).first()
        
        if not invitation:
            raise ValueError("Invitation not found")
        
        if invitation.is_accepted:
            raise ValueError("Cannot revoke accepted invitation")
        
        invitation.is_revoked = True
        invitation.revoked_at = datetime.utcnow()
        
        self.db.commit()
