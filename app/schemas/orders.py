"""Order request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    """Order item response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str = ""
    quantity: int
    price: float


class OrderResponse(BaseModel):
    """Order response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: str
    total: float
    created_at: datetime
    updated_at: datetime | None = None
    items: list[OrderItemResponse]


class AdminOrderStatusUpdateRequest(BaseModel):
    """Admin payload for order status transition."""

    status: str
