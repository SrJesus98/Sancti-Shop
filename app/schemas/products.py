"""Product request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    """Shared product fields."""

    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(ge=0)
    stock: int = Field(ge=0)
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_min_length(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return round(v, 2)


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
