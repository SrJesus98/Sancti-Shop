"""Cart endpoints."""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.db.session import get_session
from app.schemas.cart import CartAddItemRequest, CartResponse, CartUpdateItemRequest
from app.services.cart import add_item_to_cart, clear_cart, get_cart, update_cart_item_quantity


router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
def get_cart_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Get authenticated user's cart."""
    return get_cart(session, current_user)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart_endpoint(
    payload: CartAddItemRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Add item to cart, incrementing quantity if already present."""
    return add_item_to_cart(session, current_user, payload.product_id, payload.quantity)


@router.put("/items/{cart_item_id}", response_model=CartResponse)
def update_cart_item_endpoint(
    cart_item_id: int,
    payload: CartUpdateItemRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Update cart item quantity (0 removes item)."""
    return update_cart_item_quantity(session, current_user, cart_item_id, payload.quantity)


@router.delete("", response_model=CartResponse)
def clear_cart_endpoint(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Clear current user's cart."""
    return clear_cart(session, current_user)
