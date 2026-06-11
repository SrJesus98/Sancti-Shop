"""Cart endpoints — ASYNC."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.cart import CartAddItemRequest, CartResponse, CartUpdateItemRequest
from app.services.cart import add_item_to_cart, clear_cart, get_cart, update_cart_item_quantity,remove_cart_item


router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
async def get_cart_endpoint(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Get authenticated user's cart."""
    return await get_cart(session, current_user)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart_endpoint(
    payload: CartAddItemRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Add item to cart, incrementing quantity if already present."""
    return await add_item_to_cart(session, current_user, payload.product_id, payload.quantity)


@router.put("/items/{cart_item_id}", response_model=CartResponse)
async def update_cart_item_endpoint(
    cart_item_id: int,
    payload: CartUpdateItemRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Update cart item quantity (0 removes item)."""
    return await update_cart_item_quantity(session, current_user, cart_item_id, payload.quantity)


@router.delete("", response_model=CartResponse)
async def clear_cart_endpoint(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
) -> CartResponse:
    """Clear current user's cart."""
    return await clear_cart(session, current_user)

@router.delete("/items/{cart_item_id}", response_model=CartResponse)
async def delete_cart_item(
    cart_item_id: int,
    session:AsyncSession=Depends(get_async_session),
    user:User=Depends(get_current_user)):

    await remove_cart_item(session,user,cart_item_id)
    return await get_cart(session,user)