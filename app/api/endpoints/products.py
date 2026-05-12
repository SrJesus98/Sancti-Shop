"""Product endpoints for admin CRUD and public listing."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.api.dependencies.auth import require_scopes
from app.db.models import User
from app.db.session import get_session
from app.schemas.products import (
    ProductCreateRequest,
    ProductResponse,
    ProductUpdateRequest,
    PublicProductListResponse,
)
from app.services.products import create_product, delete_product, list_public_products, update_product


router = APIRouter(prefix="/products", tags=["products"])
ADMIN_PRODUCT_SCOPES = ["admin:products"]


@router.get("", response_model=PublicProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    category: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> PublicProductListResponse:
    """Public products listing with pagination and category filter."""
    items, total = list_public_products(session, page=page, size=size, category=category)
    total_pages = (total + size - 1) // size if total else 0
    return PublicProductListResponse(
        items=[ProductResponse.model_validate(item) for item in items],
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
    )


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
