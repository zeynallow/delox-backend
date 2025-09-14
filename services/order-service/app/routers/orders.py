"""
Order management router
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from shared.utils.database import get_session
from shared.utils.auth import get_current_user, CurrentUser
from shared.models.base import SuccessResponse
from shared.models.enums import OrderStatus, OrderPriority, PackageSize
from ..models import Order

router = APIRouter()


# Basic order schemas (simplified for now)
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID


class OrderCreate(BaseModel):
    """Order creation schema"""
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., min_length=1, max_length=20)
    customer_email: Optional[str] = None
    
    pickup_address: str = Field(..., min_length=1)
    pickup_contact_name: Optional[str] = None
    pickup_contact_phone: Optional[str] = None
    pickup_notes: Optional[str] = None
    
    delivery_address: str = Field(..., min_length=1)
    delivery_contact_name: Optional[str] = None
    delivery_contact_phone: Optional[str] = None
    delivery_notes: Optional[str] = None
    
    package_description: Optional[str] = None
    package_size: PackageSize = PackageSize.MEDIUM
    package_weight: Optional[Decimal] = None
    package_value: Optional[Decimal] = None
    package_quantity: int = 1
    
    priority: OrderPriority = OrderPriority.NORMAL
    scheduled_pickup_time: Optional[datetime] = None
    scheduled_delivery_time: Optional[datetime] = None
    
    delivery_fee: Optional[Decimal] = None
    cod_amount: Optional[Decimal] = None
    
    external_id: Optional[str] = None
    metadata: Optional[dict] = {}
    tags: Optional[List[str]] = []


class OrderResponse(BaseModel):
    """Order response schema"""
    id: UUID
    workspace_id: UUID
    order_number: str
    external_id: Optional[str] = None
    
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    
    pickup_address: str
    delivery_address: str
    
    package_description: Optional[str] = None
    package_size: PackageSize
    package_weight: Optional[Decimal] = None
    package_quantity: int
    
    status: OrderStatus
    priority: OrderPriority
    
    assigned_courier_id: Optional[UUID] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Create new order"""
    # Generate order number
    order_count = db.query(Order).filter(
        Order.workspace_id == current_user.workspace_id
    ).count()
    order_number = f"ORD-{order_count + 1:06d}"
    
    # Create order
    order = Order(
        workspace_id=current_user.workspace_id,
        order_number=order_number,
        external_id=order_data.external_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        customer_email=order_data.customer_email,
        pickup_address=order_data.pickup_address,
        pickup_contact_name=order_data.pickup_contact_name,
        pickup_contact_phone=order_data.pickup_contact_phone,
        pickup_notes=order_data.pickup_notes,
        delivery_address=order_data.delivery_address,
        delivery_contact_name=order_data.delivery_contact_name,
        delivery_contact_phone=order_data.delivery_contact_phone,
        delivery_notes=order_data.delivery_notes,
        package_description=order_data.package_description,
        package_size=order_data.package_size,
        package_weight=order_data.package_weight,
        package_value=order_data.package_value,
        package_quantity=order_data.package_quantity,
        priority=order_data.priority,
        scheduled_pickup_time=order_data.scheduled_pickup_time,
        scheduled_delivery_time=order_data.scheduled_delivery_time,
        delivery_fee=order_data.delivery_fee,
        cod_amount=order_data.cod_amount,
        metadata=order_data.metadata or {},
        tags=order_data.tags or []
    )
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return OrderResponse.from_orm(order)


@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    priority: Optional[OrderPriority] = Query(None),
    search: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """List orders in workspace"""
    query = db.query(Order).filter(
        Order.workspace_id == current_user.workspace_id,
        Order.is_deleted == False
    )
    
    # Apply filters
    if status:
        query = query.filter(Order.status == status)
    
    if priority:
        query = query.filter(Order.priority == priority)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            Order.order_number.ilike(search_term) |
            Order.customer_name.ilike(search_term) |
            Order.customer_phone.ilike(search_term)
        )
    
    # Apply pagination and ordering
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return [OrderResponse.from_orm(order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get order by ID"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.workspace_id == current_user.workspace_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return OrderResponse.from_orm(order)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Update order status"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.workspace_id == current_user.workspace_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update status
    old_status = order.status
    order.status = new_status
    
    # Update timestamps based on status
    if new_status == OrderStatus.PICKED_UP:
        order.picked_up_at = datetime.utcnow()
    elif new_status == OrderStatus.DELIVERED:
        order.delivered_at = datetime.utcnow()
    elif new_status == OrderStatus.FAILED:
        order.failed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    return OrderResponse.from_orm(order)


@router.delete("/{order_id}", response_model=SuccessResponse)
async def delete_order(
    order_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete order (soft delete)"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.workspace_id == current_user.workspace_id,
        Order.is_deleted == False
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Soft delete
    order.is_deleted = True
    order.deleted_at = datetime.utcnow()
    
    db.commit()
    
    return SuccessResponse(message="Order deleted successfully")
