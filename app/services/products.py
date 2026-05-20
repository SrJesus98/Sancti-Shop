"""Product service helpers."""

from fastapi import HTTPException, status
from sqlmodel import Session

from app.db.models import Product
from app.schemas.products import ProductCreateRequest, ProductResponse, ProductUpdateRequest


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


def get_products(session, page=1, size=10, category=None, sort=None, order="asc"):
    query = session.query(Product).filter(Product.is_active == True, Product.stock > 0)

    if category:
        query = query.filter(Product.category == category)

    allowed_sort = {
        "name": Product.name,
        "price": Product.price,
        "stock": Product.stock,
        "created_at": Product.created_at,
        "category": Product.category,
    }

    if sort and sort in allowed_sort:
        col = allowed_sort[sort]
        query = query.order_by(col.desc() if order == "desc" else col.asc())
    else:
        query = query.order_by(Product.created_at.desc())

    total = query.count()
    items = query.offset((page-1)*size).limit(size).all()
    total_pages = max(1, (total + size - 1) // size)

    return {
        "items": [ProductResponse.model_validate(p) for p in items],
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }


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
