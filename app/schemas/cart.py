"""Cart request/response schemas."""

from pydantic import BaseModel, ConfigDict, Field


class CartAddItemRequest(BaseModel):
    """Payload for adding item to cart."""

    product_id: int
    quantity: int = Field(default=1, ge=1)


class CartUpdateItemRequest(BaseModel):
    """Payload for updating cart item quantity."""

    quantity: int = Field(ge=0)


class CartItemResponse(BaseModel):
    """Cart item response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float


class CartResponse(BaseModel):
    """Cart response schema with totals."""

    items: list[CartItemResponse]
    total: float
