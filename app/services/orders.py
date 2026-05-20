"""Order and checkout service helpers."""

from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session

from app.db.models import CartItem, Order, OrderItem, Product, User
from app.schemas.orders import OrderItemResponse, OrderResponse
from app.services.products import validate_available_for_purchase

ADMIN_ALLOWED_TRANSITIONS = {
    "Pagada": {"Lista"},
    "Lista": {"Entregada"},
}


def build_order_response(session: Session, order: Order) -> OrderResponse:
    items = session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        total=float(order.total),
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "",
                quantity=item.quantity,
                price=float(item.price),
            )
            for item in items
        ],
    )


def checkout_from_cart(session: Session, user: User) -> OrderResponse:
    """Create order from cart, discount stock, and clear cart."""
    cart_items = session.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total = 0.0
    products_by_id: dict[int, Product] = {}
    for item in cart_items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        validate_available_for_purchase(product)
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {product.id}",
            )
        products_by_id[product.id] = product
        total += float(product.price) * item.quantity

    order = Order(user_id=user.id, status="En proceso", total=total)
    session.add(order)
    session.flush()

    for item in cart_items:
        product = products_by_id[item.product_id]
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=float(product.price),
        )
        session.add(order_item)
        product.stock -= item.quantity
        session.add(product)
        session.delete(item)

    session.commit()
    session.refresh(order)
    return build_order_response(session, order)


def list_orders_for_user(session: Session, user: User) -> list[OrderResponse]:
    """Return orders for current user."""
    orders = (
        session.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [build_order_response(session, order) for order in orders]


def mark_order_as_paid(session: Session, user: User, order_id: int) -> OrderResponse:
    """Transition order from En proceso to Pagada for owner."""
    order = session.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != "En proceso":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid status transition")

    order.status = "Pagada"
    order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return build_order_response(session, order)


def admin_update_order_status(session: Session, order_id: int, new_status: str) -> OrderResponse:
    """Admin-only status transitions: Pagada->Lista->Entregada."""
    order = session.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    allowed_next = ADMIN_ALLOWED_TRANSITIONS.get(order.status, set())
    if new_status not in allowed_next:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid status transition")

    order.status = new_status
    order.updated_at = datetime.utcnow()
    session.add(order)
    session.commit()
    session.refresh(order)
    return build_order_response(session, order)
