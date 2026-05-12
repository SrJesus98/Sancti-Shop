"""Product request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Shared product fields."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)
    stock: int = Field(ge=0)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None
    is_active: bool = True


class ProductCreateRequest(ProductBase):
    """Payload for admin product creation."""


class ProductUpdateRequest(ProductBase):
    """Payload for admin product update."""


class ProductResponse(ProductBase):
    """Product response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PublicProductListResponse(BaseModel):
    """Paginated public products list."""

    items: list[ProductResponse]
    page: int
    size: int
    total: int
    total_pages: int
