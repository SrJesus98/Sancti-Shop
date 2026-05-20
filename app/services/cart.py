"""Cart service helpers."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.db.models import CartItem, Product, User
from app.schemas.cart import CartItemResponse, CartResponse
from app.services.products import validate_available_for_purchase


def _get_product_or_404(session: Session, product_id: int) -> Product:
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def _build_cart_response(session: Session, user: User) -> CartResponse:
    items = session.query(CartItem).filter(CartItem.user_id == user.id).all()
    response_items: list[CartItemResponse] = []
    total = 0.0

    for item in items:
        product = session.query(Product).filter(Product.id == item.product_id).first()
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


def get_cart(session: Session, user: User) -> CartResponse:
    """Return cart for authenticated user."""
    return _build_cart_response(session, user)


def add_item_to_cart(session: Session, user: User, product_id: int, quantity: int) -> CartResponse:
    """Add a product to cart or increment existing item."""
    product = _get_product_or_404(session, product_id)
    validate_available_for_purchase(product)

    existing = (
        session.query(CartItem)
        .filter(CartItem.user_id == user.id, CartItem.product_id == product_id)
        .first()
    )

    if existing:
        existing.quantity += quantity
        session.add(existing)
    else:
        session.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))

    session.commit()
    return _build_cart_response(session, user)


def update_cart_item_quantity(session: Session, user: User, cart_item_id: int, quantity: int) -> CartResponse:
    """Update quantity for a cart item, removing it when quantity is 0."""
    item = (
        session.query(CartItem)
        .filter(CartItem.id == cart_item_id, CartItem.user_id == user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    if quantity == 0:
        session.delete(item)
    else:
        item.quantity = quantity
        session.add(item)

    session.commit()
    return _build_cart_response(session, user)


def clear_cart(session: Session, user: User) -> CartResponse:
    """Clear all cart items for user."""
    items = session.query(CartItem).filter(CartItem.user_id == user.id).all()
    for item in items:
        session.delete(item)
    session.commit()
    return CartResponse(items=[], total=0.0)
