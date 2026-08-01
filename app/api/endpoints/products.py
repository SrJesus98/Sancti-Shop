"""Product endpoints for admin CRUD and public listing — ASYNC."""

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_scopes
from app.core.limiter import limiter
from app.db.models import User
from app.db.session import get_async_session
from app.schemas.products import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
    PublicProductListResponse,
)
from app.services.products import create_product, delete_product, get_products, update_product


router = APIRouter(prefix="/products", tags=["products"])
ADMIN_PRODUCT_SCOPES = ["admin:products"]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> ProductResponse:
    """Public endpoint to get a single product by ID."""
    from app.services.products import get_product_or_404
    product = await get_product_or_404(session, product_id)
    return ProductResponse.model_validate(product)


@router.get("", response_model=PublicProductListResponse)
@limiter.limit("100/minute")
async def list_products(
    request: Request,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=1000),
    category: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    order: str = Query(default="asc"),
    session: AsyncSession = Depends(get_async_session),
) -> PublicProductListResponse:
    """Public products listing with pagination, category filter, and sorting."""
    result = await get_products(session, page=page, size=size, category=category, sort=sort, order=order)
    return PublicProductListResponse(**result)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    payload: ProductCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> ProductResponse:
    """Admin-only product creation."""
    product = await create_product(session, payload)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(
    product_id: int,
    payload: ProductUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> ProductResponse:
    """Admin-only product update."""
    product = await update_product(session, product_id, payload)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_endpoint(
    product_id: int,
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> Response:
    """Admin-only product deletion."""
    await delete_product(session, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
