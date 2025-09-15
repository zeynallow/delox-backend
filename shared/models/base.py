"""
Base models and mixins for all microservices
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from pydantic import BaseModel, Field


# SQLAlchemy Base
Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UUIDMixin:
    """Mixin for UUID primary key"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)


class WorkspaceMixin:
    """Mixin for workspace-based multi-tenancy"""
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


# Aliases for backward compatibility
WorkspaceEntity = WorkspaceMixin
TimestampEntity = TimestampMixin
SoftDeleteEntity = SoftDeleteMixin


class BaseEntity(Base, UUIDMixin, TimestampMixin, WorkspaceMixin, SoftDeleteMixin):
    """Base entity class with all common mixins"""
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


# Pydantic Base Models
class BaseSchema(BaseModel):
    """Base Pydantic schema"""
    class Config:
        from_attributes = True
        use_enum_values = True
        arbitrary_types_allowed = True


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields"""
    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID field"""
    id: UUID = Field(..., description="Unique identifier")


class WorkspaceSchema(BaseSchema):
    """Schema with workspace field"""
    workspace_id: UUID = Field(..., description="Workspace identifier")


class BaseEntitySchema(UUIDSchema, TimestampSchema, WorkspaceSchema):
    """Base entity schema with all common fields"""
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None


# Response Models
class SuccessResponse(BaseSchema):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseSchema):
    """Standard error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None


class PaginationMeta(BaseSchema):
    """Pagination metadata"""
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseSchema):
    """Paginated response wrapper"""
    data: list
    meta: PaginationMeta
