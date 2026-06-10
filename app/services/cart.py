"""Cart service helpers."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CartItem, Product, User
from app.schemas.cart import CartItemResponse, CartResponse
from app.services.products import validate_available_for_purchase


async def _get_product_or_404(session: AsyncSession, product_id: int) -> Product:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def _build_cart_response(session: AsyncSession, user: User) -> CartResponse:
    """Build cart response con selectinload para evitar N+1.
    
    Antes: 1 query cart_items + 1 query producto por cada item = 1+N queries
    Ahora: 1 query cart_items + 1 query productos (via selectinload) = 2 queries
    """
    result = await session.execute(
        select(CartItem)
        .where(CartItem.user_id == user.id)
        .options(selectinload(CartItem.product))
    )
    items = result.scalars().all()
    response_items: list[CartItemResponse] = []
    total = 0.0

    for item in items:
        product = item.product  # ya cargado, 0 queries extra
        if not product:
            continue
        subtotal = float(product.price) * item.quantity
        total += subtotal
        response_items.append(
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price=float(product.price),
                subtotal=subtotal,
            )
        )

    return CartResponse(items=response_items, total=total)


async def get_cart(session: AsyncSession, user: User) -> CartResponse:
    """Return cart for authenticated user."""
    return await _build_cart_response(session, user)


async def add_item_to_cart(session: AsyncSession, user: User, product_id: int, quantity: int) -> CartResponse:
    """Add a product to cart or increment existing item."""
    product = await _get_product_or_404(session, product_id)
    validate_available_for_purchase(product)

    result = await session.execute(
        select(CartItem).where(
            CartItem.user_id == user.id,
            CartItem.product_id == product_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.quantity += quantity
        session.add(existing)
    else:
        session.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))

    await session.commit()
    return await _build_cart_response(session, user)


async def update_cart_item_quantity(
    session: AsyncSession, user: User, cart_item_id: int, quantity: int
) -> CartResponse:
    """Update quantity for a cart item, removing it when quantity is 0."""
    result = await session.execute(
        select(CartItem).where(
            CartItem.id == cart_item_id,
            CartItem.user_id == user.id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    if quantity == 0:
        await session.delete(item)
    else:
        item.quantity = quantity
        session.add(item)

    await session.commit()
    return await _build_cart_response(session, user)


async def clear_cart(session: AsyncSession, user: User) -> CartResponse:
    """Clear all cart items for user."""
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id)
    )
    items = result.scalars().all()
    for item in items:
        await session.delete(item)
    await session.commit()
    return CartResponse(items=[], total=0.0)