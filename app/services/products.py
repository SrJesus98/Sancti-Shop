"""Product service helpers — ASYNC version."""

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Product
from app.schemas.products import ProductCreateRequest, ProductResponse, ProductUpdateRequest


async def create_product(session: AsyncSession, payload: ProductCreateRequest) -> Product:
    """Create a product."""
    product = Product(**payload.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def get_product_or_404(session: AsyncSession, product_id: int) -> Product:
    """Get product by id or raise 404."""
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def update_product(session: AsyncSession, product_id: int, payload: ProductUpdateRequest) -> Product:
    """Update an existing product."""
    product = await get_product_or_404(session, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product_id: int) -> None:
    """Delete an existing product."""
    product = await get_product_or_404(session, product_id)
    await session.delete(product)
    await session.commit()


async def get_products(
    session: AsyncSession,
    page: int = 1,
    size: int = 10,
    category: str | None = None,
    sort: str | None = None,
    order: str = "asc",
) -> dict:
    """List products with pagination, filter, and sorting (async)."""
    # Build base query
    stmt = select(Product).where(Product.is_active == True, Product.stock > 0)

    if category:
        stmt = stmt.where(Product.category == category)

    allowed_sort = {
        "name": Product.name,
        "price": Product.price,
        "stock": Product.stock,
        "created_at": Product.created_at,
        "category": Product.category,
    }

    if sort and sort in allowed_sort:
        col = allowed_sort[sort]
        stmt = stmt.order_by(col.desc() if order == "desc" else col.asc())
    else:
        stmt = stmt.order_by(Product.created_at.desc())

    # Count total (async)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await session.execute(count_stmt)
    total = result.scalar() or 0

    # Paginate
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await session.execute(stmt)
    items = result.scalars().all()

    total_pages = max(1, (total + size - 1) // size)

    return {
        "items": [ProductResponse.model_validate(p) for p in items],
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
    }


async def list_public_products(
    session: AsyncSession,
    page: int,
    size: int,
    category: str | None = None,
) -> tuple[list[Product], int]:
    """List active/in-stock products with pagination and category filter (async)."""
    stmt = select(Product).where(
        Product.is_active.is_(True),
        Product.stock > 0,
    )
    if category:
        stmt = stmt.where(Product.category == category)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    result = await session.execute(count_stmt)
    total = result.scalar() or 0

    # Paginate
    stmt = stmt.order_by(Product.created_at.desc())
    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await session.execute(stmt)
    items = result.scalars().all()

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
