"""Product endpoints for admin CRUD and public listing."""

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.api.dependencies.auth import require_scopes
from app.core.limiter import limiter
from app.db.models import User
from app.db.session import get_session
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
def get_product(
    product_id: int,
    session: Session = Depends(get_session),
) -> ProductResponse:
    """Public endpoint to get a single product by ID."""
    from app.services.products import get_product_or_404
    product = get_product_or_404(session, product_id)
    return ProductResponse.model_validate(product)


@router.get("", response_model=PublicProductListResponse)
@limiter.limit("100/minute")
def list_products(
    request: Request,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    category: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    order: str = Query(default="asc"),
    session: Session = Depends(get_session),
) -> PublicProductListResponse:
    """Public products listing with pagination, category filter, and sorting."""
    result = get_products(session, page=page, size=size, category=category, sort=sort, order=order)
    return PublicProductListResponse(**result)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_endpoint(
    payload: ProductCreateRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> ProductResponse:
    """Admin-only product creation."""
    product = create_product(session, payload)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product_endpoint(
    product_id: int,
    payload: ProductUpdateRequest,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> ProductResponse:
    """Admin-only product update."""
    product = update_product(session, product_id, payload)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product_endpoint(
    product_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_scopes(ADMIN_PRODUCT_SCOPES)),
) -> Response:
    """Admin-only product deletion."""
    delete_product(session, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
