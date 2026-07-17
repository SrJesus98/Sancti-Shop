"""Order service helpers — ASYNC."""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import CartItem, Order, OrderItem, Product, User
from app.schemas.orders import AdminOrderStatusUpdateRequest, OrderItemResponse, OrderResponse


async def _get_order_or_404(session: AsyncSession, order_id: int, user_id: int | None = None) -> Order:
    stmt = select(Order).where(Order.id == order_id)
    if user_id:
        stmt = stmt.where(Order.user_id == user_id)
    stmt = stmt.options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user)
        )
    result = await session.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orden no encontrada")
    return order


def build_order_response(order: Order) -> OrderResponse:
    """Build OrderResponse from Order model (sync, no DB calls)."""
    items = [
        OrderItemResponse(
            id=oi.id,
            product_id=oi.product_id,
            product_name=oi.product.name if oi.product else "Producto eliminado",
            quantity=oi.quantity,
            price=oi.price,
            subtotal=oi.quantity * oi.price,
        )
        for oi in (order.items or [])
    ]
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        user_email=order.user.email if order.user else None,
        status=order.status,
        total=order.total,
        items=items,
        created_at=order.created_at.isoformat() if order.created_at else None,
        updated_at=order.updated_at.isoformat() if order.updated_at else None,
    )


async def create_order_from_cart(session: AsyncSession, user: User) -> Order:
    """Create an order from the user's cart items."""
    result = await session.execute(
        select(CartItem).where(CartItem.user_id == user.id)
        .options(selectinload(CartItem.product))
    )
    cart_items = result.scalars().all()

    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    order_items = []
    total = 0.0
    for ci in cart_items:
        product = ci.product
        if not product or not product.is_active:
            continue
        quantity = ci.quantity if ci.quantity <= product.stock else product.stock
        price = float(product.price)
        subtotal = price * quantity
        total += subtotal
        order_items.append(
            OrderItem(
                product_id=product.id,
                quantity=quantity,
                price=price,
            )
        )

    order = Order(
        user_id=user.id,
        status="En proceso",
        total=total,
        items=order_items,
    )
    session.add(order)

    # Clear cart
    for ci in cart_items:
        await session.delete(ci)

    await session.commit()
    stmt = select(Order).where(Order.id == order.id).options(
    selectinload(Order.items).selectinload(OrderItem.product),
    selectinload(Order.user)
    )
    result = await session.execute(stmt)
    order = result.scalar_one()
    return order


async def get_user_orders(session: AsyncSession, user_id: int) -> list[OrderResponse]:
    """Get all orders for a user."""
    result = await session.execute(
        select(Order).where(Order.user_id == user_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user)
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [build_order_response(o) for o in orders]


async def get_order_detail(session: AsyncSession, order_id: int, user_id: int) -> OrderResponse:
    """Get single order detail for a user."""
    order = await _get_order_or_404(session, order_id, user_id)
    return build_order_response(order)


async def admin_get_all_orders(session: AsyncSession) -> list[OrderResponse]:
    """Admin: get all orders."""
    result = await session.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user)
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    response = []
    for o in orders:
        response.append(build_order_response(o))
    return response


async def admin_update_order_status(
    session: AsyncSession, order_id: int, payload: AdminOrderStatusUpdateRequest
) -> OrderResponse:
    """Admin: update order status."""
    order = await _get_order_or_404(session, order_id)
    order.status = payload.status
    order.updated_at = payload.updated_at
    session.add(order)
    await session.commit()
    return build_order_response(order)