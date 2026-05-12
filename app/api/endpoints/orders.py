"""Order endpoints for checkout and status transitions."""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user, require_scopes
from app.db.models import User
from app.db.session import get_session
from app.schemas.orders import AdminOrderStatusUpdateRequest, OrderResponse
from app.services.orders import (
    admin_update_order_status,
    checkout_from_cart,
    list_orders_for_user,
    mark_order_as_paid,
)


router = APIRouter(prefix="/orders", tags=["orders"])
ADMIN_ORDER_SCOPES = ["admin:orders"]


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """Checkout current cart into a new order."""
    return checkout_from_cart(session, current_user)


@router.get("", response_model=list[OrderResponse])
def list_orders_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[OrderResponse]:
    """Return authenticated user's order history."""
    return list_orders_for_user(session, current_user)


@router.patch("/{order_id}/pay", response_model=OrderResponse)
def pay_order_endpoint(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> OrderResponse:
    """User-side payment flow transition En proceso -> Pagada."""
    return mark_order_as_paid(session, current_user, order_id)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def admin_update_status_endpoint(
    order_id: int,
    payload: AdminOrderStatusUpdateRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_ORDER_SCOPES)),
) -> OrderResponse:
    """Admin-only transitions Pagada->Lista->Entregada."""
    return admin_update_order_status(session, order_id, payload.status)
