"""Product service helpers."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.db.models import Product
from app.schemas.products import ProductCreateRequest, ProductUpdateRequest


def create_product(session: Session, payload: ProductCreateRequest) -> Product:
    """Create a product."""
    product = Product(**payload.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def get_product_or_404(session: Session, product_id: int) -> Product:
    """Get product by id or raise 404."""
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def update_product(session: Session, product_id: int, payload: ProductUpdateRequest) -> Product:
    """Update an existing product."""
    product = get_product_or_404(session, product_id)
    for field, value in payload.model_dump().items():
        setattr(product, field, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, product_id: int) -> None:
    """Delete an existing product."""
    product = get_product_or_404(session, product_id)
    session.delete(product)
    session.commit()


def list_public_products(
    session: Session,
    page: int,
    size: int,
    category: str | None = None,
) -> tuple[list[Product], int]:
    """List active/in-stock products with pagination and category filter."""
    query = session.query(Product).filter(Product.is_active.is_(True), Product.stock > 0)
    if category:
        query = query.filter(Product.category == category)

    total = query.count()
    items = (
        query.order_by(Product.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return items, total


def validate_available_for_purchase(product: Product) -> None:
    """Reusable stock/availability guard for future cart endpoints."""
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is inactive and cannot be added to cart",
        )
    if product.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product out of stock, cannot be added to cart",
        )
