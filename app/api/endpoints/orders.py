"""Order endpoints — ASYNC."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_scopes
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.orders import AdminOrderStatusUpdateRequest, OrderResponse
from app.services.orders import (
    admin_get_all_orders,
    admin_update_order_status,
    create_order_from_cart,
    get_order_detail,
    get_user_orders,
    build_order_response
)


router = APIRouter(prefix="/orders", tags=["orders"])
ADMIN_ORDER_SCOPES = ["admin:orders"]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Create order from cart."""
    order = await create_order_from_cart(session, current_user)
    return build_order_response(order)


@router.get("", response_model=list[OrderResponse])
async def list_user_orders(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """List current user's orders."""
    return await get_user_orders(session, current_user.id)


@router.get("/admin", response_model=list[OrderResponse])
async def admin_list_orders(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_ORDER_SCOPES)),
) -> list[OrderResponse]:
    """Admin: list all orders."""
    return await admin_get_all_orders(session)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Get order detail."""
    return await get_order_detail(session, order_id, current_user.id)





@router.patch("/admin/{order_id}/status", response_model=OrderResponse)
async def admin_update_status(
    order_id: int,
    payload: AdminOrderStatusUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_ORDER_SCOPES)),
) -> OrderResponse:
    """Admin: update order status."""
    return await admin_update_order_status(session, order_id, payload)